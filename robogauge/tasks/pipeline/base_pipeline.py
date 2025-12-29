# -*- coding: utf-8 -*-
'''
@File    : base_pipeline.py
@Time    : 2025/11/27 15:53:26
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Base Pipeline for Robogauge
'''
import yaml
import random
import traceback
import numpy as np
from pathlib import Path
from copy import deepcopy

from robogauge.utils.logger import logger
from robogauge.tasks.simulator import MujocoSimulator, MujocoConfig, SimData
from robogauge.tasks.robots import (
    BaseRobot, RobotConfig, Go2Config, Go2, Go2MoEConfig, Go2MoE
)
from robogauge.tasks.gauge import BaseGauge, BaseGaugeConfig
from robogauge.tasks.gauge.goal_data import GoalData, VelocityGoal, PositionGoal
from robogauge.utils.helpers import class_to_dict

class BasePipeline:
    def __init__(self, 
        run_name: str,
        simulator_cfg: MujocoConfig,
        robot_cfg: RobotConfig,
        gauge_cfg: BaseGaugeConfig
    ):
        self.run_name = run_name
        self.sim_cfg = simulator_cfg
        self.robot_cfg = robot_cfg
        self.gauge_cfg = gauge_cfg

        self.sim: MujocoSimulator = eval(simulator_cfg.simulator_class)(simulator_cfg)
        self.robot: BaseRobot = eval(robot_cfg.robot_class)(robot_cfg)
        self.gauge: BaseGauge = eval(gauge_cfg.gauge_class)(gauge_cfg, robot_cfg)

        self.first_reset = True
        self.last_reset_time = 0.0
    
        # save configs
        cfg = {}
        for name in ['sim_cfg', 'robot_cfg', 'gauge_cfg']:
            obj = getattr(self, name)
            obj_dict = class_to_dict(obj)
            cfg.update({name: obj_dict})
        with open(Path(logger.log_dir) / "configs.yaml", 'w') as file:
            yaml.dump(cfg, file)
    
    def load(self):
        self.sim.load(
            self.gauge_cfg.assets.terrain_xmls,
            self.robot_cfg.assets.robot_xml,
            self.gauge_cfg.assets.terrain_spawn_pos,
            self.robot_cfg.control.default_dof_pos,
            self.gauge_cfg.backward,
        )

    def run(self):
        logger.info(f"🚀 Starting single run: {self.run_name}")
        self.load()
        sim_data = self.sim.step()
        frame_skip = int(self.robot_cfg.control.control_dt / self.sim_cfg.physics.simulation_dt)
        assert frame_skip * self.sim_cfg.physics.simulation_dt == self.robot_cfg.control.control_dt, \
            "Control dt must be multiple of simulation dt."
        logger.info(f"Sim FPS: {1.0 / self.sim_cfg.physics.simulation_dt:.2f}, Control FPS: {1.0 / self.robot_cfg.control.control_dt:.2f}, Frame Skip: {frame_skip:d}")
        logger.info("Running pipeline...")
        warning, error = None, None
        while not self.gauge.is_done():
            try:
                if self.first_reset:  # wait for robot to be still
                    goal_data = GoalData(
                        goal_type=self.robot_cfg.control.support_goal,
                        velocity_goal=VelocityGoal(),  # zero velocity
                        position_goal=PositionGoal(),  # current position
                    )
                    if (
                        (np.linalg.norm(sim_data.proprio.base.lin_vel) < 0.05 and sim_data.sim_time - self.last_reset_time > 0.1) or  # robot is still
                        (sim_data.sim_time - self.last_reset_time) > 3.0  # wait max 3s
                    ):
                        self.first_reset = False
                else:
                    goal_data = self.gauge.get_goal(sim_data)

                if goal_data is None:  # Change goal
                    sim_data = self.reset_sim_and_robot(sim_data)
                    continue

                if goal_data.visualization_pos is not None:
                    self.sim.set_target_pos(goal_data.visualization_pos)
                else:
                    self.sim.set_target_pos(None)

                obs = self.robot.build_observation(self.add_noise(sim_data), goal_data)
                action, p_gains, d_gains, control_type = self.robot.get_action(obs)

                if self.sim_cfg.domain_rand.action_delay:
                    actions_start_decimation = random.randint(0, frame_skip)
                else:
                    self.sim.setup_action(action, p_gains, d_gains, control_type)
                for i in range(frame_skip):
                    if self.sim_cfg.domain_rand.action_delay and i == actions_start_decimation:
                        self.sim.setup_action(action, p_gains, d_gains, control_type)
                    sim_data = self.sim.step()
                    self.gauge.update_metrics(sim_data, goal_data)
                if self.gauge.is_reset(sim_data):
                    sim_data = self.reset_sim_and_robot(sim_data)
            except Exception as e:
                if str(e).startswith("[Penetration Error]"):
                    warning = e
                    logger.warning(f"⚠️ Penetration detected! Reset current goal and continue..., error: {e}")
                    self.gauge.reset_current_goal()
                    logger.info("⏩ Pipeline recovered from penetration and continued current goal 🎯.")
                else:
                    error = e
                    logger.error(f"❌ Goal '{self.gauge.goal_str}' failed with error: {e},\n{traceback.format_exc()}")
                    self.gauge.switch_to_next_goal()  # skip to next goal
                    logger.info("⏩ Pipeline recovered from error and continued next goal 🎯.")
                sim_data = self.reset_sim_and_robot(sim_data)

        self.sim.close_viewer()
        self.sim.close_video_writer()
        logger.info("✅ Pipeline execution finished.")
        logger.info(f"📁 Logging saved at: {logger.log_dir}")

        return self.gauge.results, warning, error
    
    def reset_sim_and_robot(self, sim_data: SimData):
        self.sim.reset()
        self.last_reset_time = sim_data.sim_time
        self.first_reset = True
        sim_data = self.sim.step()
        self.robot.reset()
        return sim_data

    def add_noise(self, sim_data: SimData):
        sim_data = deepcopy(sim_data)
        noise_cfg = self.sim_cfg.noise
        if not noise_cfg.enabled:
            return sim_data
        proprio = sim_data.proprio
        def add_uniform_noise(data, noise_level):
            for i in range(len(data)):
                noise = random.uniform(-noise_level, noise_level)
                data[i] += noise
        add_uniform_noise(proprio.joint.pos, noise_cfg.joint_pos)
        add_uniform_noise(proprio.joint.vel, noise_cfg.joint_vel)
        add_uniform_noise(proprio.base.lin_vel, noise_cfg.lin_vel)
        add_uniform_noise(proprio.base.ang_vel, noise_cfg.ang_vel)
        add_uniform_noise(proprio.imu.lin_vel, noise_cfg.lin_vel)
        add_uniform_noise(proprio.imu.ang_vel, noise_cfg.ang_vel)
        return sim_data
