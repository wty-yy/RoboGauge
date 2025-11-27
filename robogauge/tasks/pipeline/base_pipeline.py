# -*- coding: utf-8 -*-
'''
@File    : base_pipeline.py
@Time    : 2025/11/27 15:53:26
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Base Pipeline for Robogauge
'''
import traceback
from robogauge.utils.logger import logger
from robogauge.tasks.simulator import MujocoSimulator, MujocoConfig
from robogauge.tasks.robots import BaseRobot, RobotConfig
from robogauge.tasks.gauge import BaseGauge, BaseGaugeConfig

class BasePipeline:
    def __init__(self, 
        simulator_cfg: MujocoConfig,
        robot_cfg: RobotConfig,
        gauge_cfg: BaseGaugeConfig
    ):
        self.simulator_cfg = simulator_cfg
        self.robot_cfg = robot_cfg
        self.gauge_cfg = gauge_cfg

        self.sim: MujocoSimulator = eval(simulator_cfg.simulator_class)(simulator_cfg)
        self.robot: BaseRobot = eval(robot_cfg.robot_class)(robot_cfg)
        self.gauge: BaseGauge = eval(gauge_cfg.gauge_class)(gauge_cfg)
    
    def load(self):
        self.sim.load(
            self.gauge_cfg.assets.terrain_xml,
            self.robot_cfg.assets.robot_xml,
            self.gauge_cfg.assets.terrain_spawn_xy,
            self.robot_cfg.assets.robot_spawn_height
        )
    
    def run(self):
        try:
            self.load()
            info = self.sim.step()
            frame_skip = int(self.robot_cfg.control.control_dt / self.simulator_cfg.physics.simulation_dt)
            logger.info(f"Sim FPS: {1.0 / self.simulator_cfg.physics.simulation_dt:.2f}, Control FPS: {1.0 / self.robot_cfg.control.control_dt:.2f}, Frame Skip: {frame_skip:d}")
            logger.info("Starting pipeline...")
            while not self.gauge.is_done():
                goal = self.gauge.get_goal()
                obs = self.robot.build_observation(info, goal)
                action = self.robot.get_action(obs)
                for _ in range(frame_skip):
                    self.sim.apply_action(action)
                    info = self.sim.step()
                    self.gauge.update_metrics(info)
                if self.gauge.is_reset():
                    self.sim.reset()
                    info = self.sim.step()
        finally:
            self.sim.close_viewer()
            logger.info("Pipeline execution finished.")
