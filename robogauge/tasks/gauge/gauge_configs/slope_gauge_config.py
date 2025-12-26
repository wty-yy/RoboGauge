# -*- coding: utf-8 -*-
'''
@File    : slope_gauge_config.py
@Time    : 2025/12/21 17:02:23
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Slope Gauge Configuration
'''
from robogauge.tasks.gauge.base_gauge_config import BaseGaugeConfig

class SlopeGaugeConfig(BaseGaugeConfig):
    gauge_class = 'BaseGauge'

    class assets(BaseGaugeConfig.assets):
        terrain_name = "slope"
        terrain_level = 4  # 1-10
        terrain_xmls = [
            '{ROBOGAUGE_ROOT_DIR}/resources/terrains/slope/slope_4.xml',
            '{ROBOGAUGE_ROOT_DIR}/resources/terrains/wall/10x10_wall.xml',
        ]
        terrain_spawn_pos = [0.5, 0, 0]  # x y z [m], robot freejoint spawn position on the terrain
    
    class goals(BaseGaugeConfig.goals):
        class target_pos_velocity:  # goal to reach a target position by velocity command
            enabled = True
            target_pos = [4.8, 0, 1.152 + 0.1]  # x y z [m], target position in the environment, used for target position goal
            lin_vel_x = 1.0  # +/- m/s
            lin_vel_y = 1.0  # +/- m/s
            ang_vel_yaw = 1.5  # +/- rad/s
            max_cmd_duration = 20.0  # [s] maximum duration to reach the target position
            reach_threshold = 0.1
        