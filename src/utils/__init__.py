#!/usr/bin/env python3
"""
DoS Master Framework - Utilities Module
Utility functions and helpers
"""

# Import utilities with error handling
_available_modules = {}

try:
    from .config import load_config, get_setting, set_setting, ConfigManager
    _available_modules['config'] = True
except ImportError:
    _available_modules['config'] = False
    # Fallback config functions
    def load_config():
        return {}
    def get_setting(key, default=None):
        return default
    def set_setting(key, value):
        return False
    ConfigManager = None

try:
    from .logger import setup_logger, get_logger, set_log_level
    _available_modules['logger'] = True
except ImportError:
    _available_modules['logger'] = False
    # Fallback logger functions
    import logging
    def setup_logger(name='dmf'):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def get_logger(name='dmf'):
        return setup_logger(name)
    
    def set_log_level(level):
        logger = get_logger()
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))

try:
    from .validation import (
        validate_target, validate_ip_address, validate_url, 
        validate_port, validate_attack_params, validate_profile
    )
    _available_modules['validation'] = True
except ImportError:
    _available_modules['validation'] = False
    # Fallback validation functions
    def validate_target(target):
        return target and isinstance(target, str) and len(target) > 0
    
    def validate_ip_address(ip):
        import re
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        return bool(re.match(pattern, ip))
    
    def validate_url(url):
        return url.startswith(('http://', 'https://'))
    
    def validate_port(port):
        try:
            return 1 <= int(port) <= 65535
        except:
            return False
    
    def validate_attack_params(params):
        return isinstance(params, dict) and 'target' in params
    
    def validate_profile(profile):
        return profile in ['stealth', 'moderate', 'aggressive']

try:
    from .network import NetworkUtils
    _available_modules['network'] = True
except ImportError:
    _available_modules['network'] = False
    NetworkUtils = None

__all__ = [
    'load_config', 'get_setting', 'set_setting', 'ConfigManager',
    'setup_logger', 'get_logger', 'set_log_level',
    'validate_target', 'validate_ip_address', 'validate_url',
    'validate_port', 'validate_attack_params', 'validate_profile',
    'NetworkUtils'
]