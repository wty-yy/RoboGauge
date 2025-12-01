# -*- coding: utf-8 -*-
'''
@File    : base_goals.py
@Time    : 2025/11/30 21:52:59
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Base Goal Class
'''

from collections import defaultdict
from robogauge.utils.measure import Average
from robogauge.tasks.gauge.goal_data import GoalData
from robogauge.tasks.simulator.sim_data import SimData

class BaseGoal:
    name = 'base_goal'

    def __init__(self):
        self.count = 0
        self.total = 0
        self.sub_name = None

        self._goal_mean_metrics = defaultdict(Average)
        self.last_sub_name = None
        self._sub_goal_mean_metrics = defaultdict(Average)

    def is_done(self) -> bool:
        raise NotImplementedError

    def is_reset(self, sim_data: SimData) -> bool:
        raise NotImplementedError

    def get_goal(self, sim_data: SimData) -> GoalData:
        raise NotImplementedError

    def __repr__(self):
        if self.sub_name is None:
            return f"{self.name}"
        return f"{self.name}/{self.sub_name}"
    
    def update_metrics(self, metrics: dict):
        """ Update step metrics for the current goal and sub-goal."""
        if self.last_sub_name is None or self.last_sub_name != self.sub_name:
            self.last_sub_name = self.sub_name
            self._sub_goal_mean_metrics = defaultdict(Average)
        for metric_name, value in metrics.items():
            self._goal_mean_metrics[metric_name].update(value)
            self._sub_goal_mean_metrics[metric_name].update(value)
    
    @property
    def goal_mean_metrics(self):
        """ Get the mean metrics for the current goal. """
        return {k: float(v.mean) for k, v in self._goal_mean_metrics.items()}
    
    @property
    def sub_goal_mean_metrics(self):
        """ Get the mean metrics for the current sub-goal. """
        if len(self._sub_goal_mean_metrics) == 0:
            return {}
        return {k: float(v.mean) for k, v in self._sub_goal_mean_metrics.items()}
