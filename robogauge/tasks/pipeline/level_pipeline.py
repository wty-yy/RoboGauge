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
        logger.create(args.experiment_name+'_level', args.run_name)
    
    def run(self):
        logger.info(f"🚀 Starting Level Seacher for '{self.args.experiment_name}'.")
        logger.info(f"🔢 Seeds: {self.seeds}")

        # binary search levels
        l, r = 0, 10
        all_level_results = {}
        while l < r:
            level = (l + r + 1) // 2
            all_success, results = self.test_level(level)
            all_level_results[level] = results
            if all_success:
                l = level
            else:
                r = level - 1
        level = l
        level_results = all_level_results.get(l, {
            'model_path': results['model_path'],
            'terrain_name': results['terrain_name'],
            'terrain_level': 0,
        })
        if level >= 1:
            logger.info(f"🏆 Found maximum level: {level}")
        else:
            logger.info(f"❌ No valid level found [1-10].")
        with open(logger.log_dir / "level_search_results.yaml", 'w') as f:
            yaml.dump(level_results, f, allow_unicode=True, sort_keys=False)
        return level, level_results

    def test_level(self, level: int) -> bool:
        logger.info(f"🔍 Testing level {level}...")
        self.args.level = level
        multi_pipeline = MultiPipeline(self.args)
        aggregated_results = multi_pipeline.run()
        success_mean = float(aggregated_results['success']['mean'].split(' ')[0])
        all_success = success_mean >= 0.8
        if all_success:
            logger.info(f"✅ Level {level} passed all tests.")
        else:
            logger.info(f"❌ Level {level} failed some tests.")
        return all_success, aggregated_results
