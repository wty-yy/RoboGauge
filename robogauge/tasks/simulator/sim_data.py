import numpy as np
from dataclasses import dataclass

@dataclass
class JointState:
    pos: np.ndarray     # [rad] shape (n_dof,)
    vel: np.ndarray     # [rad/s] shape (n_dof,)
    torque: np.ndarray   # [N*m] shape (n_dof,)
    limits: np.ndarray  # [rad] shape (n_dof, 2), lower and upper limits
    names: list         # list of joint names

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
    sim_time: float
    proprio: RobotProprioception
