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

class BaseGauge:
    def __init__(self, cfg: BaseGaugeConfig):
        self.cfg = cfg
    
    def is_reset(self) -> bool:
        return False
    
    def is_done(self) -> bool:
        return False
    
    def get_goal(self) -> dict:
        goal = {}
        return goal
    
    def update_metrics(self, sim_info: dict):
        ...
    