from pathlib import Path

__version__ = "1.0.0"
ROBOGAUGE_ROOT_DIR = str(Path(__file__).parents[1])
ROBOGAUGE_LOGS_DIR = str(Path(ROBOGAUGE_ROOT_DIR) / "logs")
