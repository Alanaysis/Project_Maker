"""
Logging utility for the multi-GPU framework.
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str = "multi_gpu",
    level: int = logging.INFO,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Set up a logger with console handler.

    Args:
        name: Logger name
        level: Logging level
        format_string: Custom format string

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        if format_string is None:
            format_string = (
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            )
        formatter = logging.Formatter(format_string, datefmt="%H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(level)
    return logger
