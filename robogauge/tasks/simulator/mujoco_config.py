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
        height = 480
        width = 640
