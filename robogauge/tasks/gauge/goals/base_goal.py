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
from robogauge.tasks.gauge.base_gauge_config import QUALITY_WEIGHTS

class BaseGoal:
    name = 'base_goal'

    def __init__(self):
        self.count = 0  # current task index
        self.total = 0  # total tasks
        self.sub_name = None

        self.goal_metrics = defaultdict(list)
        self.goal_quality_scores = []

    def pre_get_goal(self) -> bool:
        raise NotImplementedError
    
    def reset_goal(self):
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
        """ Update step metrics for the current goal."""
        quality_score = 1.0
        for metric_name, value in metrics.items():
            self.goal_metrics[metric_name].append(value)
            quality_score *= min(max(1e-9, value), 1.0) ** QUALITY_WEIGHTS[metric_name]
        quality_score = quality_score ** (1.0 / sum(QUALITY_WEIGHTS.values()))
        self.goal_quality_scores.append(quality_score)
    
    @property
    def goal_mean_metrics(self):
        """ Get the mean metrics for the current goal. """
        result = {k: self._analysis_metrics(v) for k, v in self.goal_metrics.items()}
        result['quality_score'] = self._analysis_metrics(self.goal_quality_scores)
        return result

    @staticmethod
    def _analysis_metrics(metrics: list):
        result = {'mean': 0}
        for i in [25, 50]:
            result[f'mean@{i}'] = 0
        if len(metrics) == 0:
            return result
        metrics = [max(0.0, min(1.0, m)) for m in metrics]
        metrics.sort()
        result['mean'] = float(sum(metrics) / len(metrics))
        for i in [25, 50]:
            count = max(1, int(len(metrics) * i / 100))
            result[f'mean@{i}'] = float(sum(metrics[:count]) / count)
        return result
