"""
src/utils/logger.py - Logging setup
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from src.config import LOGGING_CONFIG, PATHS

def setup_logger(name):
    """Setup logger with file and console handlers"""
    os.makedirs(PATHS['logs'], exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(LOGGING_CONFIG['level'])
    
    # Clear existing handlers
    logger.handlers = []
    
    # Console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console_format = logging.Formatter('%(levelname)s - %(message)s')
    console.setFormatter(console_format)
    logger.addHandler(console)
    
    # File handler
    file_handler = RotatingFileHandler(
        LOGGING_CONFIG['file'],
        maxBytes=LOGGING_CONFIG['max_bytes'],
        backupCount=LOGGING_CONFIG['backup_count']
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(LOGGING_CONFIG['format'])
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    return logger
