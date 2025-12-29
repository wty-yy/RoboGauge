# -*- coding: utf-8 -*-
'''
@File    : terrain_levels_config.py
@Time    : 2025/12/25 11:27:05
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Terrain Levels Configuration
'''
from robogauge.utils.config import Config

SEARCH_LEVELS_TERRAINS = ['slope_fd', 'slope_bd', 'wave', 'stairs_fd', 'stairs_bd', 'obstacle']
TERRAIN_NAME2_XML_NAME = {
    'flat': 'flat',
    'slope_fd': 'slope',
    'slope_bd': 'slope',
    'wave': 'wave',
    'stairs_fd': 'stairs',
    'stairs_bd': 'stairs',
    'obstacle': 'obstacle',
}

class TerrainSearchLevelsConfig(Config):
    """ Go2 robot init/target position """
    class flat:
        levels = [0]
        targets = [[4, 0, 0]]  # target positions for each level, if target goal is used
    
    class slope:
        levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        targets = [
            [4.8, 0, 0.588 + 0.1],
            [4.8, 0, 0.776 + 0.1],
            [4.8, 0, 0.964 + 0.1],
            [4.8, 0, 1.152 + 0.1],
            [4.8, 0, 1.340 + 0.1],
            [4.8, 0, 1.528 + 0.1],
            [4.8, 0, 1.716 + 0.1],
            [4.8, 0, 1.904 + 0.1],
            [4.8, 0, 2.092 + 0.1],
            [4.8, 0, 2.280 + 0.1],
        ]

    class wave:
        levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        targets = [
            [6.5, -2.65, 0.08],
            [6.5, -2.65, 0.16],
            [6.5, -2.65, 0.24],
            [6.5, -2.65, 0.32],
            [6.5, -2.65, 0.40],
            [6.5, -2.65, 0.48],
            [6.5, -2.65, 0.56],
            [6.5, -2.65, 0.64],
            [6.5, -2.65, 0.72],
            [6.5, -2.65, 0.80],
        ]

    class stairs:
        levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        targets = [
            [4.5, 0.0, 1.35],
            [4.5, 0.0, 1.80],
            [4.5, 0.0, 2.25],
            [4.5, 0.0, 2.70],
            [4.5, 0.0, 2.85],
            [4.5, 0.0, 3.00],
            [4.5, 0.0, 3.15],
            [4.5, 0.0, 3.30],
            [4.5, 0.0, 3.45],
            [4.5, 0.0, 3.60],
        ]

        spawns = [
            [1.15, 0.0, 1.1 - 0.05 * 6 - 0.15 * 3],
            [1.15, 0.0, 1.1 - 0.05 * 6 - 0.15 * 2],
            [1.15, 0.0, 1.1 - 0.05 * 6 - 0.15],
            [1.15, 0.0, 1.1 - 0.05 * 6],
            [1.15, 0.0, 1.1 - 0.05 * 5],
            [1.15, 0.0, 1.1 - 0.05 * 4],
            [1.15, 0.0, 1.1 - 0.05 * 3],
            [1.15, 0.0, 1.1 - 0.05 * 2],
            [1.15, 0.0, 1.1 - 0.05 * 1],
            [1.15, 0.0, 1.1],
        ]

    class obstacle:
        levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    
    class slope_fd(slope):  # forward direction
        pass
    class slope_bd(slope):  # backward direction
        pass
    class stairs_fd(stairs):  # forward direction
        pass
    class stairs_bd(stairs):  # backward direction
        pass

class TerrainEvalLevelsConfig(Config):
    class flat:
        levels = [0]

    class slope:
        levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        spawns = [
            [5.0, 0, 0.03 + 4.2 * (0.57 - 0.047 * 9)],
            [5.0, 0, 0.03 + 4.2 * (0.57 - 0.047 * 8)],
            [5.0, 0, 0.03 + 4.2 * (0.57 - 0.047 * 7)],
            [5.0, 0, 0.03 + 4.2 * (0.57 - 0.047 * 6)],
            [5.0, 0, 0.03 + 4.2 * (0.57 - 0.047 * 5)],
            [5.0, 0, 0.03 + 4.2 * (0.57 - 0.047 * 4)],
            [5.0, 0, 0.03 + 4.2 * (0.57 - 0.047 * 3)],
            [5.0, 0, 0.03 + 4.2 * (0.57 - 0.047 * 2)],
            [5.0, 0, 0.03 + 4.2 * (0.57 - 0.047)],
            [5.0, 0, 0.03 + 4.2 * 0.57],
        ]

    class wave:
        levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        spawns = [
            [4.55, 0, 0.65 - 0.075 * 9],
            [4.55, 0, 0.65 - 0.075 * 8],
            [4.55, 0, 0.65 - 0.075 * 7],
            [4.55, 0, 0.65 - 0.075 * 6],
            [4.55, 0, 0.65 - 0.075 * 5],
            [4.55, 0, 0.65 - 0.075 * 4],
            [4.55, 0, 0.65 - 0.075 * 3],
            [4.55, 0, 0.65 - 0.075 * 2],
            [4.55, 0, 0.65 - 0.075 * 1],
            [4.55, 0, 0.65],
        ]

    class stairs:
        levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        spawns = [
            [4.85, 0.0, 0.05 + 1.35],
            [4.85, 0.0, 0.05 + 1.80],
            [4.85, 0.0, 0.05 + 2.25 + 0.03],
            [4.85, 0.0, 0.05 + 2.70 + 0.08],
            [4.85, 0.0, 0.05 + 2.85 + 0.1],
            [4.85, 0.0, 0.05 + 3.00 + 0.12],
            [4.85, 0.0, 0.05 + 3.15 + 0.14],
            [4.85, 0.0, 0.05 + 3.30 + 0.16],
            [4.85, 0.0, 0.05 + 3.45 + 0.18],
            [4.85, 0.0, 0.05 + 3.60 + 0.2],
        ]

    class obstacle:
        levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        spawns = [
            [5, 0.0, 0.20 - 0.023 * 9],
            [5, 0.0, 0.20 - 0.023 * 8],
            [5, 0.0, 0.20 - 0.023 * 7],
            [5, 0.0, 0.20 - 0.023 * 6],
            [5, 0.0, 0.20 - 0.023 * 5],
            [5, 0.0, 0.20 - 0.023 * 4],
            [5, 0.0, 0.20 - 0.023 * 3],
            [5, 0.0, 0.20 - 0.023 * 2],
            [5, 0.0, 0.20 - 0.023 * 1],
            [5, 0.0, 0.20],
        ]

    class slope_fd(slope):  # forward direction
        pass
    class slope_bd(slope):  # backward direction
        pass
    class stairs_fd(stairs):  # forward direction
        pass
    class stairs_bd(stairs):  # backward direction
        pass

if __name__ == '__main__':
    terrain_search_cfg = TerrainSearchLevelsConfig()
    print(terrain_search_cfg.stairs.spawns)
