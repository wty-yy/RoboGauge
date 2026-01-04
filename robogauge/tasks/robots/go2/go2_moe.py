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
from collections import defaultdict

from robogauge.tasks.robots.go2.go2 import Go2
from robogauge.utils.logger import logger

class Go2MoE(Go2):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.save_info = defaultdict(list)
        self.save_count = 0

    def get_action(self, obs: np.ndarray):
        obs_tensor = torch.tensor(obs, dtype=torch.float32).unsqueeze(0).to(self.device)
        action, results = self.model(obs_tensor)
        if isinstance(results, tuple) and len(results) == 2:
            weights, latent = results
            latent = latent.detach().cpu().numpy().squeeze(0) if latent is not None else None
            weights = weights.detach().cpu().numpy().squeeze(0) if weights is not None else None
            if self.cfg.control.save_additional_output:
                self.save_info['latent'].append(latent)
                self.save_info['weights'].append(weights)
        action = action.detach().cpu().numpy().squeeze(0)[self.model2mj_idx]
        self.last_action = action
        target_dof_pos = action * self.action_scale + self.default_dof_pos
        return target_dof_pos, self.p_gains, self.d_gains, self.control_type

    def reset(self):
        super().reset()
        save_path = logger.log_dir / f"moe_info_{self.save_count}.npz"
        if self.cfg.control.save_additional_output:
            np.savez_compressed(save_path,
                weights=np.array(self.save_info['weights']),
                latent=np.array(self.save_info['latent'])
            )
            logger.info(f"Saved MoE info to {save_path}")
        self.save_count += 1
        self.save_info = defaultdict(list)
