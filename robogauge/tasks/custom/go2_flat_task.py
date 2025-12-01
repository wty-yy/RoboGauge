from robogauge.tasks.robots import Go2Config
from robogauge.tasks.gauge import FlatGaugeConfig

class Go2FlatGaugeConfig(FlatGaugeConfig):
    class metrics(FlatGaugeConfig.metrics):
        class dof_limits(FlatGaugeConfig.metrics.dof_limits):
            enabled = True
            soft_dof_limit_ratio = 0.7
            dof_names = ['hip', 'thigh']  # List of DOF names to monitor, None for all

    class goals(FlatGaugeConfig.goals):
        class max_velocity(FlatGaugeConfig.goals.max_velocity):
            enabled = True
            cmd_duration = 5.0
