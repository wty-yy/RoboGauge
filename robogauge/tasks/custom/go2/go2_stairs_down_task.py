# -*- coding: utf-8 -*-
'''
@File    : go2_stairs_down_task.py
@Time    : 2025/12/25 16:36:18
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Go2 Stairs Down Task Configuration
'''
from robogauge.tasks.robots import Go2Config, Go2MoEConfig
from robogauge.tasks.gauge import StairsDownGaugeConfig
from robogauge.tasks.simulator.mujoco_config import MujocoConfig

class Go2StairsDownGaugeConfig(StairsDownGaugeConfig):
    class metrics(StairsDownGaugeConfig.metrics):
        class dof_limits(StairsDownGaugeConfig.metrics.dof_limits):
            enabled = True
            soft_dof_limit_ratio = 0.7
            dof_names = ['hip', 'thigh']  # List of DOF names to monitor, None for all
