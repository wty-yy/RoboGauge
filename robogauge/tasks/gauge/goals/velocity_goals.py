# -*- coding: utf-8 -*-
'''
@File    : velocity_goals.py
@Time    : 2025/11/30 21:44:13
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Velocity Goals Implementation
'''
import numpy as np
from copy import deepcopy
from typing import Optional, List

from robogauge.tasks.gauge.goals import BaseGoal
from robogauge.tasks.robots import RobotConfig
from robogauge.tasks.simulator.sim_data import SimData
from robogauge.tasks.gauge.goal_data import GoalData, VelocityGoal
from robogauge.utils.helpers import class_to_dict
from robogauge.utils.logger import logger
from robogauge.utils.math_utils import quat_rotate_inverse

PI = np.pi

class BaseVelocityGoal(BaseGoal):
    name = "base_velocity_goal"

    def __init__(self, control_dt: float, cmd_duration: float = 5, **kwargs):
        """
        Args:
            control_dt (float): Control timestep.
            cmd_duration (float): Duration for each sub-task (e.g. different velocity commands).
        """
        super().__init__()
        self.control_dt = control_dt
        self.cmd_duration = cmd_duration
        self.goals = []
        self.goal_runtime = 0.0
        self.first_goal_after_reset = True
        self.last_reset_time = -1
    
    def reset_goal(self):
        self.goal_runtime = 0.0
        self.first_goal_after_reset = True
        self.last_reset_time = -1

    def is_reset(self, sim_data: SimData) -> bool:
        if self.last_reset_time == -1:
            self.last_reset_time = sim_data.sim_time
        if sim_data.sim_time - self.last_reset_time >= self.cmd_duration:
            self.last_reset_time = sim_data.sim_time
            self.first_goal_after_reset = True
            return True
        return False
    
    def pre_get_goal(self, sim_data: SimData) -> bool:
        """ Run before getting the goal
        Returns:
            bool: whether the goal sequence is done
        """
        self.update_runtime_count(sim_data)
        return self.count >= self.total

    def update_runtime_count(self, sim_data: SimData):
        """
        Update the goal runtime and count based on the simulation time.
        """
        if self.first_goal_after_reset:
            self.last_reset_time = sim_data.sim_time  # update last reset time (stance after reset)
            self.first_goal_after_reset = False
        self.goal_runtime += self.control_dt
        self.count = int(self.goal_runtime / self.cmd_duration)

class MaxVelocityGoal(BaseVelocityGoal):
    name = "max_velocity"

    """ Goal class for maximizing velocity commands, maximum 6 sub-tasks. """
    def __init__(self,
        control_dt: float,
        max_velocity: RobotConfig.commands,
        move_duration: float = 5,
        end_stance: bool = True,
        stance_duration: float = 2.0,
        **kwargs
    ):
        cmd_duration = move_duration + (stance_duration if end_stance else 0)
        super().__init__(control_dt=control_dt, cmd_duration=cmd_duration)
        self.move_duration = move_duration
        self.end_stance = end_stance
        self.stance_duration = stance_duration

        kwargs.pop('enabled', None)
        if kwargs:
            logger.warning(f"Unused kwargs in MaxVelocityGoal: {kwargs}")
        self.max_velocity = class_to_dict(max_velocity)

        self.goals = []
        for key in ['lin_vel_x', 'lin_vel_y', 'lin_vel_z', 'ang_vel_roll', 'ang_vel_pitch', 'ang_vel_yaw']:
            if self.max_velocity.get(key) is None: continue
            for value in self.max_velocity[key]:
                if value != 0:
                    self.goals.append(VelocityGoal(**{key: value}))
        
        # self.goals = self.goals[:2]
        self.count = 0
        self.total = len(self.goals)
        if len(self.goals) == 0:
            logger.warning("MaxVelocityGoal initialized with no valid velocity commands.")
            return
        self.sub_name = str(self.goals[0])

    def get_goal(self, sim_data: SimData) -> Optional[GoalData]:
        self.current_goal = self.goals[self.count]
        if self.end_stance and self.goal_runtime - self.count * self.cmd_duration >= self.move_duration:
            self.current_goal = VelocityGoal()  # zero velocity
        self.sub_name = str(self.current_goal)
        return GoalData(
            goal_type='velocity',
            velocity_goal=self.current_goal
        )

