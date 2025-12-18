# -*- coding: utf-8 -*-
'''
@File    : vel_metrics.py
@Time    : 2025/12/18 20:18:56
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Velocity Metrics Implementation
'''
import numpy as np

from robogauge.tasks.robots import RobotConfig
from robogauge.tasks.gauge.metrics.base_metric import BaseMetric, SimData, GoalData

from robogauge.utils.logger import logger
from robogauge.utils.helpers import class_to_dict


class LinVelErrMetric(BaseMetric):
    """ Metric to log linear velocity error. """
    name = 'lin_vel_err_metric'

    def __init__(self, robot_cfg: RobotConfig, **kwargs):
        super().__init__(robot_cfg)
        max_ranges = []
        cfg_commands = class_to_dict(robot_cfg.commands)
        for name in ['lin_vel_x', 'lin_vel_y', 'lin_vel_z']:
            cmds = cfg_commands.get(name)
            if cmds is not None:
                max_ranges.append(max(abs(cmds[0]), abs(cmds[1])))
        self.norm_vel = np.linalg.norm(max_ranges)
    
    def __call__(self, sim_data: SimData, goal_data: GoalData) -> float:
        if goal_data.goal_type != 'velocity':
            logger.warning("LinVelErrMetric can only be used with VelocityGoal.")
            return 0.0
        lin_vel = sim_data.proprio.base.lin_vel
        target_lin_vel = [goal_data.velocity_goal.lin_vel_x, goal_data.velocity_goal.lin_vel_y, goal_data.velocity_goal.lin_vel_z]
        vel_err = np.linalg.norm(lin_vel - target_lin_vel) / self.norm_vel
        logger.log(vel_err, f'vel_metrics/lin_vel_err', step=sim_data.n_step)
        return 1 - vel_err

class AngVelErrMetric(BaseMetric):
    """ Metric to log angular velocity error. """
    name = 'ang_vel_err_metric'

    def __init__(self, robot_cfg: RobotConfig, **kwargs):
        super().__init__(robot_cfg)
        max_ranges = []
        cfg_commands = class_to_dict(robot_cfg.commands)
        for name in ['ang_vel_roll', 'ang_vel_pitch', 'ang_vel_yaw']:
            cmds = cfg_commands.get(name)
            if cmds is not None:
                max_ranges.append(max(abs(cmds[0]), abs(cmds[1])))
        self.norm_vel = np.linalg.norm(max_ranges)
    
    def __call__(self, sim_data: SimData, goal_data: GoalData) -> float:
        if goal_data.goal_type != 'velocity':
            logger.warning("AngVelErrMetric can only be used with VelocityGoal.")
            return 0.0
        ang_vel = sim_data.proprio.base.ang_vel
        target_ang_vel = [goal_data.velocity_goal.ang_vel_roll, goal_data.velocity_goal.ang_vel_pitch, goal_data.velocity_goal.ang_vel_yaw]
        vel_err = np.linalg.norm(ang_vel - target_ang_vel) / self.norm_vel
        logger.log(vel_err, f'vel_metrics/ang_vel_err', step=sim_data.n_step)
        return 1 - vel_err
