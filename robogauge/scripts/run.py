# -*- coding: utf-8 -*-
'''
@File    : run.py
@Time    : 2025/11/27 15:54:47
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Run Robogauge Pipeline
'''
import os
os.environ['MUJOCO_GL'] = 'glfw'  # avoid mujoco.Renderer EGL context error

from robogauge.tasks import *
from robogauge.utils.task_register import task_register
from robogauge.utils.helpers import parse_args
from robogauge.utils.logger import logger

if __name__ == '__main__':
    args = parse_args()
    logger.create(args.experiment_name, args.run_name)
    logger.info(f"Starting experiment: {args.experiment_name}")
    pipeline: BasePipeline = task_register.make_pipeline(args=args)
    pipeline.run()
