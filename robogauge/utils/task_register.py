# -*- coding: utf-8 -*-
'''
@File    : task_register.py
@Time    : 2025/11/27 15:59:03
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Task Registration Utility
'''
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
            raise ValueError(f"Task '{name}' is not registered.")
        sim_cfg = self.sim_cfgs[name]
        gauger_cfg = self.gauger_cfgs[name]
        robot_cfg = self.robot_cfgs[name]
        return sim_cfg, gauger_cfg, robot_cfg
    
    def make_pipeline(self, name, args=None, sim_cfg=None, gauger_cfg=None, robot_cfg=None, run_name='0'):
        default_cfgs = self.get_cfgs(name)
        if sim_cfg is None:
            sim_cfg = default_cfgs[0]
        if gauger_cfg is None:
            gauger_cfg = default_cfgs[1]
        if robot_cfg is None:
            robot_cfg = default_cfgs[2]
        if args is not None:
            self.update_args_to_cfg(sim_cfg, gauger_cfg, robot_cfg, args)
        pipeline_class = self.get_pipeline_class(name)
        return pipeline_class(run_name, sim_cfg, robot_cfg, gauger_cfg)

    def update_args_to_cfg(self, sim_cfg, gauger_cfg, robot_cfg, args):
        if args.headless is not None:
            sim_cfg.viewer.headless = args.headless
        if args.save_video is not None:
            sim_cfg.render.save_video = args.save_video

task_register = TaskRegister()
