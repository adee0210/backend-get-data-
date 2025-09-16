import logging
from logging.handlers import RotatingFileHandler
import os


class LoggingConfig:
    _handler = None

    @staticmethod
    def logger_config(log_name: str, log_file="main.log", level: int = logging.INFO):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        root_dir = os.path.join(base_dir, log_file)

        formatter = logging.Formatter(
            "%(asctime)s - %(processName)s - %(levelname)s - %(name)s - %(message)s"
        )

        file_handler = RotatingFileHandler(
            filename=root_dir, maxBytes=10 * 1024 * 1024, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger = logging.getLogger(log_name)

        if not logger.handlers:
            for h in (console_handler, file_handler):
                logger.addHandler(h)

        logger.setLevel(level=level)
        logger.propagate = False

        return logger