class DiagonalVelocityGoal(BaseVelocityGoal):
    name = "diagonal_velocity"

    def __init__(self,
        control_dt: float,
        max_velocity: RobotConfig.commands,
        cmd_duration: float = 6,
        **kwargs
    ):
        """ Goal class for diagonal velocity changes, maximum 8 sub-tasks.
        Args:
            control_dt (float): Control timestep.
            max_velocity (RobotConfig.commands): Maximum velocity commands.
            cmd_duration (float, optional): Duration for a pair of diagonal commands.
        """
        super().__init__(control_dt=control_dt, cmd_duration=cmd_duration)
        kwargs.pop('enabled', None)
        if kwargs:
            logger.warning(f"Unused kwargs in DiagonalVelocityGoal: {kwargs}")

        self.goals = []
        lin_vel_x_vals = max_velocity.lin_vel_x + [0]
        lin_vel_y_vals = max_velocity.lin_vel_y + [0]

        for lx in lin_vel_x_vals:
            for ly in lin_vel_y_vals:
                if lx == 0 and ly == 0:
                    continue
                self.goals.append(VelocityGoal(lin_vel_x=lx, lin_vel_y=ly))
        
        # self.goals = self.goals[:2]
        self.count = 0
        self.total = len(self.goals)
        if len(self.goals) == 0:
            logger.warning("DiagonalVelocityGoal initialized with no valid diagonal velocity commands.")
            return
        self.sub_name = str(self.goals[0])

    def get_goal(self, sim_data: SimData) -> Optional[GoalData]:
        self.current_goal = self.goals[self.count]
        if self.goal_runtime - self.count * self.cmd_duration >= self.cmd_duration / 2:
            self.current_goal = self.current_goal.invert()
        self.sub_name = str(self.current_goal)
        return GoalData(
            goal_type='velocity',
            velocity_goal=self.current_goal
        )

class TargetPosVelocityGoal(BaseVelocityGoal):
    name = "target_pos_velocity"

    def __init__(self,
        control_dt: float,
        target_pos: List[float],
        lin_vel_x: float,
        lin_vel_y: float,
        ang_vel_yaw: float,
        max_cmd_duration: float,
        reach_threshold: float,
        **kwargs
    ):
        super().__init__(control_dt=control_dt, cmd_duration=max_cmd_duration)

        self.target_pos = target_pos
        self.lin_vel_x = lin_vel_x
        self.lin_vel_y = lin_vel_y
        self.ang_vel_yaw = ang_vel_yaw
        self.reach_threshold = reach_threshold

        kwargs.pop('enabled', None)
        if kwargs:
            logger.warning(f"Unused kwargs in TargetPosVelocity: {kwargs}")
        self.sub_name = None
        self.count = 0
        self.total = 1  # only one task
        self.done = False
        self.success = False
    
    def reset_goal(self):
        super().reset_goal()
        self.done = False
        self.success = False

    def get_goal(self, sim_data: SimData) -> Optional[GoalData]:
        self.update_runtime_count(sim_data)
        delta_pos, _, delta_ang = self.get_delta_info(sim_data)
        ang_vel_yaw = np.sign(delta_ang) * min(abs(delta_ang) * 2, self.ang_vel_yaw)
        self.current_goal = VelocityGoal(
            lin_vel_x=self.lin_vel_x if abs(delta_ang) < PI / 4 else 0.0,
            lin_vel_y=np.sign(delta_pos[1]) * min(abs(delta_pos[1]), self.lin_vel_y) if abs(delta_ang) >= PI / 4 else 0.0,
            ang_vel_yaw=ang_vel_yaw
        )
        return GoalData(
            goal_type='velocity',
            velocity_goal=self.current_goal,
            visualization_pos=self.target_pos
        )

    def is_reset(self, sim_data: SimData) -> bool:
        _, norm, _ = self.get_delta_info(sim_data)
        time_out = super().is_reset(sim_data)
        reached = norm < self.reach_threshold
        if time_out or reached:
            self.done = True
            if reached:
                self.success = True
            return True
        return False
    
    def pre_get_goal(self, sim_data: SimData) -> bool:
        """ Run before getting the goal
        Returns:
            bool: whether the goal is done
        """
        return self.count >= self.total or self.done
    
    def get_delta_info(self, sim_data: SimData) -> List[float]:
        current_pos = sim_data.proprio.base.pos
        delta_pos = [
            self.target_pos[0] - current_pos[0],
            self.target_pos[1] - current_pos[1],
            self.target_pos[2] - current_pos[2],
        ]
        delta_pos = quat_rotate_inverse(sim_data.proprio.base.quat, delta_pos)
        norm = np.linalg.norm(delta_pos[:2])
        delta_ang = np.arctan2(delta_pos[1], delta_pos[0])
        return delta_pos, norm, delta_ang
