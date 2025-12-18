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
from robogauge.utils.logger import logger

def run_single_process(args, data):
    seed, base_mass, friction = data
    local_args = deepcopy(args)
    local_args.seed = seed
    local_args.friction = friction
    local_args.base_mass = base_mass
    run_name = f"{local_args.run_name}_{seed}_baseMass{base_mass}_friction{friction}"
    logger.create(
        experiment_name=local_args.experiment_name,
        run_name=run_name,
        console_output=False
    )
    pipeline = task_register.make_pipeline(args=local_args, create_logger=False)
    try:
        log_dir = pipeline.run()
        ret = {
            'status': 'success',
            'log_dir': log_dir,
            'model_path': pipeline.robot_cfg.control.model_path,
        }
    except Exception as e:
        logger.error(f"❌ Process with seed={seed}, base_mass={base_mass}, friction={friction} failed with error: {e}")
        ret = {
            'status': 'error',
            'data': data,
            'error_msg': str(e),
            'traceback': traceback.format_exc()
        }
    return ret

class MultiPipeline:
    def __init__(self, args):
        self.args = args
        self.seeds = args.seeds
        self.frictions = args.frictions
        self.base_masses = args.base_masses
        self.num_processes = args.num_processes
        self.model_path = None
        logger.create(args.experiment_name+'_multi', args.run_name+'_multi')

    def run(self):
        logger.info(f"🚀 Starting Multi-Process Evaluation with {self.num_processes} processes.")
        logger.info(f"🔢 Seeds: {self.seeds}, Frictions: {self.frictions}, Base masses: {self.base_masses}")

        workers_data = list(product(self.seeds, self.base_masses, self.frictions))
        ctx = multiprocessing.get_context('spawn')
        worker_func = functools.partial(run_single_process, self.args)
        result_log_dirs = []
        success_flags = []
        with ctx.Pool(processes=self.num_processes) as pool:
            iterator = pool.imap_unordered(worker_func, workers_data)
            for results in tqdm(iterator, total=len(workers_data), desc="Evaluation"):
                success_flags.append(results['status'] == 'success')
                if results['status'] == 'success':
                    result_log_dirs.append(results['log_dir'])
                    if self.model_path is None:
                        self.model_path = results['model_path']
                    else:
                        assert self.model_path == results['model_path'], "Model paths do not match across runs."
                else:
                    data = results['data']
                    logger.error(f"❌ Process with seed={data[0]}, base_mass={data[1]}, friction={data[2]} failed with error: {results['error_msg']}")

        logger.info("✅ Multi-Process Evaluation Completed.")
        self.aggregate_results(result_log_dirs, success_flags, workers_data)
    
    def aggregate_results(self, log_dirs, success_flags, workers_data):
        """ Process results.yaml from each log_dir """
        logger.info("📊 Aggregating Results from all runs...")

        summary = {'model_path': self.model_path, 'success': {}}
        finish_msg = (
            f"""\n{'='*20} Run Finish Summary {'='*20}\n"""
            f"""{'Seed':^10}{'Base Mass':^15}{'Friction':^15}{'Status':^10}\n"""
        )
        for success, data in zip(success_flags, workers_data):
            seed, base_mass, friction = data
            status_str = "✅" if success else "❌"
            finish_msg += f"{seed:^10}{base_mass:^15}{friction:^15}{status_str:^10}\n"
            summary['success'][f"Seed_{seed}_BaseMass_{base_mass}_Friction_{friction}"] = True if success else False
        finish_msg += f"""{'='*88}"""
        logger.info(finish_msg)

        all_results = []
        all_yaml_paths = []
        for path in log_dirs:
            yaml_path = Path(path) / "results.yaml"
            if not yaml_path.exists():
                logger.warning(f"Results file not found: {yaml_path}, skipping.")
                continue
            with open(yaml_path, 'r') as file:
                data = yaml.safe_load(file)
                if data:
                    all_results.append(data)
                    all_yaml_paths.append(yaml_path)
        if not all_results:
            logger.error("No results to aggregate.")
            return
        yaml_paths_str = '\n'.join([str(p) for p in all_yaml_paths])
        logger.info(
            f"""\n{'='*20} Results Files {'='*20}\n"""
            f"""{yaml_paths_str}\n"""
            f"""{'='*56}"""
        )
        
        value_collections = defaultdict(lambda: defaultdict(list))
        for result in all_results:
            for goal, metrics in result.items():
                if goal != 'summary':
                    continue
                for metric, means in metrics.items():
                    for mean_name, mean_value in means.items():
                        value_collections[metric][mean_name].append(float(mean_value.split(' ')[0]))
        
        for metric, means in value_collections.items():
            summary[metric] = {}
            for mean_name, values in means.items():
                summary[metric][mean_name] = f"{float(np.mean(values)):.4f} ± {float(np.std(values)):.4f}"
        
        save_path = logger.log_dir / "aggregated_results.yaml"
        with open(save_path, 'w') as file:
            yaml.dump(summary, file, allow_unicode=True, sort_keys=False)
        logger.info("✅ Aggregated execution finished.")
        logger.info(f"📁 Aggregated results saved to: {save_path}")

        logger.info(
            f"""\n{'='*20} Multi-Run Summary {'='*20}\n"""
            f"""{yaml.dump(summary, allow_unicode=True)}"""
            f"""{'='*60}"""
        )
