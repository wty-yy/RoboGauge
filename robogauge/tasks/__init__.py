from robogauge.utils.task_register import task_register
from robogauge.tasks.simulator.mujoco_config import MujocoConfig
from robogauge.tasks.robots import RobotConfig, Go2Config, Go2MoEConfig, Go2TerrainConfig, Go2MoETerrainConfig
from robogauge.tasks.pipeline import BasePipeline
from robogauge.tasks.gauge import BaseGaugeConfig

from robogauge.tasks.custom.go2 import *

# Register tasks: Task name format '<robot_model>.<terrain>'
task_register.register('base', BasePipeline, MujocoConfig, BaseGaugeConfig, RobotConfig)

# Go2 MLP
task_register.register('go2.flat', BasePipeline, MujocoConfig, Go2FlatGaugeConfig, Go2Config)
task_register.register('go2.slope', BasePipeline, MujocoConfig, Go2SlopeGaugeConfig, Go2TerrainConfig)
task_register.register('go2.wave', BasePipeline, MujocoConfig, Go2WaveGaugeConfig, Go2TerrainConfig)
task_register.register('go2.stairs_up', BasePipeline, MujocoConfig, Go2StairsUpGaugeConfig, Go2TerrainConfig)
task_register.register('go2.stairs_down', BasePipeline, MujocoConfig, Go2StairsDownGaugeConfig, Go2TerrainConfig)

# Go2 MoE
task_register.register('go2_moe.flat', BasePipeline, MujocoConfig, Go2FlatGaugeConfig, Go2MoEConfig)
task_register.register('go2_moe.slope', BasePipeline, MujocoConfig, Go2SlopeGaugeConfig, Go2MoETerrainConfig)
task_register.register('go2_moe.wave', BasePipeline, MujocoConfig, Go2WaveGaugeConfig, Go2MoETerrainConfig)
task_register.register('go2_moe.stairs_up', BasePipeline, MujocoConfig, Go2StairsUpGaugeConfig, Go2MoETerrainConfig)
task_register.register('go2_moe.stairs_down', BasePipeline, MujocoConfig, Go2StairsDownGaugeConfig, Go2MoETerrainConfig)
