# -*- coding: utf-8 -*-
'''
@File    : base_gauge_config.py
@Time    : 2025/11/27 15:55:11
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Base Gauge Configuration
'''
from robogauge.utils.config import Config

class BaseGaugeConfig(Config):
    gauge_class = 'BaseGauge'
    write_tensorboard = False  # Whether to write tensorboard logs

    class assets:
        terrain_name = "flat_0"  # {type}_{level}
        terrain_xml = '{ROBOGAUGE_ROOT_DIR}/resources/terrains/flat.xml'
        terrain_spawn_pos = [0, 0, 0]  # x y z [m], robot freejoint spawn position on the terrain
    
    class goals:
        class max_velocity:  # goal with maximum velocity
            enabled = False
            cmd_duration = 5.0  # [s] duration for each velocity command

        class diagonal_velocity:  # goal with diagonal velocity changes
            enabled = False
            cmd_duration = 6.0  # [s] duration for a pair of diagonal velocity commands

        class target_pos_velocity:  # goal to reach a target position by velocity command
            enabled = False
            target_pos = [5, 0, 0]  # x y z [m], target position in the environment, used for target position goal
            lin_vel_x = 1.0  # +/- m/s
            lin_vel_y = 1.0  # +/- m/s
            ang_vel_yaw = 1.5  # +/- rad/s
            max_cmd_duration = 10.0  # [s] maximum duration to reach the target position
            reach_threshold = 0.1

    class metrics:
        metric_dt = 0.1  # [s] frequency to compute metrics
        class dof_limits:
            enabled = True
            soft_dof_limit_ratio = 0.9
            dof_names = None  # List of DOF names to monitor, None for all
        
        class visualization:
            enabled = True
            dof_torque = True
            dof_pos = True
        
        class lin_vel_err:
            enabled = True
        
        class ang_vel_err:
            enabled = True
        
        class dof_power:
            enabled = True
            scaling_factor = 100.0  # [W] scaling factor for power metric
        
        class orientation_stability:
            enabled = True
        
        class torque_smoothness:
            enabled = True
            scaling_factor = 30.0  # [Nm] scaling factor for torque smoothness metric
