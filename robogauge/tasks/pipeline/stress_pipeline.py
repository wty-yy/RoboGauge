# -*- coding: utf-8 -*-
'''
@File    : stress_pipeline.py
@Time    : 2025/12/25 21:20:43
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Stress Pipeline for Robogauge
'''
# MuJoCo/XLA warnings suppression
import os
os.environ['ABSL_LOG_LEVEL'] = 'error'  
import absl.logging
absl.logging.set_verbosity(absl.logging.ERROR)

import yaml
import traceback
import functools
import numpy as np
from tqdm import tqdm
import multiprocessing
from copy import deepcopy
from itertools import product
from collections import defaultdict

from robogauge.utils.logger import Logger
from robogauge.utils.process_utils import NoDaemonPool
from robogauge.utils.progress_monitor import report_progress, ProgressTypes, start_progress_monitor_thread, ProgressData
from robogauge.tasks.pipeline import MultiPipeline, LevelPipeline
from robogauge.tasks.gauge.gauge_configs.terrain_levels_config import SEARCH_LEVELS_TERRAINS
from robogauge.utils.file_utils import compress_directory

stress_logger = Logger()  # StressPipeline logger

GOALS = {
    'level_pipeline': ['target_pos_velocity'],
    'multi_pipeline': ['max_velocity', 'diagonal_velocity']
}

def run_pipeline(args, progress_queue, data):
    args = deepcopy(args)
    task_id = data['task_id']
    search = data['search_max_level']
    task_label = f"[{data['terrain_name']}] M:{data['base_mass']} F:{data['friction']}"
    progress_data = ProgressData(
        task_id=task_id,
        msg_prefix=task_label + ' ',
        progress_queue=progress_queue
    )

    args.friction = data['friction']
    args.frictions = [data['friction']]
    args.base_mass = data['base_mass']
    args.base_masses = [data['base_mass']]
    args.task_name = f"{data['task_robot_model']}.{data['terrain_name']}"
    args.experiment_name = f"{args.experiment_name}_{data['terrain_name']}_M{data['base_mass']}_F{data['friction']}"

    if search is True:
        args.goals = GOALS['level_pipeline']
        args.spawn_type = "level_search"
        level, level_results = LevelPipeline(args, console_output=False, progress_data=progress_data).run()
        if level == 0:  # no valid level found
            report_progress(progress_data, ProgressTypes.FINISH, desc=f"❌ Failed (Lv 0)")
            results = {
                'success': False,
                'results': level_results,
                'data': data,
                'level': 0,
            }
            return results
        report_progress(progress_data, ProgressTypes.RESET, total=0, desc=f"✅ Found Lv {level} -> Running")
        progress_data.msg_prefix += f"(Lv {level}) "
    else:
        level = None  # flat terrain
        args.task_name = f"{data['task_robot_model']}.{data['terrain_name']}"
        args.experiment_name = f"{args.experiment_name}_{data['terrain_name']}"
        
    args.level = level
    args.goals = GOALS['multi_pipeline']
    args.spawn_type = "level_eval"
    results = {
        'success': True,
        'results': MultiPipeline(args, console_output=False, progress_data=progress_data).run(),
        'data': data,
        'level': level,
    }
    report_progress(progress_data, ProgressTypes.FINISH, desc=f"✅ Done (Lv {level})")
    return results

