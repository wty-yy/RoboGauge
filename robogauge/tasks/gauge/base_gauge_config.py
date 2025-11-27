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
        terrain_spawn_xy = [0, 0]  # x y [m]

    class metrics:
        dof_limits = True
    
    class commands:
        stance = True
        max_lin_vel = True
        diagonal_lin_vel = True
    
