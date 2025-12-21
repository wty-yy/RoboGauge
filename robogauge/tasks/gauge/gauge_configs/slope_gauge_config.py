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
        terrain_name = "slope_5"  # {type}_{level}
        terrain_xml = '{ROBOGAUGE_ROOT_DIR}/resources/terrains/slope/slope_10.xml'
        terrain_spawn_pos = [0, 0, 0]  # x y z [m], robot freejoint spawn position on the terrain
    
    class goals:
        class target_pos_velocity:  # goal to reach a target position by velocity command
            enabled = True
            target_pos = [4, 0, 2.0]  # x y z [m], target position in the environment, used for target position goal
            lin_vel_x = 1.0  # +/- m/s
            lin_vel_y = 1.0  # +/- m/s
            ang_vel_yaw = 1.5  # +/- rad/s
            max_cmd_duration = 20.0  # [s] maximum duration to reach the target position
            reach_threshold = 0.1
