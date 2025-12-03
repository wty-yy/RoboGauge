# -*- coding: utf-8 -*-
'''
@File    : base_gauge_config.py
@Time    : 2025/11/27 15:55:11
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Base Gauge Configuration
'''
from robogauge.utils.config import Config

class BaseGaugeConfig(Config):
    gauge_class = 'BaseGauge'

    class assets:
        terrain_xml = '{ROBOGAUGE_ROOT_DIR}/resources/terrains/flat.xml'
        terrain_spawn_pos = [0, 0, 0]  # x y z [m], robot freejoint spawn position on the terrain
    
    class goals:
        class max_velocity:  # goal with maximum velocity
            enabled = True
            cmd_duration = 5.0  # [s] duration for each velocity command

        class diagonal_velocity:  # goal with diagonal velocity changes
            enabled = True
            cmd_duration = 6.0  # [s] duration for a pair of diagonal velocity commands

    class metrics:
        metric_dt = 0.1  # [s] frequency to compute metrics
        class dof_limits:
            enabled = True
            soft_dof_limit_ratio = 0.9
            dof_names = None  # List of DOF names to monitor, None for all
        
        class visualization:
            enabled = True
            dof_force = True
            dof_pos = True
