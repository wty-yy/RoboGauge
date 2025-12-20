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
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

from robogauge.tasks import *
from robogauge.tasks.pipeline.multi_pipeline import MultiPipeline

from robogauge.utils.task_register import task_register
from robogauge.utils.helpers import parse_args
from robogauge.utils.logger import logger


if __name__ == '__main__':
    args = parse_args()
    if not args.multi:
        pipeline: BasePipeline = task_register.make_pipeline(args=args)
        pipeline.run()
    else:
        multi_pipeline = MultiPipeline(args)
        multi_pipeline.run()
