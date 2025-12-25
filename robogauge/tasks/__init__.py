from robogauge.utils.task_register import task_register
from robogauge.tasks.simulator.mujoco_config import MujocoConfig
from robogauge.tasks.robots import RobotConfig, Go2Config, Go2MoEConfig
from robogauge.tasks.pipeline import BasePipeline
from robogauge.tasks.gauge import BaseGaugeConfig

from robogauge.tasks.custom.go2 import *

task_register.register('base', BasePipeline, MujocoConfig, BaseGaugeConfig, RobotConfig)
task_register.register('go2_flat', BasePipeline, MujocoConfig, Go2FlatGaugeConfig, Go2Config)
task_register.register('go2_moe_flat', BasePipeline, MujocoConfig, Go2FlatGaugeConfig, Go2MoEConfig)
task_register.register('go2_slope', BasePipeline, Go2SlopeMujocoConfig, Go2SlopeGaugeConfig, Go2Config)
task_register.register('go2_moe_slope', BasePipeline, Go2SlopeMujocoConfig, Go2SlopeGaugeConfig, Go2MoEConfig)
task_register.register('go2_wave', BasePipeline, MujocoConfig, Go2WaveGaugeConfig, Go2Config)
task_register.register('go2_moe_wave', BasePipeline, MujocoConfig, Go2WaveGaugeConfig, Go2MoEConfig)
task_register.register('go2_stairs_up', BasePipeline, MujocoConfig, Go2StairsUpGaugeConfig, Go2Config)
task_register.register('go2_moe_stairs_up', BasePipeline, MujocoConfig, Go2StairsUpGaugeConfig, Go2MoEConfig)
task_register.register('go2_stairs_down', BasePipeline, MujocoConfig, Go2StairsDownGaugeConfig, Go2Config)
task_register.register('go2_moe_stairs_down', BasePipeline, MujocoConfig, Go2StairsDownGaugeConfig, Go2MoEConfig)