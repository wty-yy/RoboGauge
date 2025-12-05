from robogauge.tasks.robots import RobotConfig
from robogauge.tasks.simulator.sim_data import SimData
from robogauge.tasks.gauge.metrics.base_metric import BaseMetric

from robogauge.utils.logger import logger

class VisualizationMetric(BaseMetric):
    """ Metric to visualize various robot states in the simulator. """
    name = 'visualization_metric'

    def __init__(self,
        robot_cfg: RobotConfig,
        dof_force: bool = False,
        dof_pos: bool = False,
        **kwargs
    ):
        super().__init__(robot_cfg)
        self.dof_force = dof_force
        self.dof_pos = dof_pos

    def __call__(self, sim_data: SimData) -> float:
        for i in range(len(sim_data.proprio.joint.force)):
            name = sim_data.proprio.joint.names[i]
            if self.dof_force:
                force = sim_data.proprio.joint.force[i]
                logger.log(force, f'dof_force/{name}', step=sim_data.n_step)
            if self.dof_pos:
                pos = sim_data.proprio.joint.pos[i]
                logger.log(pos, f'dof_pos/{name}', step=sim_data.n_step)
        return 0.0
