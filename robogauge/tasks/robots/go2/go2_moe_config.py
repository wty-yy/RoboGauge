# -*- coding: utf-8 -*-
'''
@File    : go2_moe_config.py
@Time    : 2025/12/05 17:32:27
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : None
'''
from robogauge.tasks.robots.go2.go2_config import Go2Config

class Go2MoEConfig(Go2Config):
    robot_class = 'Go2MoE'

    class control(Go2Config.control):
        model_path = "{ROBOGAUGE_ROOT_DIR}/resources/models/go2/go2_moe_cts_137k_0.6739.pt"
        save_additional_output = False

class Go2MoETerrainConfig(Go2MoEConfig):
    """ Go2 MoE Robot Configuration for Terrain Tasks (wave, stairs up/down, slope, obstacles) """
    class commands(Go2MoEConfig.commands):
        lin_vel_x = [-1.0, 1.0]  # min max [m/s]
        lin_vel_y = [-1.0, 1.0]  # min max [m/s]
        ang_vel_yaw = [-1.5, 1.5]  # min max [rad/s]
