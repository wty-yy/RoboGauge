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
from copy import deepcopy

from robogauge.tasks.pipeline.multi_pipeline import MultiPipeline
from robogauge.utils.logger import Logger
from robogauge.utils.progress_monitor import report_progress, ProgressTypes, ProgressData
from robogauge.utils.file_utils import compress_directory

level_logger = Logger()  # LevelPipeline logger

class LevelPipeline:
    def __init__(self, args, console_output=True, progress_data: ProgressData = None):
        self.args = args
        self.seeds = args.search_seeds
        self.console_output = console_output
        self.progress_data = progress_data
        parent_log_dir = getattr(args, 'parent_log_dir', None)
        level_logger.create(args.experiment_name+'_level', args.run_name, console_output=console_output, parent_log_dir=parent_log_dir)
        self.args.parent_log_dir = str(level_logger.log_dir / "subtasks")
        self.compress_logs = args.compress_logs
        args.compress_logs = False  # Disable child log compression
    
    def run(self):
        level_logger.info(f"🚀 Starting Level Searcher for '{self.args.experiment_name}'.")
        level_logger.info(f"🔢 Seeds: {self.seeds}")
        report_progress(self.progress_data, ProgressTypes.INIT, total=10, desc="🔍 Searching Max Level")

        # binary search levels
        l, r = 0, 10
        all_level_results = {}
        while l < r:
            level = (l + r + 1) // 2
            report_progress(self.progress_data, ProgressTypes.DESC, desc=f"🔍 Testing Level {level}")
            all_success, results = self.test_level(level)
            all_level_results[level] = results
            if all_success:
                l = level
            else:
                r = level - 1
            report_progress(self.progress_data, ProgressTypes.UPDATE, value=1)
        level = l
        level_results = all_level_results.get(l, {
            'model_path': results['model_path'],
            'terrain_name': results['terrain_name'],
            'terrain_level': 0,
        })
        if level >= 1:
            level_logger.info(f"🏆 Found maximum level: {level}")
        else:
            level_logger.info(f"❌ No valid level found [1-10].")
        with open(level_logger.log_dir / "level_search_results.yaml", 'w') as f:
            yaml.dump(level_results, f, allow_unicode=True, sort_keys=False)
        level_logger.logger.info(f"📂 Level search results saved to: {level_logger.log_dir / 'level_search_results.yaml'}")
        if self.compress_logs:
            compress_directory(level_logger.log_dir / "subtasks", delete_original=True, logger=level_logger)
        return level, level_results

    def test_level(self, level: int):
        level_logger.info(f"🔍 Testing level {level}...")
        args = deepcopy(self.args)
        args.level = level
        args.seeds = self.seeds
        multi_pipeline = MultiPipeline(args, console_output=self.console_output)
        aggregated_results = multi_pipeline.run()
        success_mean = float(aggregated_results['summary']['success']['mean'].split(' ')[0])
        all_success = success_mean >= 0.8
        if all_success:
            level_logger.info(f"✅ Level {level} passed all tests, success mean: {success_mean}.")
        else:
            level_logger.info(f"❌ Level {level} failed some tests, success mean: {success_mean}.")
        return all_success, aggregated_results
