# -*- coding: utf-8 -*-
'''
@File    : helpers.py
@Time    : 2025/11/27 15:26:37
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Helpers for robogauge, include:
- Argument parsing
- Class to dict conversion
- Path parsing
'''
import yaml
from argparse import ArgumentParser
from pathlib import Path
from robogauge import ROBOGAUGE_ROOT_DIR

def parse_path(path):
    if "{ROBOGAUGE_ROOT_DIR}" in str(path):
        path = str(path).replace("{ROBOGAUGE_ROOT_DIR}", ROBOGAUGE_ROOT_DIR)
    return path

def class_to_dict(obj) -> dict:
    # From https://github.com/leggedrobotics/legged_gym/blob/master/legged_gym/utils/helpers.py
    if not hasattr(obj, "__dict__"):
        return obj
    result = {}
    for key in dir(obj):
        if key.startswith("_"):
            continue
        element = []
        val = getattr(obj, key)
        if isinstance(val, list):
            for item in val:
                element.append(class_to_dict(item))
        else:
            element = class_to_dict(val)
        result[key] = element
    return result

def set_seed(seed: int):
    import os
    import torch
    import random
    import numpy as np
    assert seed >= 0, "Seed must be non-negative."

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    raise TypeError('Boolean value expected.')

def parse_args():
    parser = ArgumentParser()
    parameters = [
        # Single run parameters
        {"name": "--task-name", "type": str, "default": "base", "help": "Name of the task to run."},
        {"name": "--experiment-name", "type": str, "help": "Name of the experiment to run."},
        {"name": "--run-name", "type": str, "default": "run", "help": "Name of the run."},
        {"name": "--model-path", "type": str, "help": "Path to the model file."},
        {"name": "--headless", "action": "store_true", "default": False, "help": "Run in headless mode."},
        {"name": "--save-video", "action": "store_true", "default": False, "help": "Save video output."},
        {"name": "--seed", "type": int, "default": 42, "help": "Random seed."},
        {"name": "--write-tensorboard", "action": "store_true", "default": False, "help": "Write tensorboard logs."},
        {"name": "--plot-radar", "action": "store_true", "default": False, "help": "Plot radar charts for metrics."},
        {"name": "--base-mass", "type": float, "default": 0.0, "help": "Set the base mass of the robot."},
        {"name": "--friction", "type": float, "default": 1.0, "help": "Set the ground friction coefficient."},
        {"name": "--level", "type": int, "help": "Set the difficulty level of the environment, range 1-10 (flat is 0)."},
        {"name": "--goals", "type": str, "nargs": "+", "help": "List of goal names to evaluate."},

        # Multiprocessing parameters, with different seeds
        {"name": "--multi", "action": "store_true", "default": False, "help": "Enable multiprocessing."},
        {"name": "--num-processes", "type": int, "default": 2, "help": "Number of parallel processes."},
        {"name": "--seeds", "type": int, "nargs": "+", "default": [0, 1, 2, 3, 4], "help": "List of random seeds for multiple runs."},
        {"name": "--base-masses", "type": float, "nargs": "+", "default": [0], "help": "List of base masses for the model."},
        {"name": "--frictions", "type": float, "nargs": "+", "default": [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5], "help": "List of friction coefficients for the model."},

        # Level pipeline parameters
        {"name": "--search-max-level", "action": "store_true", "default": False, "help": "Use level pipeline to search maximum level."},

        # Stress pipeline parameters
        {"name": "--stress-benchmark", "action": "store_true", "default": False, "help": "Use stress pipeline to benchmark model robustness."},
        {"name": "--stress-terrain-names", "type": str, "nargs": "+", "default": ["flat", "slope", "wave", "stairs_up", "stairs_down"], "help": "List of terrain names for stress benchmark."},
        {"name": "--stress-num-processes", "type": int, "default": 2, "help": "Number of parallel processes for stress benchmark."},

        {"name": "--compress-logs", "action": "store_true", "default": False, "help": "Compress and delete logs after run."},
    ]
    for param in parameters:
        parser.add_argument(param['name'], **{k: v for k, v in param.items() if k != 'name'})
    args = parser.parse_args()
    flatten_task_name = args.task_name.replace('.', '_')
    args.cli_experiment_name = args.experiment_name
    if args.experiment_name is not None:
        args.experiment_name = f"{flatten_task_name}_{args.experiment_name}"
    else:
        args.experiment_name = flatten_task_name
    return args

def snake_to_pascal(s: str) -> str:
    """ 'snake_case' to 'PascalCase' conversion """
    parts = [p for p in s.split('_') if p]
    return ''.join(p[0].upper() + p[1:] if p else '' for p in parts)
