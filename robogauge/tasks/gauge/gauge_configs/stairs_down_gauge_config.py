# -*- coding: utf-8 -*-
'''
@File    : stairs_down_gauge_config.py
@Time    : 2025/12/25 14:12:59
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Stairs Down Gauge Configuration
'''
from robogauge.tasks.gauge.base_gauge_config import BaseGaugeConfig

class StairsDownGaugeConfig(BaseGaugeConfig):
    gauge_class = 'BaseGauge'

    class assets(BaseGaugeConfig.assets):
        terrain_name = "stairs_down"
        terrain_level = 10  # 1-10
        terrain_xmls = [
            '{ROBOGAUGE_ROOT_DIR}/resources/terrains/stairs_down/stairs_down_10.xml',
            '{ROBOGAUGE_ROOT_DIR}/resources/terrains/wall/10x10_wall.xml',
        ]
        # NOTE: Adjusted y=3.0 to avoid rolling down just pass the target
        terrain_spawn_pos = [1.1, 3.0, 7]  # x y z [m], robot freejoint spawn position on the terrain
    
    class goals(BaseGaugeConfig.goals):
        class target_pos_velocity:  # goal to reach a target position by velocity command
            enabled = True
            target_pos = [8.3, 0.0, 1.90]  # x y z [m], target position in the environment, used for target position goal
            lin_vel_x = 0.8  # +/- m/s
            lin_vel_y = 1.0  # +/- m/s
            ang_vel_yaw = 1.5  # +/- rad/s
            max_cmd_duration = 30.0  # [s] maximum duration to reach the target position
            reach_threshold = 0.3
