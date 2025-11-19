# backend/app/utils/logger.py
"""
Logging configuration for InfoSense application.
Provides structured JSON logging for production environments.
"""

import logging
import sys
from pythonjsonlogger import jsonlogger
from app.core.config import settings

# Custom JSON formatter for structured logging
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that adds application-specific fields.
    """
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add application name
        log_record['app'] = 'infosense'
        
        # Add environment
        log_record['env'] = settings.environment
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add timestamp if not present
        if 'timestamp' not in log_record:
            log_record['timestamp'] = self.formatTime(record)
        
        # Add module and function info
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno


def setup_logging() -> logging.Logger:
    """
    Setup and configure application logging.
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("infosense")
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create handler
    if settings.environment == "production":
        # JSON logging for production
        handler = logging.StreamHandler(sys.stdout)
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Human-readable logging for development
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Set_levels for external libraries
    logging.getLogger('telethon').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    
    logger.info(f"Logging configured for environment: {settings.environment}")
    return logger


# Global logger instance
logger = setup_logging()
