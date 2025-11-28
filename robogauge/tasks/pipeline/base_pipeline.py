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
from robogauge.tasks.robots import BaseRobot, RobotConfig, Go2Config, Go2
from robogauge.tasks.gauge import BaseGauge, BaseGaugeConfig

class BasePipeline:
    def __init__(self, 
        run_name: str,
        simulator_cfg: MujocoConfig,
        robot_cfg: RobotConfig,
        gauge_cfg: BaseGaugeConfig
    ):
        self.run_name = run_name
        self.simulator_cfg = simulator_cfg
        self.robot_cfg = robot_cfg
        self.gauge_cfg = gauge_cfg

        self.sim: MujocoSimulator = eval(simulator_cfg.simulator_class)(simulator_cfg)
        self.robot: BaseRobot = eval(robot_cfg.robot_class)(robot_cfg)
        self.gauge: BaseGauge = eval(gauge_cfg.gauge_class)(gauge_cfg)
    
    def load(self):
        logger.create_tensorboard(self.run_name)
        self.sim.load(
            self.gauge_cfg.assets.terrain_xml,
            self.robot_cfg.assets.robot_xml,
            self.gauge_cfg.assets.terrain_spawn_xy,
            self.robot_cfg.assets.robot_spawn_height,
            self.robot_cfg.control.default_dof_pos
        )
    
    def run(self):
        try:
            self.load()
            sim_data = self.sim.step()
            frame_skip = int(self.robot_cfg.control.control_dt / self.simulator_cfg.physics.simulation_dt)
            logger.info(f"Sim FPS: {1.0 / self.simulator_cfg.physics.simulation_dt:.2f}, Control FPS: {1.0 / self.robot_cfg.control.control_dt:.2f}, Frame Skip: {frame_skip:d}")
            logger.info("Running pipeline...")
            while not self.gauge.is_done():
                goal = self.gauge.get_goal()
                obs = self.robot.build_observation(sim_data, goal)
                action, p_gains, d_gains, control_type = self.robot.get_action(obs)
                self.sim.setup_action(action, p_gains, d_gains, control_type)
                for _ in range(frame_skip):
                    sim_data = self.sim.step()
                    self.gauge.update_metrics(sim_data)
                if self.gauge.is_reset():
                    self.sim.reset()
                    sim_data = self.sim.step()
        finally:
            self.sim.close_viewer()
            logger.info("Pipeline execution finished.")
            logger.info(f"Logging saved at: {logger.log_dir}")
