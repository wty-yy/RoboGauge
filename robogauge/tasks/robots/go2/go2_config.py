# -*- coding: utf-8 -*-
'''
@File    : go2_config.py
@Time    : 2025/11/27 16:03:27
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Go2 Robot Configuration
'''
from robogauge.tasks.robots import RobotConfig

class Go2Config(RobotConfig):
    class assets:
        robot_xml = "{ROBOGAUGE_ROOT_DIR}/resources/robots/go2/go2.xml"
        robot_spawn_height = 0.1  # z [m]

    class control:
        control_dt = 0.02  # 50 Hz
        action_scale = 0.25  # scale for normalized actions

