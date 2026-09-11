"""
Logging infrastructure for Auto Clicker Pro.
Provides structured console and rotating file logging to replace silent exception swallowing.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from utils import resource_path

LOG_DIR = os.path.join(os.path.expanduser("~"), ".autoclickerpro", "logs")

def setup_logging(level=logging.INFO):
    """Set up and configure the root logger for AutoClickerPro."""
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, "app.log")

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)-7s] [%(name)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Root application logger
    logger = logging.getLogger("AutoClickerPro")
    logger.setLevel(level)

    # Prevent duplicate handlers if called multiple times
    if not logger.handlers:
        # File handler (max 2MB, keep 3 backups)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

def get_logger(name=None):
    """Retrieve a child logger for a specific module."""
    if name:
        return logging.getLogger(f"AutoClickerPro.{name}")
    return logging.getLogger("AutoClickerPro")
