# -*- coding: utf-8 -*-
'''
@File    : wave_gauge_config.py
@Time    : 2025/12/22 11:02:09
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Wave Gauge Configuration
'''
from robogauge.tasks.gauge.base_gauge_config import BaseGaugeConfig

class WaveGaugeConfig(BaseGaugeConfig):
    gauge_class = 'BaseGauge'

    class assets(BaseGaugeConfig.assets):
        terrain_name = "wave"
        terrain_level = 10  # 1-10
        terrain_xmls = [
            '{ROBOGAUGE_ROOT_DIR}/resources/terrains/wave/wave_10.xml',
            '{ROBOGAUGE_ROOT_DIR}/resources/terrains/wall/10x10_wall.xml',
        ]
        terrain_spawn_pos = [1.5, 1.25, 0.0]  # x y z [m], robot freejoint spawn position on the terrain
    
    class goals:
        class target_pos_velocity:  # goal to reach a target position by velocity command
            enabled = True
            target_pos = [6.5, -2.65, 0.8]  # x y z [m], target position in the environment, used for target position goal
            lin_vel_x = 1.0  # +/- m/s
            lin_vel_y = 1.0  # +/- m/s
            ang_vel_yaw = 1.5  # +/- rad/s
            max_cmd_duration = 20.0  # [s] maximum duration to reach the target position
            reach_threshold = 0.1
