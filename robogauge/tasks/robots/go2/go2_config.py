# -*- coding: utf-8 -*-
'''
@File    : go2_config.py
@Time    : 2025/11/27 16:03:27
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Go2 Robot Configuration
'''
from typing_extensions import Literal
from robogauge.tasks.robots import RobotConfig

class Go2Config(RobotConfig):
    robot_class = 'Go2'

    class assets:
        robot_xml = "{ROBOGAUGE_ROOT_DIR}/resources/robots/go2/go2.xml"
        robot_spawn_height = 0.1  # z [m]

    class control(RobotConfig.control):
        device = 'cpu'
        torch_script_model_path = "{ROBOGAUGE_ROOT_DIR}/resources/models/go2/go2_cts_83501.pt"
        # torch_script_model_path = "{ROBOGAUGE_ROOT_DIR}/resources/models/go2/go2_cts_cmd-1,1_38k.pt"
        control_dt = 0.02  # 50 Hz
        control_type = 'P'  # Position control

        # Mujoco joint PD gains
        p_gains = [20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0]  # [N*m/rad]
        d_gains = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]  # [N*m*s/rad]
    
        num_observations = 45
        num_actions = 12

        default_dof_pos = [0.1,  0.8,  -1.5,  -0.1, 0.8, -1.5, 
                           0.1,  1.0,  -1.5,  -0.1, 1.0, -1.5] 
        
        mj2model_dof_indices = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

        class scales(RobotConfig.control.scales):
            lin_vel = 2.0
            ang_vel = 0.25
            dof_pos = 1.0
            dof_vel = 0.05
            action = 0.25  # target pos = action_scale * action * default_pos
            cmd = [2.0, 2.0, 0.25]

    class commands(RobotConfig.commands):
        lin_vel_x = [-1.5, 1.5]  # min max [m/s]
        lin_vel_y = [-1, 1]  # min max [m/s]
        lin_vel_z = None  # min max [m/s]
        ang_vel_roll = None  # min max [rad/s]
        ang_vel_pitch = None  # min max [rad/s]
        ang_vel_yaw = [-2, 2]  # min max [rad/s]

