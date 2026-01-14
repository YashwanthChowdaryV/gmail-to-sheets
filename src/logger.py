"""
Enhanced logging with timestamps - Bonus Feature
FIXED VERSION
"""

import logging
import os
from datetime import datetime
import config


class EmailLogger:
    """Custom logger with timestamps and file output"""
    
    def __init__(self):
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure logger with timestamps"""
        self.logger = logging.getLogger('EmailProcessor')
        
        # Set level
        try:
            level = getattr(logging, config.LOG_LEVEL)
        except:
            level = logging.INFO
        
        self.logger.setLevel(level)
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Console handler (always on)
        console_handler = logging.StreamHandler()
        console_format = logging.Formatter(
            '%(asctime)s - %(levelname)8s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        console_handler.setLevel(level)
        self.logger.addHandler(console_handler)
        
        # File handler (if enabled)
        if config.LOG_ENABLED and config.LOG_FILE:
            try:
                # Create directory if needed
                log_dir = os.path.dirname(config.LOG_FILE)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                
                file_handler = logging.FileHandler(config.LOG_FILE, encoding='utf-8', mode='a')
                file_format = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(file_format)
                file_handler.setLevel(level)
                self.logger.addHandler(file_handler)
                
                # Log to file after setup
                self.info(f"Logging to file: {config.LOG_FILE}")
            except Exception as e:
                print(f"⚠️ Failed to setup file logging: {e}")
    
    def info(self, message):
        """Log info message with timestamp"""
        self.logger.info(message)
    
    def warning(self, message):
        """Log warning message with timestamp"""
        self.logger.warning(message)
    
    def error(self, message, exc_info=False):
        """Log error message with timestamp"""
        self.logger.error(message, exc_info=exc_info)
    
    def debug(self, message):
        """Log debug message with timestamp"""
        self.logger.debug(message)


# Create global instance
logger = EmailLogger()