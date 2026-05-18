# -*- coding: utf-8 -*-
'''
@File    : go2_lab_config.py
@Time    : 2026/04/11 17:59:09
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Go2 Lab Robot Configuration
'''
from robogauge.tasks.robots.go2.go2_config import Go2Config, Go2TerrainConfig


class Go2LabConfig(Go2Config):
    """Go2 Lab robot configuration aligned with RobotLab observation scaling."""

    class control(Go2Config.control):
        p_gains = [25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0]  # [N*m/rad]
        class scales(Go2Config.control.scales):
            # RobotLab policy command observation uses unit scale.
            cmd = [1.0, 1.0, 1.0]


class Go2LabTerrainConfig(Go2LabConfig, Go2TerrainConfig):
    """Go2 Lab robot configuration for terrain tasks."""
