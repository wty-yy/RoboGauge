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
        terrain_spawn_xy = [0, 0]  # x y [m]

    class goals:
        max_velocity = True  # goal with maximum velocity

    class metrics:
        dof_limits = True
    
    class commands:
        stance = True
        max_lin_vel = True
        diagonal_lin_vel = True
    

