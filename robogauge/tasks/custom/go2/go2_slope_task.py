# -*- coding: utf-8 -*-
'''
@File    : go2_slope_task.py
@Time    : 2025/12/21 17:06:27
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Go2 Slope Task Configuration
'''
from robogauge.tasks.robots import Go2Config, Go2MoEConfig
from robogauge.tasks.gauge import SlopeGaugeConfig
from robogauge.tasks.simulator.mujoco_config import MujocoConfig

class Go2SlopeGaugeConfig(SlopeGaugeConfig):
    class metrics(SlopeGaugeConfig.metrics):
        class dof_limits(SlopeGaugeConfig.metrics.dof_limits):
            enabled = True
            soft_dof_limit_ratio = 0.7
            dof_names = ['hip', 'thigh']  # List of DOF names to monitor, None for all
