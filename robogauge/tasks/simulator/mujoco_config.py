# -*- coding: utf-8 -*-
'''
@File    : mujoco_config.py
@Time    : 2025/11/27 15:55:34
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Mujoco Simulator Configuration
'''
from robogauge.utils.config import Config

class MujocoConfig(Config):
    simulator_class = 'MujocoSimulator'

    class physics:
        simulation_dt = 0.002  # 500 Hz
    
    class viewer:
        headless = False
        block_rendering = True  # Whether to block rendering in the viewer loop.
        camera_distance = 2.0
        camera_elevation = -20.0
        camera_azimuth = 60.0
    
    class render:
        save_video = False
        video_fps = 30
        width = 640
        height = 480
        # width = 1920
        # height = 1080
    
    class domain_rand:
        # With randomization
        action_delay = True  # [0, control_dt]

        # Setup by config file, ensure evaluation coverage
        base_mass = 0.0  # [kg], {-1, 0, 1, 2, 3}
        friction = 0.0  # [N.s/m], {0.4, 0.7, 1.0, 1.3, 1.6}

    class noise:
        # Uniform noise
        enabled = True
        lin_vel = 0.05      # [m/s]
        ang_vel = 0.8       # [rad/s]
        joint_pos = 0.01    # [rad]
        joint_vel = 3.0    # [rad/s]

    class truncation:
        enabled = True
        projected_gravity_rad = 2.5  # [rad], if gravity projection angle exceeds this value, truncate episode
        penetration_threshold = -0.035  # [m], if any contact penetration depth is below this threshold, truncate episode
        skip_penetration_geoms = ['wall', 'floor']  # Geometries to skip penetration check
        skip_self_penetration = True  # Whether to check self-penetration
        penetration_max_reset_num = 1  # Max number of resets due to penetration per run
