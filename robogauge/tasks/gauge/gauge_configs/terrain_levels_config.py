from robogauge.utils.config import Config

class TerrainLevelsConfig(Config):
    class flat:
        levels = [0]
        targets = [[4, 0, 0]]  # target positions for each level, if target goal is used
    
    class slope:
        levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        targets = [
            [5, 0, 0.588],
            [5, 0, 0.776],
            [5, 0, 0.964],
            [5, 0, 1.152],
            [5, 0, 1.340],
            [5, 0, 1.528],
            [5, 0, 1.716],
            [5, 0, 1.904],
            [5, 0, 2.092],
            [5, 0, 2.280],
        ]

    class wave:
        levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        targets = []

