from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Literal

@dataclass
class VelocityGoal:
    lin_vel: List[float]  # x, y, z [m/s], z is ignored for ground robots
    ang_vel: List[float]  # roll, pitch, yaw [rad/s], roll and pitch are ignored for ground robots

@dataclass
class PositionGoal:
    # relative to robot's current position
    target_pos: List[float]  # x, y, z [m], z is ignored for ground robots
    # reach target orientation
    target_quat: List[float]  # x, y, z, w quaternion
    tolerance: float  # [m] position tolerance to consider goal reached

@dataclass
class GoalData:
    goal_type: Literal['velocity', 'position']
    velocity_goal: Optional[VelocityGoal] = None
    position_goal: Optional[PositionGoal] = None
