# -*- coding: utf-8 -*-
'''
@File    : level_pipeline.py
@Time    : 2025/12/22 20:38:11
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Level Pipeline for Robogauge
'''
import yaml

from robogauge.tasks.pipeline.multi_pipeline import MultiPipeline
from robogauge.utils.logger import logger

class LevelPipeline:
    def __init__(self, args):
        self.args = args
        self.seeds = args.seeds
        self.model_path = None
        logger.create(args.experiment_name+'_level', args.run_name)
    
    def run(self):
        logger.info(f"🚀 Starting Level Seacher for '{self.args.experiment_name}'.")
        logger.info(f"🔢 Seeds: {self.seeds}")

        # binary search levels
        l, r = 0, 10
        while l < r:
            level = (l + r + 1) // 2
            if self.test_level(level):
                l = level
            else:
                r = level - 1
        if l >= 1:
            logger.info(f"🏆 Found maximum level: {l}")
        else:
            logger.info(f"❌ No valid level found [1-10].")
    
    def test_level(self, level: int) -> bool:
        logger.info(f"🔍 Testing level {level}...")
        self.args.level = level
        multi_pipeline = MultiPipeline(self.args)
        log_dir = multi_pipeline.run()
        # load results.yaml
        with open(log_dir / "aggregated_results.yaml", 'r') as f:
            results = yaml.safe_load(f)
        self.model_path = results['model_path']
        success_mean = float(results['success']['mean'].split(' ')[0])
        all_success = success_mean == 1.0
        if all_success:
            logger.info(f"✅ Level {level} passed all tests.")
        else:
            logger.info(f"❌ Level {level} failed some tests.")
        return all_success
