# -*- coding: utf-8 -*-
'''
@File    : base_gauge.py
@Time    : 2025/11/27 15:55:19
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Base Gauge for Robogauge
'''
from typing import List
from functools import partial

from robogauge.utils.logger import logger
from robogauge.utils.helpers import class_to_dict

from robogauge.tasks.robots import RobotConfig
from robogauge.tasks.gauge.base_gauge_config import BaseGaugeConfig
from robogauge.tasks.gauge.goal_data import GoalData, VelocityGoal, PositionGoal
from robogauge.tasks.simulator.sim_data import SimData

from robogauge.tasks.gauge.goals import BaseGoal, MaxVelocityGoal
from robogauge.tasks.gauge.metrics import dof_limits_metric

class BaseGauge:
    def __init__(self, cfg: BaseGaugeConfig, robot_cfg: RobotConfig):
        self.cfg = cfg
        self.goals_cfg = class_to_dict(self.cfg.goals)
        self.metrics_cfg = class_to_dict(self.cfg.metrics)

        self.goal_str = ""
        self.goal_idx = 0
        self.goals: List[BaseGoal] = []
        self.metrics: List[function] = []
        self.info = {
            'goal': [],
            'metric': [],
        }

        log_str = "Initialized Gauge with Goals:\n"
        for name, kwargs in self.goals_cfg.items():
            if not kwargs['enabled']: continue
            if name == 'max_velocity':
                self.goals.append(MaxVelocityGoal(robot_cfg.commands, **kwargs))
                log_str += f"  - Max Velocity Goal: {kwargs}\n"
            else:
                raise NotImplementedError(f"Goal '{name}' is not implemented in BaseGauge.")
            self.info['goal'].append(name)
        for name, enabled in self.metrics_cfg.items():
            if not enabled: continue
            metric_func = eval(f"{name}_metric")
            self.metrics.append(partial(metric_func, robot_cfg=robot_cfg, **self.metrics_cfg[name]))
            log_str += f"  - Metric: {name}\n"
            self.info['metric'].append(name)
        logger.info(log_str.strip())
    
    def is_reset(self, sim_data: SimData) -> bool:
        if self.goal_idx >= len(self.goals):
            return False
        return self.goals[self.goal_idx].is_reset(sim_data)
    
    def is_done(self) -> bool:
        if self.goal_idx >= len(self.goals):
            return True
        return False
    
    def get_goal(self, sim_data: SimData) -> GoalData:
        # goal = GoalData(
        #     goal_type='velocity',
        #     velocity_goal=VelocityGoal(
        #         ang_vel_yaw=-5.0,
        #     )
        # )
        if self.goal_idx >= len(self.goals):
            logger.error("All goals have been exhausted.")
            return None
        goal_instance = self.goals[self.goal_idx]
        goal = goal_instance.get_goal(sim_data)
        if goal is None:
            self.goal_idx += 1
            return None

        now_goal_str = str(goal_instance)
        if now_goal_str != self.goal_str:
            self.goal_str = now_goal_str
            logger.info(f"New Goal [{self.goal_idx+1}/{len(self.goals)}] [{goal_instance.count+1}/{goal_instance.total}]: {self.goal_str}")
        return goal
    
    def update_metrics(self, sim_data: SimData):
        if sim_data.n_step % int(0.1 / sim_data.sim_dt) != 0:
            return
        for i in range(len(sim_data.proprio.joint.force)):
            logger.log(sim_data.proprio.joint.force[i], f'dof/force_{i}', step=sim_data.n_step)
        for metric_func in self.metrics:
            metric_func(sim_data)
    