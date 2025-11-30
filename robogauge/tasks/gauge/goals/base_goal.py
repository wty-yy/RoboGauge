# -*- coding: utf-8 -*-
'''
@File    : base_goals.py
@Time    : 2025/11/30 21:52:59
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Base Goal Class
'''

from robogauge.tasks.simulator.sim_data import SimData
from robogauge.tasks.gauge.goal_data import GoalData

class BaseGoal:
    count = 0
    total = 0

    def is_done(self) -> bool:
        raise NotImplementedError

    def is_reset(self, sim_data: SimData) -> bool:
        raise NotImplementedError

    def get_goal(self, sim_data: SimData) -> GoalData:
        raise NotImplementedError