class StressPipeline:
    def __init__(self, args):
        self.args = args
        self.seeds = args.seeds
        self.task_robot_model = args.task_name.split('.')[0]
        self.num_processes = args.num_processes
        args.experiment_name = self.task_robot_model + '_stress' + ('' if args.cli_experiment_name is None else '_' + args.cli_experiment_name)
        self.static_info = {}
        stress_logger.create(args.experiment_name, args.run_name)
        self.args.parent_log_dir = str(stress_logger.log_dir / "subtasks")
        self.compress_logs = args.compress_logs
        args.compress_logs = False  # Disable child log compression
        args.num_processes = 1  # Disable child multi-process

    def add_static_info(self, key: str, value):
        if key not in self.static_info:
            self.static_info[key] = value
        else:
            assert self.static_info[key] == value, f"Static info key '{key}' has conflicting values: {self.static_info[key]} vs {value}"

    def run(self):
        stress_logger.info(f"🚀 Starting Stress Benchmark for '{self.args.experiment_name}'.")
        stress_logger.info(f"🔢 Seeds: {self.seeds}")
        terrain_names = self.args.stress_terrain_names
        stress_logger.info(f"🌄 Stress Test Terrain Names: {terrain_names}")

        ### Build worker data ###
        workers_data = []
        for terrain_name in terrain_names:
            search_max_level = True
            if terrain_name not in SEARCH_LEVELS_TERRAINS:  # Flattened terrain
                search_max_level = False
            data = {
                'task_robot_model': self.task_robot_model,
                'terrain_name': terrain_name,
                'search_max_level': search_max_level,
            }
            for friction, base_mass in product(self.args.frictions, self.args.base_masses):
                now_data = deepcopy(data)
                now_data.update({
                    'friction': friction,
                    'base_mass': base_mass,
                })
                workers_data.append(now_data)

        ### Start progress monitor ###
        progress_queue, monitor_thread = start_progress_monitor_thread(len(workers_data))
        for i, data in enumerate(workers_data):
            data['task_id'] = i

        ### Run and collect results ###
        ctx = multiprocessing.get_context('spawn')
        worker_func = functools.partial(run_pipeline, self.args, progress_queue)
        results_list = []
        try:
            with NoDaemonPool(processes=self.num_processes, context=ctx) as pool:
                iterator = pool.imap_unordered(worker_func, workers_data)
                for results in iterator:
                    results_list.append(results)
                    self.add_static_info('model_path', results['results'].pop('model_path', None))
        except Exception as e:
            stress_logger.error(f"❌ Stress benchmark encountered an error: {e}, {traceback.format_exc()}")
        finally:
            progress_queue.put(None)  # Stop the progress monitor thread
            monitor_thread.join()
        
        stress_logger.info("✅ Stress Benchmark Completed.")
        stress_results = self.aggregate_results(results_list)
        return stress_results

    def aggregate_results(self, all_results):
        stress_logger.info("📊 Aggregating Stress Benchmark Results...")
        finish_msg = (
            f"""\n{'='*20} Stress Benchmark Summary {'='*20}\n"""
            f"""{'Seeds':^20}{str(self.seeds)}\n"""
            f"""{'Terrain Name':^20}{'Base Mass':^15}{'Friction':^15}{'Max Level':^15}\n"""
        )
        all_results = sorted(all_results, key=lambda x: (x['data']['terrain_name'], x['data'].get('base_mass', 0), x['data'].get('friction', 0)))
        for result in all_results:
            terrain_name = result['data']['terrain_name']
            base_mass = result['data'].get('base_mass', self.args.base_masses)
            friction = result['data'].get('friction', self.args.frictions)
            status = f"{result['level']}" if result['success'] else "❌"
            finish_msg += f"{terrain_name:^20}{str(base_mass):^15}{str(friction):^15}{status:^15}\n"
        finish_msg += f"""{'='*66}"""
        stress_logger.info(finish_msg)

        if not all_results:
            stress_logger.error("No results to aggregate.")
            return

        summary = {**self.static_info, 'summary': {}, 'robust_score': {}, 'benchmark_score': 0.0}
        metric_collections = defaultdict(lambda: defaultdict(list))
        terrain_collections = defaultdict(lambda: defaultdict(list))
        zero_terrain_count = 0
        for result in all_results:
            terrain_name = result['data']['terrain_name']
            terrain_level = result['level']  # None, 0, 1, ..., 10
            key = f'{terrain_name}_{terrain_level}'
            key += f'_baseMass{result["data"]["base_mass"]}_friction{result["data"]["friction"]}'
            if terrain_level == 0:
                summary[key] = None
                zero_terrain_count += 1
                continue
            summary[key] = result['results']

            for metric, means in result['results']['summary'].items():
                for mean_name, value_str in means.items():
                    value = float(value_str.split(' ± ')[0])
                    metric_collections[metric][mean_name].append(value)
            for mean_name, value in result['results']['terrain_quality_score'].items():
                terrain_collections[terrain_name][mean_name].append(value)

        for metric, means in metric_collections.items():
            summary['summary'][metric] = {}
            for mean_name, values in means.items():
                values.extend([0.0] * zero_terrain_count)  # include zero terrains
                summary['summary'][metric][mean_name] = f"{float(np.mean(values)):.4f} ± {float(np.std(values)):.4f}"
        
        robust_score = defaultdict(dict)
        robust_scores = []
        for terrain_name, means in terrain_collections.items():
            for mean_name, values in means.items():
                values.extend([0.0] * zero_terrain_count)  # include zero terrains
                robust_score[terrain_name][mean_name] = float(np.mean(values))
                robust_scores.append(robust_score[terrain_name][mean_name])
        summary['robust_score'] = dict(robust_score)
        summary['benchmark_score'] = float(np.mean(robust_scores))

        save_path = stress_logger.log_dir / "stress_benchmark_results.yaml"
        with open(save_path, 'w') as file:
            yaml.dump(summary, file, allow_unicode=True, sort_keys=False)
        stress_logger.info(f"✅ Stress benchmark aggregated execution finished.")
        stress_logger.info(f"📁 Stress benchmark results saved to: {save_path}")

        if self.compress_logs:
            compress_directory(stress_logger.log_dir / "subtasks", delete_original=True, logger=stress_logger)
        return summary
