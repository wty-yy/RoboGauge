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
    run_name = f"{local_args.run_name}_{seed}_baseMass{base_mass}_friction{friction}"
    logger.create(
        experiment_name=local_args.experiment_name,
        run_name=run_name,
        console_output=False
    )
    pipeline = task_register.make_pipeline(args=local_args, create_logger=False)
    log_dir = pipeline.run()
    return log_dir

class MultiPipeline:
    def __init__(self, args):
        self.args = args
        self.seeds = args.seeds
        self.frictions = args.frictions
        self.base_masses = args.base_masses
        self.num_processes = args.num_processes
        logger.create(args.experiment_name+'_multi', args.run_name+'_multi')

    def run(self):
        logger.info(f"🚀 Starting Multi-Process Evaluation with {self.num_processes} processes.")
        logger.info(f"🔢 Seeds: {self.seeds}, Frictions: {self.frictions}, Base masses: {self.base_masses}")

        process_args = list(product(self.seeds, self.base_masses, self.frictions))
        ctx = multiprocessing.get_context('spawn')
        worker_func = functools.partial(run_single_process, self.args)
        result_log_dirs = []
        with ctx.Pool(processes=self.num_processes) as pool:
            iterator = pool.imap_unordered(worker_func, process_args)
            for log_dir in tqdm(iterator, total=len(process_args), desc="Evaluation"):
                result_log_dirs.append(log_dir)

        logger.info("✅ Multi-Process Evaluation Completed.")
        self.aggregate_results(result_log_dirs)
    
    def aggregate_results(self, log_dirs):
        """ Process results.yaml from each log_dir """
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
        
        summary = {}
        for metric, means in value_collections.items():
            summary[metric] = {}
            for mean_name, values in means.items():
                summary[metric][mean_name] = f"{float(np.mean(values)):.4f} ± {float(np.std(values)):.4f}"
        
        save_path = logger.log_dir / "aggregated_results.yaml"
        with open(save_path, 'w') as file:
            yaml.dump(summary, file, allow_unicode=True)
        logger.info("✅ Aggregated execution finished.")
        logger.info(f"📁 Aggregated results saved to: {save_path}")

        logger.info(
            f"""\n{'='*20} Multi-Run Summary {'='*20}\n"""
            f"""{yaml.dump(summary, allow_unicode=True)}"""
            f"""{'='*60}"""
        )
