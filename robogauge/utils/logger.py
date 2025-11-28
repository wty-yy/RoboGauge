# -*- coding: utf-8 -*-
'''
@File    : my_logger.py
@Time    : 2025/02/26 21:43:47
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : A customed logger, support: 
1. Color level name
2. Output to console and save log to file
3. Support vscode file location jump (ctrl+left key)
'''
import time
import logging
from pathlib import Path
from robogauge import ROBOGAUGE_ROOT_DIR
from torch.utils.tensorboard import SummaryWriter

class LogColor:
    """ ANSI color codes """
    RESET = '\033[0m'
    RED   = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE  = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN  = '\033[36m'
    WHITE = '\033[37m'
    BOLD  = '\033[1m'
    UNDERLINE = '\033[4m'

LOG_COLORS = {
    """ Match level name to color """
    'DEBUG': LogColor.CYAN,
    'INFO': LogColor.GREEN,
    'WARNING': LogColor.YELLOW,
    'ERROR': LogColor.RED,
    'CRITICAL': LogColor.RED + LogColor.BOLD,
}

class ColorFormatter(logging.Formatter):
    """Color Formatter for color_level"""
    def __init__(self, fmt, datefmt=None, use_color=True):
        self.formatter = logging.Formatter(fmt, datefmt)
        self.use_color = use_color

    def format(self, record):
        record.color_level = f"{LOG_COLORS.get(record.levelname, LogColor.RESET)}{record.levelname}{LogColor.RESET}" if self.use_color else record.levelname
        return self.formatter.format(record)


class Logger:
    logger: logging.Logger = None
    log_dir: Path = None
    writer: SummaryWriter = None

    def create(self,
        experiment_name,
        console_output=True, color_output=True,
        log_level=logging.DEBUG, save_file_mode='a'
    ):
        """
        Create customed Logger

        Args:
            logger_name (str): Logger name
            console_output (bool, optional): Whether output to console. Defaults to True.
            color_output (bool, optional): Whether use color output. Defaults to True.
            log_level (int, optional): Defaults to logging.DEBUG.
            save_file_mode (str, optional): The mode of saving to path_log_file

        Returns:
            logging.Logger: logger
        """
        self.logger = logging.getLogger(experiment_name + "_logger")
        self.logger.setLevel(log_level)
        self.logger.propagate = False

        console_formatter = ColorFormatter(    # console output format
            fmt="%(asctime)s - %(color_level)s - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            use_color=color_output
        )
        file_formatter = logging.Formatter(    # file output format
            fmt="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        if console_output:
            sh = logging.StreamHandler()
            sh.setFormatter(console_formatter)
            self.logger.addHandler(sh)

        self.log_dir = Path(ROBOGAUGE_ROOT_DIR) / "logs" / experiment_name / time.strftime("%Y%m%d-%H-%M-%S")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        path_log_file = self.log_dir / "stdout.log"
        if path_log_file:
            fh = logging.FileHandler(path_log_file, mode=save_file_mode, encoding='utf-8')
            fh.setFormatter(file_formatter)
            self.logger.addHandler(fh)
    
    def create_tensorboard(self, run_name: str):
        if self.writer is not None:
            self.writer.close()
        self.writer = SummaryWriter(str(self.log_dir / run_name))
        self.info(f"Tensorboard writer created at: {self.log_dir / run_name}")

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs, stacklevel=2)
    
    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs, stacklevel=2)
    
    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs, stacklevel=2)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs, stacklevel=2)

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs, stacklevel=2)
    
    def log(self, value, tag, step):
        """ Log scalar value to tensorboard

        Args:
            value (float): scalar value
            tag (str): tag name
            step (int): step number
        """
        if self.writer is not None:
            self.writer.add_scalar(tag, value, step)
        else:
            self.warning("Tensorboard writer is not initialized, skipping log.")

logger = Logger()

if __name__ == '__main__':
    from pathlib import Path
    path_parent = Path(__file__).parents[0]
    path_log = path_parent / "app.log"

    logger = Logger()
    logger.create("my_logger")

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    # logger_no_color = Logger()
    # logger_no_color.create("no_color_logger", console_output=True, color_output=False)
    # logger_no_color.info("This is a info message without color")

    # logger_file_only = Logger()
    # logger_file_only.create("file_only_logger", console_output=False)  # save to file only
    # logger_file_only.error("This is an error message only in file")
