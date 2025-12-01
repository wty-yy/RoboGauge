from robogauge.utils.task_register import task_register
from robogauge.tasks.simulator.mujoco_config import MujocoConfig
from robogauge.tasks.robots import RobotConfig, Go2Config
from robogauge.tasks.pipeline import BasePipeline
from robogauge.tasks.gauge import BaseGaugeConfig

from robogauge.tasks.custom.go2_flat_task import Go2FlatGaugeConfig

task_register.register('base', BasePipeline, MujocoConfig, BaseGaugeConfig, RobotConfig)
task_register.register('go2_flat', BasePipeline, MujocoConfig, Go2FlatGaugeConfig, Go2Config)
