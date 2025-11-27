# -*- coding: utf-8 -*-
'''
@File    : base_robot.py
@Time    : 2025/11/27 15:53:57
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Base Robot Class
'''
import torch
import numpy as np
from robogauge.tasks.robots.base_robot_config import RobotConfig

class BaseRobot:
    def __init__(self, cfg: RobotConfig):
        self.num_act = cfg.mdp.num_actions
        self.num_obs = cfg.mdp.num_observations
        self.model = None
    
    def load_model(self):
        ...
    
    def build_observation(self, sim_info: dict, goal_info: dict) -> np.ndarray:
        obs = np.zeros(self.num_obs)
        return obs
    
    def get_action(self, obs) -> np.ndarray:
        action = np.zeros_like(self.num_act)
        return action
