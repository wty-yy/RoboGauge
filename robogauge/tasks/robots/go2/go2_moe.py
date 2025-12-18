# -*- coding: utf-8 -*-
'''
@File    : go2_moe.py
@Time    : 2025/12/05 17:29:16
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : None
'''
import torch
import numpy as np

from robogauge.tasks.robots.go2.go2 import Go2

class Go2MoE(Go2):
    def get_action(self, obs: np.ndarray):
        obs_tensor = torch.tensor(obs, dtype=torch.float32).unsqueeze(0).to(self.device)
        action, weights = self.model(obs_tensor)
        action = action.detach().cpu().numpy().squeeze(0)[self.model2mj_idx]
        weights = weights.detach().cpu().numpy().squeeze(0)
        self.last_action = action
        target_dof_pos = action * self.action_scale + self.default_dof_pos
        return target_dof_pos, self.p_gains, self.d_gains, self.control_type
