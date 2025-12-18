# -*- coding: utf-8 -*-
'''
@File    : height_metric.py
@Time    : 2025/12/18 20:18:33
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Orientation Stability, Torque Smoothness Metric Implementation
'''
import numpy as np

from robogauge.tasks.robots import RobotConfig
from robogauge.tasks.gauge.metrics.base_metric import BaseMetric, GoalData, SimData
from robogauge.utils.math_utils import get_projected_gravity

from robogauge.utils.logger import logger


class OrientationStabilityMetric(BaseMetric):
    """ Metric to log height stability. """
    name = 'height_std_metric'

    def __init__(self,
        robot_cfg: RobotConfig,
        **kwargs
    ):
        super().__init__(robot_cfg)
    
    def __call__(self, sim_data: SimData, goal_data: GoalData) -> float:
        projected_gravity = get_projected_gravity(sim_data.proprio.base.quat)
        projected_x = projected_gravity[0]
        metric_value = 1 - abs(projected_x)  # consider roll only
        logger.log(abs(projected_x), f'stable_metric/projected_x_abs', step=sim_data.n_step)
        return metric_value

class TorqueSmoothnessMetric(BaseMetric):
    """ Metric to log torque smoothness. """
    name = 'torque_smoothness_metric'

    def __init__(self,
        robot_cfg: RobotConfig,
        scaling_factor: float = 30.0,
        **kwargs
    ):
        super().__init__(robot_cfg)
        self.last_torque = None
        self.scaling_factor = scaling_factor
    
    def reset(self):
        self.last_torque = None
    
    def __call__(self, sim_data: SimData, goal_data: GoalData) -> float:
        current_torque = np.array(sim_data.proprio.joint.torque, np.float32)
        if self.last_torque is None:
            self.last_torque = current_torque
            return 1.0  # No change at first step
        torque_diff = current_torque - self.last_torque
        rms_value = np.sqrt(np.mean(np.square(torque_diff)))
        metric_value = 1.0 - rms_value / self.scaling_factor
        logger.log(rms_value, f'stable_metric/torque_rms_diff', step=sim_data.n_step)
        return metric_value