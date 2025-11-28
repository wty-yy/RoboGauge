import numpy as np
from dataclasses import dataclass

@dataclass
class JointState:
    pos: np.ndarray
    vel: np.ndarray
    force: np.ndarray

@dataclass
class BaseState:
    pos: np.ndarray
    quat: np.ndarray
    lin_vel: np.ndarray
    ang_vel: np.ndarray

@dataclass
class IMUState:
    pos: np.ndarray
    quat: np.ndarray
    acc: np.ndarray
    lin_vel: np.ndarray
    ang_vel: np.ndarray

@dataclass
class RobotProprioception:
    joint: JointState
    base: BaseState
    imu: IMUState

@dataclass
class SimData:
    n_step: int
    sim_dt: float
    proprio: RobotProprioception
