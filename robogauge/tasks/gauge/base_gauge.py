# -*- coding: utf-8 -*-
'''
@File    : base_gauge.py
@Time    : 2025/11/27 15:55:19
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Base Gauge for Robogauge
'''
import yaml
from typing import List
from pathlib import Path
from functools import partial

from robogauge.utils.logger import logger
from robogauge.utils.helpers import class_to_dict, snake_to_pascal

from robogauge.tasks.robots import RobotConfig
from robogauge.tasks.gauge.base_gauge_config import BaseGaugeConfig
from robogauge.tasks.gauge.goal_data import GoalData, VelocityGoal, PositionGoal
from robogauge.tasks.simulator.sim_data import SimData

from robogauge.tasks.gauge.goals import BaseGoal, MaxVelocityGoal, DiagonalVelocityGoal
from robogauge.tasks.gauge.metrics import *

class BaseGauge:
    def __init__(self, cfg: BaseGaugeConfig, robot_cfg: RobotConfig):
        self.cfg = cfg
        self.robot_cfg = robot_cfg
        self.goals_cfg = class_to_dict(self.cfg.goals)
        self.metrics_cfg = class_to_dict(self.cfg.metrics)

        self.goal_str = ""
        self.goal_idx = 0
        self.goals: List[BaseGoal] = []
        self.metrics: List[function] = []
        self.info = {'goal': [], 'metric': []}
        self.results = {}  # {'goal/sub_goal': {'metric': result}}

        log_str = "Initialized Gauge with Goals and Metrics:\n"
        for name, kwargs in self.goals_cfg.items():
            if not kwargs['enabled']: continue
            if name == 'max_velocity':
                self.goals.append(MaxVelocityGoal(robot_cfg.commands, **kwargs))
                log_str += f"  - Max Velocity Goal: {kwargs}\n"
            elif name == 'diagonal_velocity':
                self.goals.append(DiagonalVelocityGoal(robot_cfg.commands, **kwargs))
                log_str += f"  - Diagonal Velocity Goal: {kwargs}\n"
            else:
                raise NotImplementedError(f"Goal '{name}' is not implemented in BaseGauge.")
            self.info['goal'].append(name)
        for name, enabled in self.metrics_cfg.items():
            if not enabled: continue
            if name in ['metric_dt']: continue
            metric_class_name = f"{snake_to_pascal(name)}Metric"
            metric_class = eval(metric_class_name)
            self.metrics.append(metric_class(robot_cfg=robot_cfg, **self.metrics_cfg[name]))
            log_str += f"  - Metric: {name}\n"
            self.info['metric'].append(metric_class_name)
        logger.info(log_str.strip())

        if len(self.goals) == 0:
            logger.warning("No goals have been configured for the Gauge. Exiting.")
        else:
            self.create_new_goal_logger()
    
    def is_reset(self, sim_data: SimData) -> bool:
        if self.goal_idx >= len(self.goals):
            return False
        return self.goals[self.goal_idx].is_reset(sim_data)
    
    def is_done(self) -> bool:
        if self.goal_idx >= len(self.goals):
            self.save_results()
            return True
        return False

    def create_new_goal_logger(self):
        """ Create a new logger for new goal to metrics. """
        if self.goal_idx >= len(self.goals): return
        logger.create_tensorboard(
            self.robot_cfg.robot_name,
            Path(self.robot_cfg.control.model_path).stem,
            self.goals[self.goal_idx].name
        )
    
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
        goal_obj = self.goals[self.goal_idx]
        goal = goal_obj.get_goal(sim_data)

        if goal is None:  # goal obj finished
            self.results[goal_obj.name] = goal_obj.goal_mean_metrics
            self.goal_idx += 1
            self.create_new_goal_logger()
            return None

        now_goal_str = str(goal_obj)
        if now_goal_str != self.goal_str:  # sub goal changed
            self.goal_str = now_goal_str
            logger.info(f"New Goal [{self.goal_idx+1}/{len(self.goals)}] [{goal_obj.count+1}/{goal_obj.total}]: {self.goal_str}")
        return goal
    
    def update_metrics(self, sim_data: SimData):
        if sim_data.n_step % int(self.cfg.metrics.metric_dt / sim_data.sim_dt) != 0:
            return
        metrics_results = {}
        for metric_name, metric_obj in zip(self.info['metric'], self.metrics):
            val = metric_obj(sim_data)
            if metric_name not in ['visualization']:
                metrics_results[metric_name] = val
        self.goals[self.goal_idx].update_metrics(metrics_results)

    def save_results(self):
        """ Save the results to a yaml file. """
        save_path = Path(logger.log_dir) / "results.yaml"
        with open(save_path, 'w') as file:
            yaml.dump(self.results, file)
            yaml_str = yaml.dump(self.results)
        logger.info(
            f"""\n{'='*20} Goals and Metrics results {'='*20}\n"""
            f"""{yaml_str}"""
            f"""{'='*68}"""
        )
        logger.info(f"Saved metric results to {save_path}")
