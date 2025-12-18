# -*- coding: utf-8 -*-
'''
@File    : dof_metrics.py
@Time    : 2025/12/18 20:18:24
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : DOF Limits Metric Implementation
'''
import numpy as np

from robogauge.tasks.robots import RobotConfig
from robogauge.tasks.gauge.metrics.base_metric import BaseMetric, GoalData, SimData

from robogauge.utils.logger import logger


class DofLimitsMetric(BaseMetric):
    """ Metric to log DOF limit violations. """
    name = 'dof_limits_metric'

    def __init__(self,
        robot_cfg: RobotConfig,
        soft_dof_limit_ratio: float = 0.9,
        dof_names: list = None,
        **kwargs
    ):
        super().__init__(robot_cfg)
        self.soft_dof_limit_ratio = soft_dof_limit_ratio
        self.calc_dof_names = dof_names
    
    def __call__(self, sim_data: SimData, goal_data: GoalData) -> float:
        values = []
        for i in range(len(sim_data.proprio.joint.limits)):
            lower_limit = sim_data.proprio.joint.limits[i, 0]
            upper_limit = sim_data.proprio.joint.limits[i, 1]
            dof_range = upper_limit - lower_limit
            soft_lower_limit = lower_limit + (1 - self.soft_dof_limit_ratio) * dof_range
            soft_upper_limit = upper_limit - (1 - self.soft_dof_limit_ratio) * dof_range

            pos = sim_data.proprio.joint.pos[i]
            dof_name = sim_data.proprio.joint.names[i]
            value = 0
            if pos < soft_lower_limit:
                value = soft_lower_limit - pos
            elif pos > soft_upper_limit:
                value = pos - soft_upper_limit
            value /= dof_range  # Normalize by DOF range
            logger.log(value, f'dof_limits/{dof_name}', step=sim_data.n_step)
            if self.calc_dof_names is not None:
                for use_name in self.calc_dof_names:
                    if use_name in dof_name:
                        values.append(value)
            else:
                values.append(value)
        rms_value = 1 - np.sqrt(np.mean(np.square(values)))
        logger.log(1 - rms_value, f'dof_limits/rms', step=sim_data.n_step)
        return rms_value

class DofPowerMetric(BaseMetric):
    """ Metric to log DOF power efficiency. """
    name = 'dof_power_metric'

    def __init__(self,
        robot_cfg: RobotConfig,
        scaling_factor: float = 100.0,
        **kwargs
    ):
        super().__init__(robot_cfg)
        self.scaling_factor = scaling_factor
    
    def __call__(self, sim_data: SimData, goal_data: GoalData) -> float:
        values = []
        for i in range(len(sim_data.proprio.joint.torque)):
            torque = sim_data.proprio.joint.torque[i]
            velocity = sim_data.proprio.joint.vel[i]
            power = abs(torque * velocity)
            values.append(power)
            dof_name = sim_data.proprio.joint.names[i]
            logger.log(power, f'dof_power/{dof_name}', step=sim_data.n_step)
        rms_power = np.sqrt(np.mean(np.square(values)))
        metric_power = 1 - rms_power / self.scaling_factor
        logger.log(rms_power, f'dof_power/rms', step=sim_data.n_step)
        return metric_power
