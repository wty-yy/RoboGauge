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
from collections import defaultdict

import numpy as np
from robogauge.utils.logger import logger
from robogauge.utils.helpers import class_to_dict, snake_to_pascal

from robogauge.tasks.robots import RobotConfig
from robogauge.tasks.gauge.base_gauge_config import BaseGaugeConfig
from robogauge.tasks.gauge.goal_data import GoalData, VelocityGoal, PositionGoal
from robogauge.tasks.simulator.sim_data import SimData
from robogauge.tasks.gauge.gauge_configs.terrain_levels_config import SEARCH_LEVELS_TERRAINS

from robogauge.tasks.gauge.goals import *
from robogauge.tasks.gauge.metrics import *

class BaseGauge:
    def __init__(self,
            cfg: BaseGaugeConfig,
            robot_cfg: RobotConfig,
        ):
        self.cfg = cfg
        self.robot_cfg = robot_cfg
        self.goals_cfg = class_to_dict(self.cfg.goals)
        self.metrics_cfg = class_to_dict(self.cfg.metrics)

        self.goal_str = "Init"
        self.goal_idx = 0
        self.goals: List[BaseGoal] = []
        self.metrics: List[function] = []
        self.info = {'goal': [], 'metric': []}
        self.results = {}  # {'goal/sub_goal': {'metric': result}}

        log_str = "Initialized Gauge with Goals 🎯 and Metrics 📊:\n"
        for name, kwargs in self.goals_cfg.items():
            if not kwargs['enabled']: continue
            if name == 'max_velocity':
                self.goals.append(MaxVelocityGoal(robot_cfg.control.control_dt, robot_cfg.commands, **kwargs))
                log_str += f"  - Max Velocity Goal: {kwargs}\n"
            elif name == 'diagonal_velocity':
                self.goals.append(DiagonalVelocityGoal(robot_cfg.control.control_dt, robot_cfg.commands, **kwargs))
                log_str += f"  - Diagonal Velocity Goal: {kwargs}\n"
            elif name == 'target_pos_velocity':
                self.goals.append(TargetPosVelocityGoal(robot_cfg.control.control_dt, cfg.backward, **kwargs))
                log_str += f"  - Target Position Velocity Goal: {kwargs}\n"
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
            self.info['metric'].append(name)
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
        if self.goal_idx >= len(self.goals) or not self.cfg.write_tensorboard:
            return
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
        goal_obj = self.goals[self.goal_idx]
        if goal_obj.pre_get_goal(sim_data):  # goal finished
            self.switch_to_next_goal()
            return None
        goal = goal_obj.get_goal(sim_data)

        now_goal_str = str(goal_obj)
        if f"{goal_obj.count+1}_{now_goal_str}" != self.goal_str:  # sub goal changed
            self.goal_str = f"{goal_obj.count+1}_{now_goal_str}"
            logger.info(f"New Goal [{self.goal_idx+1}/{len(self.goals)}] [{goal_obj.count+1}/{goal_obj.total}]: {self.goal_str}")
        return goal
    
    def reset_current_goal(self):
        """ Reset the current goal """
        if self.goal_idx >= len(self.goals):
            return
        goal_obj = self.goals[self.goal_idx]
        goal_obj.reset_goal()
    
    def switch_to_next_goal(self):
        """ Switch to the next goal and log the metrics of the current goal. """
        goal_obj = self.goals[self.goal_idx]
        metrics = goal_obj.goal_mean_metrics
        if hasattr(goal_obj, 'success'):  # target position goal
            metrics['success'] = {'mean': float(goal_obj.success)}
        
        key = f"{goal_obj.name}"
        self.results[key] = metrics

        self.goal_idx += 1
        self.create_new_goal_logger()
    
    def update_metrics(self, sim_data: SimData, goal_data: GoalData):
        if sim_data.n_step % int(self.cfg.metrics.metric_dt / sim_data.sim_dt) != 0:
            return
        metrics_results = {}
        for metric_name, metric_obj in zip(self.info['metric'], self.metrics):
            val = metric_obj(sim_data, goal_data)
            if metric_name not in ['visualization']:
                metrics_results[metric_name] = val
        self.goals[self.goal_idx].update_metrics(metrics_results)

    def save_results(self):
        """ Save the results to a yaml file. """
        metrics = defaultdict(lambda: defaultdict(list))
        for goal in self.results:
            for metric_name, quantiles in self.results[goal].items():
                for quantile, val in quantiles.items():
                    metrics[metric_name][quantile].append(val)
        self.results['summary'] = {'quality_score': {}, 'terrain_quality_score': {}}
        for metric_name, quantiles in metrics.items():
            if metric_name not in self.results['summary']:
                self.results['summary'][metric_name] = {}
            for quantile, vals in quantiles.items():
                mean = float(np.mean(vals))
                std = float(np.std(vals))
                self.results['summary'][metric_name][quantile] = f"{mean:.4f} ± {std:.4f}"
                if metric_name == 'quality_score':
                    tqs = mean
                    if self.cfg.assets.terrain_name in SEARCH_LEVELS_TERRAINS:
                        tqs = 0.09 * (self.cfg.assets.terrain_level - 1) + 0.19 * mean
                    self.results['summary']['terrain_quality_score'][quantile] = f"{tqs:.4f} ± {std:.4f}"

        save_path = Path(logger.log_dir) / "results.yaml"
        self.results["terrain_name"] = self.cfg.assets.terrain_name
        self.results["terrain_level"] = self.cfg.assets.terrain_level

        with open(save_path, 'w', encoding='utf-8') as file:
            yaml_str = yaml.dump(self.results, allow_unicode=True, sort_keys=False)
            file.write(yaml_str)
        logger.info(
            f"""\n{'='*20} Goals and Metrics results {'='*20}\n"""
            f"""{yaml_str}"""
            f"""{'='*68}"""
        )
        logger.info(f"Saved metric results to {save_path}")
