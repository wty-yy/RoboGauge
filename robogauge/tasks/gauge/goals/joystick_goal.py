# -*- coding: utf-8 -*-
'''
@File    : joystick_goal.py
@Time    : 2026/02/04 10:47:47
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Joystick Goals Implementation
'''
import pygame
from typing import Literal
from robogauge.utils.helpers import class_to_dict
from robogauge.tasks.robots import RobotConfig
from robogauge.tasks.gauge.goals import BaseGoal
from robogauge.tasks.gauge.goal_data import GoalData, VelocityGoal
from robogauge.tasks.simulator.sim_data import SimData

class JoystickGoal(BaseGoal):
    name = "joystick_goal"

    def __init__(self,
            max_velocity: RobotConfig.commands,
            goal_type: Literal['velocity', 'position'],
            dead_zone=0.1,
            **kwargs
        ):
        super().__init__()
        self.goal_type = goal_type
        self.dead_zone = dead_zone
        self.max_velocity = class_to_dict(max_velocity)
        if self.goal_type != 'velocity':
            raise NotImplementedError("Only 'velocity' goal type is implemented for JoystickGoal.")
        
        pygame.init()
        while not pygame.joystick.get_count():
            print("Waiting for joystick connection...")
            pygame.time.wait(1000)
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        print(f"Joystick '{self.joystick.get_name()}' initialized.")

    def is_reset(self, sim_data: SimData) -> bool:
        return False  # never reset

    def pre_get_goal(self, sim_data: SimData) -> bool:
        return False  # loop forever
    
    def joystick2cmd(self, joystick_value, key_name):
        assert key_name in self.max_velocity, f"Key '{key_name}' not in max_velocity config."
        mn, mx = self.max_velocity[key_name]
        return (joystick_value + 1) / 2 * (mx - mn) + mn
    
    def get_goal(self, sim_data: SimData) -> GoalData:
        pygame.event.pump()
        lx = -self.joystick.get_axis(0)  # Left stick X-axis
        ly = -self.joystick.get_axis(1)  # Left stick Y-axis
        rx = -self.joystick.get_axis(3)  # Right stick X-axis
        if abs(lx) < self.dead_zone: lx = 0
        if abs(ly) < self.dead_zone: ly = 0
        if abs(rx) < self.dead_zone: rx = 0
        cmd_x = self.joystick2cmd(ly, 'lin_vel_x')
        cmd_y = self.joystick2cmd(lx, 'lin_vel_y')
        cmd_yaw = self.joystick2cmd(rx, 'ang_vel_yaw')
        print(f"RAW CMD: {lx:.2f}, {ly:.2f}, {rx:.2f} => CMD: {cmd_x:.2f}, {cmd_y:.2f}, {cmd_yaw:.2f}", end='\r')
        return GoalData(
            goal_type='velocity',
            velocity_goal=VelocityGoal(
                lin_vel_x=cmd_x,
                lin_vel_y=cmd_y,
                ang_vel_yaw=cmd_yaw,
            )
        )
