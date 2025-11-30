from robogauge.tasks.robots import RobotConfig
from robogauge.tasks.simulator.sim_data import SimData

from robogauge.utils.logger import logger

def example_metric(
    sim_data: SimData,
    robot_cfg: RobotConfig,
    **kwargs
) -> float:
    """ An example metric function. """
    value = 0.0
    # Compute some metric value based on sim_data and robot_cfg
    logger.log(value, 'example_metric', step=sim_data.n_step)
    return value

def dof_limits_metric(
    sim_data: SimData,
    robot_cfg: RobotConfig,
    soft_dof_limit_ratio: float = 0.9,
    **kwargs
) -> float:
    """ Metric to log DOF limit violations. """
    mean_value = 0.0
    for i in range(len(sim_data.proprio.joint.limits)):
        lower_limit = sim_data.proprio.joint.limits[i, 0]
        upper_limit = sim_data.proprio.joint.limits[i, 1]
        dof_range = upper_limit - lower_limit
        soft_lower_limit = lower_limit + soft_dof_limit_ratio * dof_range
        soft_upper_limit = upper_limit - soft_dof_limit_ratio * dof_range

        pos = sim_data.proprio.joint.pos[i]
        value = 0
        if pos < soft_lower_limit:
            value = soft_lower_limit - pos
        elif pos > soft_upper_limit:
            value = pos - soft_upper_limit
        value /= dof_range  # Normalize by DOF range
        logger.log(value, f'dof_limits/{i}', step=sim_data.n_step)
        mean_value += value
    mean_value /= len(sim_data.proprio.joint.limits)
    logger.log(mean_value, f'dof_limits/mean', step=sim_data.n_step)
    return mean_value
