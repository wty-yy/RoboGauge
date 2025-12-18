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

from robogauge.utils.helpers import parse_path
from robogauge.utils.logger import logger
from robogauge.tasks.robots.base_robot_config import RobotConfig
from robogauge.tasks.simulator.sim_data import SimData
from robogauge.tasks.gauge.goal_data import GoalData

class BaseRobot:
    def __init__(self, cfg: RobotConfig):
        self.cfg = cfg
        self.device = self.cfg.control.device
        self.num_obs = cfg.control.num_observations
        self.num_action = cfg.control.num_actions
        self.control_type = cfg.control.control_type
        self.p_gains = np.array(cfg.control.p_gains)
        self.d_gains = np.array(cfg.control.d_gains)
        model_path = parse_path(cfg.control.model_path)
        logger.info(f"Loading robot model from '{model_path}'")
        self.model = torch.jit.load(model_path).to(self.device)
        self.model.eval()
    
    def build_observation(self, sim_data: SimData, goal_data: GoalData) -> np.ndarray:
        obs = np.zeros(self.num_obs, dtype=np.float32)
        return obs
    
    def get_action(self, obs: np.ndarray):
        """
        Returns:
            action: (num_action,) target joint positions/velocities/torques
            p_gains: (num_action,) proportional gains for Mujoco PD controller
            d_gains: (num_action,) derivative gains for Mujoco PD controller
            control_type: 'P', 'V', or 'T' for position/velocity/torque control
        """
        action = np.zeros(self.num_action, dtype=np.float32)
        return action, self.p_gains, self.d_gains, self.control_type

