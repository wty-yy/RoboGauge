"""Go2 Lab policy adapter for pose-command observations."""

import numpy as np

from robogauge.tasks.robots.go2.go2 import Go2


def _quat_wxyz_to_rotation_matrix(quat_wxyz: np.ndarray) -> np.ndarray:
    """Convert one MuJoCo ``[w, x, y, z]`` quaternion to a rotation matrix."""
    quat = np.asarray(quat_wxyz, dtype=np.float64)
    if quat.shape != (4,):
        raise ValueError(f"base_quat_wxyz must have shape (4,), got {quat.shape}.")

    quat_norm = np.linalg.norm(quat)
    if not np.isfinite(quat_norm) or quat_norm <= 1.0e-12:
        raise ValueError("base_quat_wxyz must be a finite, non-zero quaternion.")

    w, x, y, z = quat / quat_norm
    return np.array(
        [
            [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)],
            [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)],
            [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)],
        ],
        dtype=np.float64,
    )


def body_twist_to_yaw_only(
    velocity_command_b: np.ndarray,
    base_quat_wxyz: np.ndarray,
) -> np.ndarray:
    """Project a full body-frame planar twist into the yaw-only base frame."""
    velocity = np.asarray(velocity_command_b, dtype=np.float64)
    if velocity.shape != (3,):
        raise ValueError(f"velocity_command_b must have shape (3,), got {velocity.shape}.")

    rotation_wb = _quat_wxyz_to_rotation_matrix(base_quat_wxyz)
    world_linear = rotation_wb @ np.array([velocity[0], velocity[1], 0.0])
    heading = np.arctan2(rotation_wb[1, 0], rotation_wb[0, 0])
    cos_heading = np.cos(heading)
    sin_heading = np.sin(heading)

    world_angular = rotation_wb @ np.array([0.0, 0.0, velocity[2]])
    return np.array(
        [
            cos_heading * world_linear[0] + sin_heading * world_linear[1],
            -sin_heading * world_linear[0] + cos_heading * world_linear[1],
            world_angular[2],
        ],
        dtype=np.float32,
    )


def velocity_to_pose_command(
    velocity_command_yaw_b: np.ndarray,
    horizon_s: float,
    small_angle_threshold: float,
) -> np.ndarray:
    """Integrate a constant yaw-only planar twist into a local SE(2) pose increment."""
    if horizon_s <= 0.0:
        raise ValueError("horizon_s must be positive.")
    if small_angle_threshold <= 0.0:
        raise ValueError("small_angle_threshold must be positive.")

    velocity = np.asarray(velocity_command_yaw_b, dtype=np.float64)
    if velocity.shape != (3,):
        raise ValueError(f"velocity_command_yaw_b must have shape (3,), got {velocity.shape}.")

    theta = velocity[2] * horizon_s
    if abs(theta) <= small_angle_threshold:
        theta_squared = theta * theta
        coefficient_a = 1.0 - theta_squared / 6.0
        coefficient_b = theta / 2.0 - theta * theta_squared / 24.0
    else:
        coefficient_a = np.sin(theta) / theta
        coefficient_b = 2.0 * np.sin(theta / 2.0) ** 2 / theta

    velocity_x, velocity_y = velocity[:2]
    return np.array(
        [
            horizon_s * (coefficient_a * velocity_x - coefficient_b * velocity_y),
            horizon_s * (coefficient_b * velocity_x + coefficient_a * velocity_y),
            theta,
        ],
        dtype=np.float32,
    )


class Go2LabPose(Go2):
    """Run a Go2 Lab pose-command policy from RoboGauge velocity goals."""

    def transform_velocity_command(
        self,
        velocity_command: np.ndarray,
        base_quat_wxyz: np.ndarray,
    ) -> np.ndarray:
        yaw_only_velocity = body_twist_to_yaw_only(velocity_command, base_quat_wxyz)
        return velocity_to_pose_command(
            yaw_only_velocity,
            horizon_s=self.cfg.control.command_horizon_s,
            small_angle_threshold=self.cfg.control.small_angle_threshold,
        )
