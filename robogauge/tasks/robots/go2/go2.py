# -*- coding: utf-8 -*-
'''
@File    : go2.py
@Time    : 2025/11/28 15:27:07
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : None
'''
import torch
import numpy as np

from robogauge.tasks.robots.base_robot import BaseRobot
from robogauge.utils.math_utils import get_projected_gravity
from robogauge.tasks.robots.go2.go2_config import Go2Config
from robogauge.tasks.simulator.sim_data import SimData
from robogauge.tasks.gauge.goal_data import GoalData
from robogauge.utils.logger import logger

class Go2(BaseRobot):
    def __init__(self, cfg: Go2Config):
        super().__init__(cfg)
        self.cmd_range = cfg.commands
        self.default_dof_pos = np.array(cfg.control.default_dof_pos, dtype=np.float32)
        self.last_action = np.zeros(self.num_action, dtype=np.float32)
        self.action_scale = cfg.control.scales.action
        self.mj2model_idx = self.cfg.control.mj2model_dof_indices
        self.model2mj_idx = [self.mj2model_idx.index(i) for i in range(len(self.mj2model_idx))]
    
    def build_observation(self, sim_data: SimData, goal_data: GoalData) -> np.ndarray:
        sim_proprio = sim_data.proprio
        obs = np.zeros(self.num_obs)
        if goal_data.goal_type == 'velocity':
            ang_vel = sim_proprio.imu.ang_vel * self.cfg.control.scales.ang_vel
            projected_gravity = get_projected_gravity(sim_proprio.imu.quat)
            dof_pos = (sim_proprio.joint.pos - self.default_dof_pos) * self.cfg.control.scales.dof_pos
            dof_vel = sim_proprio.joint.vel * self.cfg.control.scales.dof_vel

            goal = goal_data.velocity_goal
            cmd = np.array([goal.lin_vel_x, goal.lin_vel_y, goal.ang_vel_yaw], dtype=np.float32)
            cmd = np.minimum(np.maximum(cmd, np.array([self.cmd_range.lin_vel_x[0], self.cmd_range.lin_vel_y[0], self.cmd_range.ang_vel_yaw[0]], dtype=np.float32)), 
                             np.array([self.cmd_range.lin_vel_x[1], self.cmd_range.lin_vel_y[1], self.cmd_range.ang_vel_yaw[1]], dtype=np.float32))
            
            cmd *= self.cfg.control.scales.cmd

            obs[:3] = ang_vel
            obs[3:6] = projected_gravity
            obs[6:9] = cmd
            obs[9:9+self.num_action] = dof_pos[self.mj2model_idx]
            obs[9+self.num_action:9+2*self.num_action] = dof_vel[self.mj2model_idx]
            obs[9+2*self.num_action:9+3*self.num_action] = self.last_action[self.mj2model_idx]
        else:
            raise NotImplementedError(f"Goal type '{goal_data.goal_type}' not implemented in Go2 robot.")
        return obs
    
    def reset(self):
        self.last_action = np.zeros(self.num_action, dtype=np.float32)
        self.model.reset()  # reset history

    def get_action(self, obs: np.ndarray):
        obs_tensor = torch.tensor(obs, dtype=torch.float32).unsqueeze(0).to(self.device)
        action = self.model(obs_tensor).detach().cpu().numpy().squeeze(0)[self.model2mj_idx]
        self.last_action = action
        target_dof_pos = action * self.action_scale + self.default_dof_pos
        return target_dof_pos, self.p_gains, self.d_gains, self.control_type
