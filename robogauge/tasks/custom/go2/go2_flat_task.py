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

        class target_pos_velocity(FlatGaugeConfig.goals.target_pos_velocity):  # goal to reach a target position by velocity command, config target at assets.target_pos
            enabled = True
            target_pos = [2, 2, 0]  # x y z [m], target position in the environment, used for target position goal
            lin_vel_x = 1.0  # +/- m/s
            lin_vel_y = 1.0  # +/- m/s
            ang_vel_yaw = 1.5  # +/- rad/s
            max_cmd_duration = 10.0  # [s] maximum duration to reach the target position
            reach_threshold = 0.1  # [m] distance threshold to consider the target reached
