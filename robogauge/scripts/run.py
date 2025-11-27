# -*- coding: utf-8 -*-
'''
@File    : run.py
@Time    : 2025/11/27 15:54:47
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Run Robogauge Pipeline
'''
from robogauge.tasks import *
from robogauge.utils.task_register import task_register
from robogauge.utils.helpers import parse_args
from robogauge.utils.logger import logger

if __name__ == '__main__':
    args = parse_args()
    logger.create(args.experiment_name)
    logger.info(f"Starting experiment: {args.experiment_name}")
    pipeline: BasePipeline = task_register.make_pipeline(args.task_name, args=args)
    pipeline.run()
