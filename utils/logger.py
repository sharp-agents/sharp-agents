"""Logging utility using loguru."""

import sys
from loguru import logger
from pathlib import Path


def setup_logger():
    """Setup and configure the logger."""
    # Remove default handler
    logger.remove()
    
    # Add console handler with color
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Add file handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days"
    )
    
    return logger


def get_logger(name: str):
    """Get a logger instance for a specific module."""
    return logger.bind(name=name)


# Setup logger when module is imported
setup_logger()
