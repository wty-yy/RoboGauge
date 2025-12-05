from robogauge.utils.logger import logger
from robogauge.tasks.robots import RobotConfig
from robogauge.tasks.simulator.sim_data import SimData

class BaseMetric:
    """ Base class for all metric functions. """
    name = 'base_metric'

    def __init__(self, robot_cfg: RobotConfig, **kwargs):
        self.robot_cfg = robot_cfg

    def __call__(self, sim_data: SimData) -> float:
        value = 0.0
        logger.log(value, self.name, step=sim_data.n_step)
        return value
