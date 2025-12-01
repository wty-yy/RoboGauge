import numpy as np

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
    dof_names: list = None,
    **kwargs
) -> float:
    """ Metric to log DOF limit violations. """
    values = []
    for i in range(len(sim_data.proprio.joint.limits)):
        lower_limit = sim_data.proprio.joint.limits[i, 0]
        upper_limit = sim_data.proprio.joint.limits[i, 1]
        dof_range = upper_limit - lower_limit
        soft_lower_limit = lower_limit + (1 - soft_dof_limit_ratio) * dof_range
        soft_upper_limit = upper_limit - (1 - soft_dof_limit_ratio) * dof_range

        pos = sim_data.proprio.joint.pos[i]
        dof_name = sim_data.proprio.joint.names[i]
        value = 0
        if pos < soft_lower_limit:
            value = soft_lower_limit - pos
        elif pos > soft_upper_limit:
            value = pos - soft_upper_limit
        value /= dof_range  # Normalize by DOF range
        logger.log(value, f'dof_limits/{dof_name}', step=sim_data.n_step)
        if dof_names is not None:
            for use_name in dof_names:
                if use_name in dof_name:
                    values.append(value)
        else:
            values.append(value)
    rms_value = 1 - np.sqrt(np.mean(np.square(values)))
    logger.log(1 - rms_value, f'dof_limits/rms', step=sim_data.n_step)
    return rms_value

def visualization_metric(
    sim_data: SimData,
    robot_cfg: RobotConfig,
    dof_force: bool = False,
    dof_pos: bool = False,
    **kwargs,
):
    """ Metric to visualize various robot states in the simulator. """
    for i in range(len(sim_data.proprio.joint.force)):
        name = sim_data.proprio.joint.names[i]
        if dof_force:
            force = sim_data.proprio.joint.force[i]
            logger.log(force, f'dof_force/{name}', step=sim_data.n_step)
        if dof_pos:
            pos = sim_data.proprio.joint.pos[i]
            logger.log(pos, f'dof_pos/{name}', step=sim_data.n_step)
    return 0.0
