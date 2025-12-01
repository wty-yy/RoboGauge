# -*- coding: utf-8 -*-
'''
@File    : velocity_goals.py
@Time    : 2025/11/30 21:44:13
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Velocity Goals Implementation
'''
from typing import Optional

from robogauge.tasks.gauge.goals import BaseGoal
from robogauge.tasks.robots import RobotConfig
from robogauge.tasks.simulator.sim_data import SimData
from robogauge.tasks.gauge.goal_data import GoalData, VelocityGoal
from robogauge.utils.helpers import class_to_dict
from robogauge.utils.logger import logger

class MaxVelocityGoal(BaseGoal):
    name = "max_velocity"

    """ Goal class for maximizing velocity commands. """
    def __init__(self, max_velocity: RobotConfig.commands, cmd_duration: float = 5, **kwargs):
        super().__init__()
        kwargs.pop('enabled', None)
        if kwargs:
            logger.warning(f"Unused kwargs in MaxVelocityGoal: {kwargs}")

        self.max_velocity = class_to_dict(max_velocity)
        self.cmd_duration = cmd_duration
        self.last_reset_time = 0.0

        self.goals = []
        for key in ['lin_vel_x', 'lin_vel_y', 'lin_vel_z', 'ang_vel_roll', 'ang_vel_pitch', 'ang_vel_yaw']:
            if self.max_velocity.get(key) is None: continue
            for value in self.max_velocity[key]:
                if value != 0:
                    self.goals.append(VelocityGoal(**{key: value}))
        
        self.count = 0
        self.total = len(self.goals)
        if len(self.goals) == 0:
            logger.warning("MaxVelocityGoal initialized with no valid velocity commands.")
            return
        self.sub_name = str(self.goals[0])

    def is_reset(self, sim_data: SimData) -> bool:
        if sim_data.sim_time - self.last_reset_time >= self.cmd_duration:
            self.last_reset_time = sim_data.sim_time
            return True
        return False

    def get_goal(self, sim_data: SimData) -> Optional[GoalData]:
        self.count = int(sim_data.sim_time / self.cmd_duration)
        if self.count >= self.total:
            return None
        self.current_goal = self.goals[self.count]
        self.sub_name = str(self.current_goal)
        return GoalData(
            goal_type='velocity',
            velocity_goal=self.current_goal
        )
