# -*- coding: utf-8 -*-
'''
@File    : base_robot_config.py
@Time    : 2025/11/27 15:53:47
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Base Robot Configuration
'''
from robogauge.utils.config import Config

class RobotConfig(Config):
    robot_class = 'BaseRobot'

    class assets:
        robot_xml = "{ROBOGAUGE_ROOT_DIR}/resources/robots/go2/go2.xml"
        robot_spawn_height = 0.1  # z [m]

    class control:
        torch_script_model_path = "{ROBOGAUGE_ROOT_DIR}/resources/models/go2/go2_cts_61500.pt"
        control_dt = 0.02  # 50 Hz
        action_scale = 0.25  # target pos = action_scale * action * default_pos
        stiffness = 20.0  # [N*m/rad]
        damping = 0.5  # [N*m*s/rad]
    
    class mdp:
        num_observations = 46
        num_actions = 12
    
    class commands:
        lin_vel_x = [-1, 1]  # min max [m/s]
        lin_vel_y = [-1, 1]  # min max [m/s]
        ang_vel_yaw = [-1, 1]  # min max [rad/s]
    
