from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Literal

@dataclass
class VelocityGoal:
    lin_vel_x: float = 0.0  # [m/s]
    lin_vel_y: float = 0.0  # [m/s]
    lin_vel_z: float = 0.0  # [m/s]
    ang_vel_roll: float = 0.0  # [rad/s]
    ang_vel_pitch: float = 0.0  # [rad/s]
    ang_vel_yaw: float = 0.0  # [rad/s]
    
    def __repr__(self):
        s = ""
        for field in self.__dataclass_fields__:
            if getattr(self, field) != 0.0:
                s += f"{field}={getattr(self, field):.1f}_"
        return s[:-1] if s else "stance"

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
