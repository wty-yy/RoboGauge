# -*- coding: utf-8 -*-
'''
@File    : multi_pipeline.py
@Time    : 2025/12/06 15:32:44
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Multiprocessing Pipeline for Robogauge
'''
import yaml
import traceback
import functools
import numpy as np
from tqdm import tqdm
import multiprocessing
from pathlib import Path
from copy import deepcopy
from itertools import product
from collections import defaultdict

from robogauge.tasks.pipeline.base_pipeline import BasePipeline

from robogauge.utils.task_register import task_register
from robogauge.utils.logger import Logger
from robogauge.utils.process_utils import NoDaemonPool
from robogauge.utils.progress_monitor import report_progress, ProgressTypes, ProgressData
from robogauge.utils.file_utils import compress_directory
from robogauge.tasks.gauge.gauge_configs.terrain_levels_config import SEARCH_LEVELS_TERRAINS

multi_logger = Logger()  # MultiPipeline logger

def run_single_process(args, data):
    from robogauge.utils.logger import logger
    seed, base_mass, friction = data
    local_args = deepcopy(args)
    local_args.seed = seed
    local_args.friction = friction
    local_args.base_mass = base_mass
    run_name = f"{local_args.run_name}_{seed}_baseMass{base_mass}_friction{friction}"
    logger.create(
        experiment_name=local_args.experiment_name,
        run_name=run_name,
        console_output=False,
        parent_log_dir=args.parent_log_dir
    )
    pipeline = task_register.make_pipeline(args=local_args, create_logger=False)
    results, warning, error = pipeline.run()
    if error is None:
        ret = {
            'status': 'success',
            'results': results,
            'data': data,
            'model_path': pipeline.robot_cfg.control.model_path,
        }
        if warning is not None:
            logger.warning(f"⚠️ Process with seed={seed}, base_mass={base_mass}, friction={friction} completed with warning: {warning}")
    else:
        logger.error(f"❌ Process with seed={seed}, base_mass={base_mass}, friction={friction} failed with error: {error}")
        ret = {
            'status': 'error',
            'results': results,
            'model_path': pipeline.robot_cfg.control.model_path,
            'data': data,
            'error_msg': str(error),
            'traceback': traceback.format_exc()
        }
    return ret

