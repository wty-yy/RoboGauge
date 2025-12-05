# -*- coding: utf-8 -*-
'''
@File    : go2_moe_config.py
@Time    : 2025/12/05 17:32:27
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : None
'''
from robogauge.tasks.robots.go2.go2_config import Go2Config

class Go2MoEConfig(Go2Config):
    robot_class = 'Go2MoE'

    class control(Go2Config.control):
        model_path = "{ROBOGAUGE_ROOT_DIR}/resources/models/go2/go2_moe_cts_124k.pt"
