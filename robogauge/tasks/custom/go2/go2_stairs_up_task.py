# -*- coding: utf-8 -*-
'''
@File    : go2_wave_task.py
@Time    : 2025/12/22 11:02:23
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Go2 Wave Task Configuration
'''
from robogauge.tasks.gauge import StairsUpGaugeConfig
from robogauge.tasks.simulator.mujoco_config import MujocoConfig

class Go2StairsUpGaugeConfig(StairsUpGaugeConfig):
    class metrics(StairsUpGaugeConfig.metrics):
        class dof_limits(StairsUpGaugeConfig.metrics.dof_limits):
            enabled = True
            soft_dof_limit_ratio = 0.7
            dof_names = ['hip', 'thigh']  # List of DOF names to monitor, None for all
