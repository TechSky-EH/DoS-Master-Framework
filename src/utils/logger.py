#!/usr/bin/env python3
"""
DoS Master Framework - Logging System
Comprehensive logging with file rotation and structured output
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """Colored console formatter"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        
        # Add color to levelname
        colored_levelname = f"{log_color}{record.levelname}{reset_color}"
        record.colored_levelname = colored_levelname
        
        # Format timestamp
        record.timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        return super().format(record)

class FrameworkLogger:
    """Framework logger with file and console handlers"""
    
    def __init__(self, name: str = 'dos-master-framework'):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        self._setup_console_handler()
        self._setup_file_handler()
        
    def _setup_console_handler(self):
        """Setup console handler with colors"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        console_format = '[%(timestamp)s] %(colored_levelname)s - %(message)s'
        console_formatter = ColoredFormatter(console_format)
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(console_handler)
    
    def _setup_file_handler(self):
        """Setup file handler with rotation"""
        log_dir = Path('/var/log/dos-master-framework')
        
        # Create log directory if it doesn't exist
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / 'dmf.log'
        except PermissionError:
            # Fallback to user directory
            log_dir = Path.home() / '.dos-master-framework' / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / 'dmf.log'
        
        # Rotating file handler (10MB max, 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        file_format = '[%(asctime)s] %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s'
        file_formatter = logging.Formatter(file_format)
        file_handler.setFormatter(file_formatter)
        
        self.logger.addHandler(file_handler)
    
    def get_logger(self):
        """Get logger instance"""
        return self.logger
    
    def set_level(self, level: str):
        """Set logging level"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        if level.upper() in level_map:
            self.logger.setLevel(level_map[level.upper()])
            
            # Update console handler level
            for handler in self.logger.handlers:
                if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                    handler.setLevel(level_map[level.upper()])
    
    def add_file_handler(self, log_file: str, level: str = 'DEBUG'):
        """Add additional file handler"""
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=10*1024*1024, backupCount=5
            )
            
            level_map = {
                'DEBUG': logging.DEBUG,
                'INFO': logging.INFO,
                'WARNING': logging.WARNING,
                'ERROR': logging.ERROR,
                'CRITICAL': logging.CRITICAL
            }
            
            file_handler.setLevel(level_map.get(level.upper(), logging.DEBUG))
            
            file_format = '[%(asctime)s] %(levelname)s - %(name)s - %(message)s'
            file_formatter = logging.Formatter(file_format)
            file_handler.setFormatter(file_formatter)
            
            self.logger.addHandler(file_handler)
            
        except Exception as e:
            self.logger.error(f"Failed to add file handler: {e}")

# Global logger instance
_framework_logger = None

def setup_logger(name: str = 'dos-master-framework', level: str = 'INFO') -> logging.Logger:
    """Setup and return framework logger"""
    global _framework_logger
    
    if _framework_logger is None:
        _framework_logger = FrameworkLogger(name)
        _framework_logger.set_level(level)
    
    return _framework_logger.get_logger()

def get_logger(name: str = 'dos-master-framework') -> logging.Logger:
    """Get existing logger or create new one"""
    if _framework_logger is None:
        return setup_logger(name)
    return _framework_logger.get_logger()

def set_log_level(level: str):
    """Set global log level"""
    if _framework_logger:
        _framework_logger.set_level(level)

def add_log_file(log_file: str, level: str = 'DEBUG'):
    """Add additional log file"""
    if _framework_logger:
        _framework_logger.add_file_handler(log_file, level)