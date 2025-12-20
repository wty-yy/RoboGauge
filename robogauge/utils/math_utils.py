import numpy as np

def get_projected_gravity(quat):
    """ Compute world frame gravity (0, 0, -1) projected into robot base frame.
    Args:
        quat: (4,) quaternion (w, x, y, z) from robot base to world frame
    Returns:
        projected_gravity: (3,) projected gravity vector in robot base frame
    """
    qw, qx, qy, qz = quat

    gravity_orientation = np.zeros(3)

    gravity_orientation[0] = 2 * (-qz * qx + qw * qy)
    gravity_orientation[1] = -2 * (qz * qy + qw * qx)
    gravity_orientation[2] = 1 - 2 * (qw * qw + qz * qz)

    return gravity_orientation

def quat_rotate_inverse(q, v):
    q = np.array(q, np.float32)
    v = np.array(v, np.float32)
    q_w = q[0]
    q_vec = q[1:]
    a = v * (2.0 * q_w ** 2 - 1.0)
    b = np.cross(q_vec, v) * q_w * 2.0
    c = q_vec * np.dot(q_vec, v) * 2.0
    return a - b + c
