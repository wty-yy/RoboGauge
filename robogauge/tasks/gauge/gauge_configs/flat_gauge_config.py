# -*- coding: utf-8 -*-
'''
@File    : flat_gauge_config.py
@Time    : 2025/11/27 16:03:02
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Flat Gauge Configuration
'''
from robogauge.tasks.gauge.base_gauge_config import BaseGaugeConfig

class FlatGaugeConfig(BaseGaugeConfig):
    gauge_class = 'BaseGauge'

    class assets:
        terrain_xml = '{ROBOGAUGE_ROOT_DIR}/resources/terrains/flat.xml'
        terrain_spawn_pos = [0, 0, 0]  # x y z [m], robot freejoint spawn position on the terrain
    
    class goals:
        class max_velocity:  # goal with maximum velocity
            enabled = True
            move_duration = 5.0  # [s] duration for each velocity command
            end_stance = True  # whether to end with zero velocity command
            standce_duration = 2.0  # [s] duration for the ending stance command
        
        class diagonal_velocity:  # goal with diagonal velocity changes
            enabled = True
            cmd_duration = 6.0  # [s] duration for a pair of diagonal velocity commands

    class metrics(BaseGaugeConfig.metrics):
        metric_dt = 0.1  # [s] frequency to compute metrics
        class dof_limits:
            enabled = True
            soft_dof_limit_ratio = 0.9
            dof_names = None  # List of DOF names to monitor, None for all
        
        class visualization:
            enabled = True
            dof_force = True
            dof_pos = True

        class lin_vel_err:
            enabled = True
        
        class ang_vel_err:
            enabled = True
