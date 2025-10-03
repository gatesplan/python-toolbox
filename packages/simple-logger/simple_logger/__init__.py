"""Simple Logger - loguru 기반 로거 래퍼"""

__version__ = "0.0.1"

from .logger import configure_logger, func_logging, init_logging
from loguru import logger

__all__ = [
    "configure_logger",
    "func_logging",
    "init_logging",
    "logger",
]
