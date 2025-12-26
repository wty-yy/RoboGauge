# -*- coding: utf-8 -*-
'''
@File    : stress_pipeline.py
@Time    : 2025/12/25 21:20:43
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Stress Pipeline for Robogauge
'''
import yaml
import functools
from tqdm import tqdm
import multiprocessing
from copy import deepcopy
from itertools import product

from robogauge.utils.logger import Logger
from robogauge.tasks.pipeline import MultiPipeline, LevelPipeline
from robogauge.tasks.gauge.gauge_configs.terrain_levels_config import TerrainSearchLevelsConfig

stress_logger = Logger()  # StressPipeline logger

def run_pipeline(args, data):
    args = deepcopy(args)
    search = data['search_max_level']
    if search is True:
        args.friction = data['friction']
        args.frictions = [data['friction']]
        args.base_mass = data['base_mass']
        args.base_masses = [data['base_mass']]
        args.task_name = f"{data['task_robot_model']}.{data['terrain_name']}"
        args.experiment_name = f"{args.experiment_name}_{data['terrain_name']}_baseMass{data['base_mass']}_friction{data['friction']}"
    else:
        args.task_name = f"{data['task_robot_model']}.{data['terrain_name']}"
        args.experiment_name = f"{args.experiment_name}_{data['terrain_name']}"
        
    level = None  # flat terrain
    if search:
        level, results = LevelPipeline(args).run()

    if level == 0:  # no valid level found
        results = {
            'success': False,
            'results': results,
            'data': data,
        }
    else:
        args.level = level
        results = {
            'success': True,
            'results': MultiPipeline(args).run(),
            'data': data,
        }

    return results

class StressPipeline:
    def __init__(self, args):
        self.args = args
        self.seeds = args.seeds
        self.task_robot_model = args.task_name.split('.')[0]
        self.num_processes = args.stress_num_processes
        args.experiment_name = self.task_robot_model + '_stress' + ('' if args.cli_experiment_name is None else '_' + args.cli_experiment_name)
        self.static_info = {}
        stress_logger.create(args.experiment_name, args.run_name)

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

        ctx = multiprocessing.get_context('spawn')
        worker_func = functools.partial(run_pipeline, self.args)

        ### Build worker data ###
        workers_data = []
        terrain_search_levels_config = TerrainSearchLevelsConfig()
        for terrain_name in terrain_names:
            search_max_level = True
            terrain_level_cfg = getattr(terrain_search_levels_config, terrain_name, None)
            assert terrain_level_cfg is not None, f"Terrain '{terrain_name}' not found in TerrainSearchLevelsConfig."
            if len(terrain_level_cfg.levels) == 1:  # Flattened terrain
                search_max_level = False
            data = {
                'task_robot_model': self.task_robot_model,
                'terrain_name': terrain_name,
                'search_max_level': search_max_level,
            }
            if search_max_level:
                for friction, base_mass in product(self.args.frictions, self.args.base_masses):
                    data.update({
                        'friction': friction,
                        'base_mass': base_mass,
                    })
            workers_data.append(data)

        ### Run and collect results ###
        results_list = []
        with ctx.Pool(processes=self.num_processes) as pool:
            iterator = pool.imap_unordered(worker_func, workers_data)
            for results in tqdm(iterator, total=len(workers_data), desc="Stress Benchmark"):
                results_list.append(results)
                self.add_static_info('model_path', results['results']['model_path'])
        
        stress_logger.info("✅ Stress Benchmark Completed.")
        stress_results = self.aggregate_results(results_list)
        return stress_results

    def aggregate_results(self, all_results):
        stress_logger.info("📊 Aggregating Stress Benchmark Results...")
        summary = {}
        finish_msg = (
            f"""\n{'='*20} Stress Benchmark Summary {'='*20}\n"""
            f"""{'Terrain Name':^20}{'Base Mass':^15}{'Friction':^15}{'Status':^10}\n"""
        )
        all_results = sorted(all_results, key=lambda x: (x['data']['terrain_name'], x['data'].get('base_mass', 0), x['data'].get('friction', 0)))
        for result in all_results:
            terrain_name = result['data']['terrain_name']
            base_mass = result['data'].get('base_mass', self.args.base_masses)
            friction = result['data'].get('friction', self.args.frictions)
            status = "✅" if result['success'] else "❌"
            finish_msg += f"{terrain_name:^20}{str(base_mass):^15}{str(friction):^15}{status:^10}\n"
        finish_msg += f"""{'='*66}"""
        stress_logger.info(finish_msg)
