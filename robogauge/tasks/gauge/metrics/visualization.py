# -*- coding: utf-8 -*-
'''
@File    : visualization.py
@Time    : 2025/12/18 20:19:09
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Visualization Metric Implementation
'''
from robogauge.tasks.robots import RobotConfig
from robogauge.tasks.gauge.metrics.base_metric import BaseMetric, SimData, GoalData

from robogauge.utils.logger import logger

class VisualizationMetric(BaseMetric):
    """ Metric to visualize various robot states in the simulator. """
    name = 'visualization_metric'

    def __init__(self,
        robot_cfg: RobotConfig,
        dof_torque: bool = False,
        dof_pos: bool = False,
        **kwargs
    ):
        super().__init__(robot_cfg)
        self.dof_torque = dof_torque
        self.dof_pos = dof_pos

    def __call__(self, sim_data: SimData, goal_data: GoalData) -> float:
        for i in range(len(sim_data.proprio.joint.torque)):
            name = sim_data.proprio.joint.names[i]
            if self.dof_torque:
                torque = sim_data.proprio.joint.torque[i]
                logger.log(torque, f'dof_torque/{name}', step=sim_data.n_step)
            if self.dof_pos:
                pos = sim_data.proprio.joint.pos[i]
                logger.log(pos, f'dof_pos/{name}', step=sim_data.n_step)
        return 0.0
