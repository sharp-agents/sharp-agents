"""Logging utility using loguru."""

import sys
from loguru import logger
from pathlib import Path


def setup_logger():
    """Setup and configure the logger."""
    # Remove default handler
    logger.remove()
    
    # Add console handler with colors
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True
    )
    
    # Add file handler with daily rotation
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "sharp_agents.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} - {message}",
        level="DEBUG",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    return logger


def get_logger(name: str):
    """Get a logger instance for a specific module."""
    return logger.bind(name=name)


# Setup logger when module is imported
setup_logger()
