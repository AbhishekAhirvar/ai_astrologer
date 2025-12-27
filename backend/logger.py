import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name="ai_astrologer"):
    """
    Sets up a professional, industry-standard logger with console and file output.
    Includes log rotation to prevent massive file sizes.
    """
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "app.log")
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate logs if setup_logger is called multiple times
    if logger.handlers:
        return logger

    # 1. Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 2. Rotating File Handler (max 5MB per file, keep 3 backup files)
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=5 * 1024 * 1024, 
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)

    # Create formatters and add them to handlers
    # Format: 2023-10-27 10:45:30 [INFO] [app.py:50] - Message content
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(name)s:%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# Global logger instance
logger = setup_logger()
