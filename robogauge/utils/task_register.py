# -*- coding: utf-8 -*-
'''
@File    : task_register.py
@Time    : 2025/11/27 15:59:03
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Task Registration Utility
'''
from robogauge import ROBOGAUGE_ROOT_DIR
from robogauge.utils.logger import logger
from robogauge.utils.helpers import parse_args, set_seed, class_to_dict
from robogauge.tasks.gauge.gauge_configs.terrain_levels_config import TerrainSearchLevelsConfig

class TaskRegister():
    def __init__(self):
        self.pipeline_classes = {}
        self.sim_cfgs = {}
        self.gauger_cfgs = {}
        self.robot_cfgs = {}
    
    def register(self, name: str, pipeline_class, sim_cfg, gauger_cfg, robot_cfg):
        self.pipeline_classes[name] = pipeline_class
        self.sim_cfgs[name] = sim_cfg
        self.gauger_cfgs[name] = gauger_cfg
        self.robot_cfgs[name] = robot_cfg
    
    def get_pipeline_class(self, name: str):
        if name not in self.pipeline_classes:
            raise ValueError(f"Task '{name}' is not registered.")
        return self.pipeline_classes[name]
    
    def get_cfgs(self, name):
        if name not in self.sim_cfgs:
            raise ValueError(f"Task '{name}' is not registered, checkout '{ROBOGAUGE_ROOT_DIR}/robogauge/tasks/__init__.py'.")
        sim_cfg = self.sim_cfgs[name]
        gauger_cfg = self.gauger_cfgs[name]
        robot_cfg = self.robot_cfgs[name]
        return sim_cfg, gauger_cfg, robot_cfg
    
    def make_pipeline(self, args=None, sim_cfg=None, gauger_cfg=None, robot_cfg=None, create_logger=True):
        if args is None:
            args = parse_args()
        default_cfgs = self.get_cfgs(args.task_name)
        if sim_cfg is None:
            sim_cfg = default_cfgs[0]
        if gauger_cfg is None:
            gauger_cfg = default_cfgs[1]
        if robot_cfg is None:
            robot_cfg = default_cfgs[2]
        if args is not None:
            self.update_args_to_cfg(sim_cfg, gauger_cfg, robot_cfg, args)
        pipeline_class = self.get_pipeline_class(args.task_name)
        set_seed(args.seed)
        run_name = args.run_name + f'_{args.seed}'
        if create_logger:
            logger.create(args.experiment_name, run_name)
        return pipeline_class(run_name, sim_cfg, robot_cfg, gauger_cfg)

    def update_args_to_cfg(self, sim_cfg, gauger_cfg, robot_cfg, args):
        if args.model_path is not None:
            robot_cfg.control.model_path = args.model_path
        if args.headless is not None:
            sim_cfg.viewer.headless = args.headless
        if args.save_video is not None:
            sim_cfg.render.save_video = args.save_video
        if args.write_tensorboard is not None:
            gauger_cfg.write_tensorboard = args.write_tensorboard
        if args.friction is not None:
            sim_cfg.domain_rand.friction = args.friction
        if args.base_mass is not None:
            sim_cfg.domain_rand.base_mass = args.base_mass
        if args.level is not None:
            gauger_cfg.assets.terrain_level = args.level
            levels_cfg = TerrainSearchLevelsConfig()
            cfg = getattr(levels_cfg, gauger_cfg.assets.terrain_name, None)
            assert cfg is not None, f"Level {args.level} configuration not found in TerrainLevelsConfig."
            assert args.level in cfg.levels, f"Level must be in {cfg.levels}."
            if hasattr(cfg, 'targets'):
                gauger_cfg.goals.target_pos_velocity.target_pos = cfg.targets[cfg.levels.index(args.level)]
            if hasattr(cfg, 'spawns'):
                gauger_cfg.assets.terrain_spawn_pos = cfg.spawns[cfg.levels.index(args.level)]
            xml = gauger_cfg.assets.terrain_xmls[0]
            xml = xml.rsplit('/', 1)[0] + f"/{gauger_cfg.assets.terrain_name}_{args.level}.xml"
            gauger_cfg.assets.terrain_xmls[0] = xml
        if args.goals is not None:
            keys = class_to_dict(gauger_cfg.goals).keys()
            enable_count = 0
            for key in keys:
                flag = key in args.goals
                getattr(gauger_cfg.goals, key).enabled = flag
                enable_count += int(flag)
            assert enable_count > 0, f"At least one goal must be enabled from '{args.goals}', available goals are {list(keys)}."

task_register = TaskRegister()
