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
import sys

# Select the rendering backend before importing MuJoCo.  EGL provides an
# offscreen context on headless Linux, while GLFW is used by the GUI viewer.
# Keep an explicit MUJOCO_GL value so callers can override either default.
default_mujoco_gl = (
    'egl'
    if sys.platform.startswith('linux') and '--headless' in sys.argv
    else 'glfw'
)
os.environ.setdefault('MUJOCO_GL', default_mujoco_gl)

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

from robogauge.tasks import *
from robogauge.tasks.pipeline import *

from robogauge.utils.task_register import task_register
from robogauge.utils.helpers import parse_args
from robogauge.utils.logger import logger


if __name__ == '__main__':
    args = parse_args()
    if args.stress_benchmark:
        stress_pipeline = StressPipeline(args)
        stress_pipeline.run()
    elif args.multi:
        multi_pipeline = MultiPipeline(args)
        multi_pipeline.run()
    elif args.search_max_level:
        level_pipeline = LevelPipeline(args)
        level_pipeline.run()
    else:
        pipeline: BasePipeline = task_register.make_pipeline(args=args)
        pipeline.run()
