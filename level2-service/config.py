"""
Configuration for Level-2 Deep Analysis Service
"""

import logging
import logging.config


class Config:
    """Service configuration"""
    
    # Service
    SERVICE_PORT = 8001
    SERVICE_HOST = "0.0.0.0"
    
    # Selenium
    SELENIUM_TIMEOUT = 6  # Page load timeout in seconds
    REQUEST_TIMEOUT = 10  # Total request timeout in seconds
    HEADLESS_MODE = True
    
    # Batching
    MAX_BATCH_SIZE = 100
    
    # Database (future)
    DATABASE_URL = "sqlite:///./level2_service.db"
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class LogConfig(dict):
    """Logging configuration"""
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "default",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": "level2_service.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 3
            }
        },
        "loggers": {
            "": {
                "level": "DEBUG",
                "handlers": ["console", "file"]
            },
            "selenium": {
                "level": "WARNING",
                "handlers": ["file"]
            },
            "urllib3": {
                "level": "WARNING",
                "handlers": ["file"]
            }
        }
    }
