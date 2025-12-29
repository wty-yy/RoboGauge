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
task_register.register('go2.slope_fd', BasePipeline, MujocoConfig, Go2SlopeForwardGaugeConfig, Go2TerrainConfig)
task_register.register('go2.slope_bd', BasePipeline, MujocoConfig, Go2SlopeBackwardGaugeConfig, Go2TerrainConfig)
task_register.register('go2.wave', BasePipeline, MujocoConfig, Go2WaveGaugeConfig, Go2TerrainConfig)
task_register.register('go2.stairs_fd', BasePipeline, MujocoConfig, Go2StairsForwardGaugeConfig, Go2TerrainConfig)
task_register.register('go2.stairs_bd', BasePipeline, MujocoConfig, Go2StairsBackwardGaugeConfig, Go2TerrainConfig)
task_register.register('go2.obstacle', BasePipeline, MujocoConfig, Go2ObstacleGaugeConfig, Go2TerrainConfig)

# Go2 MoE
task_register.register('go2_moe.flat', BasePipeline, MujocoConfig, Go2FlatGaugeConfig, Go2MoEConfig)
task_register.register('go2_moe.slope_fd', BasePipeline, MujocoConfig, Go2SlopeForwardGaugeConfig, Go2MoETerrainConfig)
task_register.register('go2_moe.slope_bd', BasePipeline, MujocoConfig, Go2SlopeBackwardGaugeConfig, Go2MoETerrainConfig)
task_register.register('go2_moe.wave', BasePipeline, MujocoConfig, Go2WaveGaugeConfig, Go2MoETerrainConfig)
task_register.register('go2_moe.stairs_fd', BasePipeline, MujocoConfig, Go2StairsForwardGaugeConfig, Go2MoETerrainConfig)
task_register.register('go2_moe.stairs_bd', BasePipeline, MujocoConfig, Go2StairsBackwardGaugeConfig, Go2MoETerrainConfig)
task_register.register('go2_moe.obstacle', BasePipeline, MujocoConfig, Go2ObstacleGaugeConfig, Go2MoETerrainConfig)
