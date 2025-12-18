# -*- coding: utf-8 -*-
'''
@File    : base_metric.py
@Time    : 2025/12/18 20:18:45
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Base Metric Implementation
'''
from robogauge.utils.logger import logger
from robogauge.tasks.robots import RobotConfig
from robogauge.tasks.simulator.sim_data import SimData
from robogauge.tasks.gauge.goals.base_goal import GoalData

class BaseMetric:
    """ Base class for all metric functions. """
    name = 'base_metric'

    def __init__(self, robot_cfg: RobotConfig, **kwargs):
        self.robot_cfg = robot_cfg
    
    def reset(self):
        pass

    def __call__(self, sim_data: SimData, goal_data: GoalData) -> float:
        value = 0.0
        logger.log(value, self.name, step=sim_data.n_step)
        return value
