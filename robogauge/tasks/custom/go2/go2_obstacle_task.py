# -*- coding: utf-8 -*-
'''
@File    : go2_obstacle_task.py
@Time    : 2025/12/27 14:32:22
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Go2 Obstacle Task Configuration
'''
from robogauge.tasks.gauge import ObstacleGaugeConfig
from robogauge.tasks.simulator.mujoco_config import MujocoConfig

class Go2ObstacleGaugeConfig(ObstacleGaugeConfig):
    class metrics(ObstacleGaugeConfig.metrics):
        class dof_limits(ObstacleGaugeConfig.metrics.dof_limits):
            enabled = True
            soft_dof_limit_ratio = 0.7
            dof_names = ['hip', 'thigh']  # List of DOF names to monitor, None for all
