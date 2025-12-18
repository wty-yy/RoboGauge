# -*- coding: utf-8 -*-
'''
@File    : go2_flat_task.py
@Time    : 2025/12/18 20:19:25
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Go2 Flat Task Configuration
'''
from robogauge.tasks.robots import Go2Config, Go2MoEConfig
from robogauge.tasks.gauge import FlatGaugeConfig
from robogauge.tasks.simulator.mujoco_config import MujocoConfig

class Go2FlatGaugeConfig(FlatGaugeConfig):
    class metrics(FlatGaugeConfig.metrics):
        class dof_limits(FlatGaugeConfig.metrics.dof_limits):
            enabled = True
            soft_dof_limit_ratio = 0.7
            dof_names = ['hip', 'thigh']  # List of DOF names to monitor, None for all

    class goals(FlatGaugeConfig.goals):
        class max_velocity(FlatGaugeConfig.goals.max_velocity):
            enabled = True
            move_duration = 5.0
            end_stance = True
            stance_duration = 2.0
        
        class diagonal_velocity(FlatGaugeConfig.goals.diagonal_velocity):
            enabled = True
            cmd_duration = 6.0

class Go2FlatConfig(Go2Config):
    class commands(Go2Config.commands):
        lin_vel_x = [-1.8, 1.8]  # min max [m/s]
        lin_vel_y = [-1.8, 1.8]  # min max [m/s]
        ang_vel_yaw = [-1.8, 1.8]  # min max [rad/s]

class Go2MoEFlatConfig(Go2MoEConfig):
    class commands(Go2Config.commands):
        lin_vel_x = [-1.8, 1.8]  # min max [m/s]
        lin_vel_y = [-1.8, 1.8]  # min max [m/s]
        ang_vel_yaw = [-1.8, 1.8]  # min max [rad/s]

    class control(Go2Config.control):
        # model_path = "{ROBOGAUGE_ROOT_DIR}/resources/models/go2/go2_moe_cts_124k.pt"
        model_path = "/home/xfy/Coding/kaiwu2025/rob_finals/sim2real/models/v6-2_106503/kaiwu_script_v6-2_106503.pt"

class Go2MoEFlatMujocoConfig(MujocoConfig):
    class domain_rand(MujocoConfig.domain_rand):
        base_mass = 0.0
        friction = 1.0
