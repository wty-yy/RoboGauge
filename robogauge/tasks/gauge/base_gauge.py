# -*- coding: utf-8 -*-
'''
@File    : base_gauge.py
@Time    : 2025/11/27 15:55:19
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Base Gauge for Robogauge
'''
from robogauge.tasks.robots.base_robot_config import RobotConfig
from robogauge.tasks.gauge.base_gauge_config import BaseGaugeConfig
from robogauge.tasks.gauge.goal_data import GoalData, VelocityGoal, PositionGoal
from robogauge.tasks.simulator.sim_data import SimData
from robogauge.utils.logger import logger

class BaseGauge:
    def __init__(self, cfg: BaseGaugeConfig):
        self.cfg = cfg
    
    def is_reset(self) -> bool:
        return False
    
    def is_done(self) -> bool:
        return False
    
    def get_goal(self) -> GoalData:
        goal = GoalData(
            goal_type='velocity',
            velocity_goal=VelocityGoal(
                lin_vel=[5.0, 0.0, 0.0],
                ang_vel=[0.0, 0.0, 0.0]
            )
        )
        return goal
    
    def update_metrics(self, sim_data: SimData):
        if sim_data.n_step % int(0.1 / sim_data.sim_dt) != 0:
            return
        for i in range(len(sim_data.proprio.joint.force)):
            logger.log(sim_data.proprio.joint.force[i], f'dof/force_{i}', step=sim_data.n_step)
    