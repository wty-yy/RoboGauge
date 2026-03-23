import numpy as np
from dataclasses import dataclass

@dataclass
class JointState:
    pos: np.ndarray     # [rad] shape (n_dof,)
    vel: np.ndarray     # [rad/s] shape (n_dof,)
    torque: np.ndarray  # [N*m] shape (n_dof,)
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
class RigidBodyDynamics:
    names: list                   # list of rigid body names
    mass: np.ndarray              # [kg] shape (n_body,)
    com_pos: np.ndarray           # [m] world frame, shape (n_body, 3)
    com_lin_vel: np.ndarray       # [m/s] world frame, shape (n_body, 3)
    com_lin_acc: np.ndarray       # [m/s^2] world frame, shape (n_body, 3)
    ang_vel: np.ndarray           # [rad/s] world frame, shape (n_body, 3)
    ang_acc: np.ndarray           # [rad/s^2] world frame, shape (n_body, 3)
    inertia_world: np.ndarray     # [kg*m^2] world frame, shape (n_body, 3, 3)

@dataclass
class GroundContactState:
    positions: np.ndarray         # [m] world frame, shape (n_contact, 3)
    distances: np.ndarray         # [m] shape (n_contact,)
    normal_forces: np.ndarray     # [N] contact-frame normal force magnitude, shape (n_contact,)
    tangent_forces: np.ndarray    # [N] contact-frame tangential force magnitude, shape (n_contact,)
    friction_coefficients: np.ndarray  # [-] translational friction coefficient, shape (n_contact,)
    robot_geom_names: list        # list of robot geom names
    other_geom_names: list        # list of non-robot geom names
    robot_body_names: list        # list of robot body names
    other_body_names: list        # list of non-robot body names

@dataclass
class DynamicsState:
    gravity: np.ndarray
    rigid_bodies: RigidBodyDynamics
    contacts: GroundContactState
    default_diagonal_foot_distance: float

@dataclass
class VisualState:
    zmp_world_pos: np.ndarray = None
    zmp_draw_enabled: bool = False
    zmp_draw_size: float = 0.03
    zmp_draw_height_offset: float = 0.02
    zmp_draw_rgba: np.ndarray = None

@dataclass
class SimData:
    n_step: int
    sim_dt: float
    sim_time: float
    proprio: RobotProprioception
    dynamics: DynamicsState
    visual: VisualState
