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

QUALITY_WEIGHTS  = {  # Weights for geometric average, to calculate quality score
    'lin_vel_err': 2,
    'ang_vel_err': 2,
    'dof_limits': 1,
    'dof_power': 1,
    'orientation_stability': 1,
    'torque_smoothness': 1,
    'friction_margin': 1,
    'zmp_margin': 1,
}

class BaseGaugeConfig(Config):
    gauge_class = 'BaseGauge'
    write_tensorboard = False  # Whether to write tensorboard logs
    backward = False  # Whether to invert init yaw orient and backward move to target

    class assets:
        terrain_name = "flat"
        terrain_level = 0
        terrain_xmls = ['{ROBOGAUGE_ROOT_DIR}/resources/terrains/flat.xml']
        terrain_spawn_pos = [0, 0, 0]  # x y z [m], robot freejoint spawn position on the terrain
    
    class goals:
        class max_velocity:  # goal with maximum velocity
            enabled = False
            move_duration = 5.0  # [s] duration for each velocity command
            stance_duration = 2.0  # [s] duration for each stance (no movement)

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

        class joystick:  # goal controlled by joystick
            enabled = False
            goal_type = 'velocity'  # 'velocity'
            dead_zone = 0.1  # joystick dead zone

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

        class friction_margin:
            enabled = True
            force_threshold = 5.0  # [N] skip feet with too small accumulated normal force

        class zmp_margin:
            enabled = True
            contact_threshold = 1e-3  # [m] contact.dist <= threshold is treated as support contact
            force_threshold = 1e-6  # [N] abs(Fz) below threshold skips ZMP and returns 1.0
            draw_point = True  # Whether to draw the ZMP point in both viewer and offscreen render
            draw_point_size = 0.03  # [m] ZMP point sphere radius in Mujoco visualization
            draw_height_offset = 0.00  # [m] Lift the point slightly above the support plane for visibility
            draw_point_rgba = [1.0, 0.85, 0.1, 1.0]  # RGBA color of the ZMP point
