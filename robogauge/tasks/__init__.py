from robogauge.utils.task_register import task_register
from robogauge.tasks.simulator.mujoco_config import MujocoConfig
from robogauge.tasks.robots import RobotConfig, Go2Config
from robogauge.tasks.pipeline import BasePipeline
from robogauge.tasks.gauge import BaseGaugeConfig

task_register.register('base', BasePipeline, MujocoConfig, BaseGaugeConfig, RobotConfig)
task_register.register('go2', BasePipeline, MujocoConfig, BaseGaugeConfig, Go2Config)