class MultiPipeline:
    def __init__(self, args, console_output=True, progress_data: ProgressData = None):
        self.args = args
        self.seeds = args.seeds
        self.frictions = args.frictions
        self.base_masses = args.base_masses
        self.console_output = console_output
        self.progress_data = progress_data
        self.num_processes = args.num_processes
        self.static_info = {}
        parent_log_dir = getattr(args, 'parent_log_dir', None)
        multi_logger.create(args.experiment_name+'_multi', args.run_name+'_multi', console_output=console_output, parent_log_dir=parent_log_dir)
        self.args.parent_log_dir = str(multi_logger.log_dir / "subtasks")
        self.compress_logs = args.compress_logs
    
    def add_static_info(self, key: str, value):
        if key not in self.static_info:
            self.static_info[key] = value
        else:
            assert self.static_info[key] == value, f"Static info key '{key}' has conflicting values: {self.static_info[key]} vs {value}"

    def run(self):
        multi_logger.info(f"🚀 Starting Multi-Process Evaluation with {self.num_processes} processes.")
        multi_logger.info(f"🔢 Seeds: {self.seeds}, Frictions: {self.frictions}, Base masses: {self.base_masses}")

        workers_data = list(product(self.seeds, self.base_masses, self.frictions))
        report_progress(self.progress_data, ProgressTypes.INIT, total=len(workers_data), desc="🚀 MultiPipeline")

        ctx = multiprocessing.get_context('spawn')
        worker_func = functools.partial(run_single_process, self.args)
        results_list = []

        def update_results(results):
            results_list.append(results)
            self.add_static_info('model_path', results['model_path'])
            self.add_static_info('terrain_name', results['results']['terrain_name'])
            self.add_static_info('terrain_level', results['results']['terrain_level'])
            report_progress(self.progress_data, ProgressTypes.UPDATE, value=1)
            if results['status'] != 'success':
                data = results['data']
                multi_logger.error(f"❌ Process with seed={data[0]}, base_mass={data[1]}, friction={data[2]} failed with error: {results['error_msg']}")

        if self.num_processes == 1:
            multi_logger.info("🚀 Running in Serial Mode")
            bar = workers_data
            if self.console_output:
                bar = tqdm(workers_data, desc="Evaluation")
            for data in bar:
                results = worker_func(data)
                update_results(results)
        else:
            with NoDaemonPool(processes=self.num_processes, context=ctx) as pool:
                iterator = pool.imap_unordered(worker_func, workers_data)
                bar = iterator
                if self.console_output:
                    bar = tqdm(iterator, total=len(workers_data), desc="Evaluation")
                for results in bar:
                    update_results(results)

        multi_logger.info("✅ Multi-Process Evaluation Completed.")
        aggregated_results = self.aggregate_results(results_list)
        return aggregated_results
    
    def aggregate_results(self, all_results):
        """ Process results from all processes and aggregate them. """
        multi_logger.info("📊 Aggregating Results from all runs...")

        summary = {'success': {}, **self.static_info, 'summary': {}, 'terrain_weighted_summary': {}}
        finish_msg = (
            f"""\n{'='*20} Run Finish Summary {'='*20}\n"""
            f"""{'Seed':^10}{'Base Mass':^15}{'Friction':^15}{'Status':^10}\n"""
        )
        all_results = sorted(all_results, key=lambda x: x['data'])
        for result in all_results:
            seed, base_mass, friction = result['data']
            success = result['status'] == 'success'
            status_str = "✅" if success else "❌"
            finish_msg += f"{seed:^10}{base_mass:^15}{friction:^15}{status_str:^10}\n"
            summary['success'][f"Seed_{seed}_BaseMass_{base_mass}_Friction_{friction}"] = True if success else False
        finish_msg += f"""{'='*88}"""
        multi_logger.info(finish_msg)

        if not all_results:
            multi_logger.error("No results to aggregate.")
            return
        
        value_collections = defaultdict(lambda: defaultdict(list))
        for result in all_results:
            for goal, metrics in result['results'].items():
                if goal != 'summary':
                    continue
                for metric, means in metrics.items():
                    for mean_name, mean_value in means.items():
                        value_collections[metric][mean_name].append(float(mean_value.split(' ')[0]))
        
        for metric, means in value_collections.items():
            summary['summary'][metric] = {}
            for mean_name, values in means.items():
                v = float(np.mean(values))
                summary['summary'][metric][mean_name] = f"{v:.4f} ± {float(np.std(values)):.4f}"

            if 'quality_score' in metric: continue
            summary['terrain_weighted_summary'][metric] = {}
            for mean_name, values in means.items():
                twv = float(np.mean(values))
                if summary['terrain_name'] in SEARCH_LEVELS_TERRAINS:
                    twv = 0.09 * (summary['terrain_level'] - 1) + 0.19 * v
                summary['terrain_weighted_summary'][metric][mean_name] = f"{twv:.4f} ± {float(np.std(values)):.4f}"
        
        save_path = multi_logger.log_dir / "aggregated_results.yaml"
        with open(save_path, 'w') as file:
            yaml.dump(summary, file, allow_unicode=True, sort_keys=False)
        multi_logger.info("✅ Aggregated execution finished.")
        multi_logger.info(f"📁 Aggregated results saved to: {save_path}")

        if self.compress_logs:
            compress_directory(multi_logger.log_dir / "subtasks", delete_original=True, logger=multi_logger)
        # multi_logger.info(
        #     f"""\n{'='*20} Multi-Run Summary {'='*20}\n"""
        #     f"""{yaml.dump(summary, allow_unicode=True)}"""
        #     f"""{'='*60}"""
        # )
        return summary
