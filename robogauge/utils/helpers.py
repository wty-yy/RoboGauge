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
from argparse import ArgumentParser
from pathlib import Path
from robogauge import ROBOGAUGE_ROOT_DIR

def pares_path(path):
    if "{ROBOGAUGE_ROOT_DIR}" in str(path):
        path = str(path).replace("{ROBOGAUGE_ROOT_DIR}", ROBOGAUGE_ROOT_DIR)
    return path

def class_to_dict(obj) -> dict:
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

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    raise TypeError('Boolean value expected.')

def parse_args():
    parser = ArgumentParser()
    parameters = [
        {"name": "--task-name", "type": str, "default": "base", "help": "Name of the task to run."},
        {"name": "--experiment-name", "type": str, "default": "base", "help": "Name of the experiment to run."},
        {"name": "--headless", "action": "store_true", "default": False, "help": "Run in headless mode."},
        {"name": "--save-video", "action": "store_true", "default": False, "help": "Save video output."},
    ]
    for param in parameters:
        parser.add_argument(param['name'], **{k: v for k, v in param.items() if k != 'name'})
    return parser.parse_args()
