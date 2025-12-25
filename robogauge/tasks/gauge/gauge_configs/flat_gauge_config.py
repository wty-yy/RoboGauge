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

    class assets(BaseGaugeConfig.assets):
        terrain_name = "flat"
        terrain_level = 0
        terrain_xmls = ['{ROBOGAUGE_ROOT_DIR}/resources/terrains/flat.xml']
        terrain_spawn_pos = [0, 0, 0]  # x y z [m], robot freejoint spawn position on the terrain
