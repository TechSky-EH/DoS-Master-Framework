#!/usr/bin/env python3
"""
DoS Master Framework - Configuration Management
Centralized configuration loading and management
"""

import os
import yaml
import json
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    """Configuration management class"""
    
    def __init__(self):
        self.config_dir = Path('/etc/dos-master-framework')
        self.user_config_dir = Path.home() / '.dos-master-framework'
        self.project_config_dir = Path(__file__).parent.parent.parent / 'config'
        
        self._config_cache = {}
        
    def load_config(self, config_name: str = 'default') -> Dict[str, Any]:
        """Load configuration file"""
        if config_name in self._config_cache:
            return self._config_cache[config_name]
        
        config_file = f"{config_name}.yaml"
        config_data = {}
        
        # Try loading from different locations (priority order)
        search_paths = [
            self.user_config_dir / config_file,
            self.config_dir / config_file,
            self.project_config_dir / config_file
        ]
        
        for config_path in search_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config_data = yaml.safe_load(f) or {}
                    break
                except Exception as e:
                    print(f"Warning: Failed to load config from {config_path}: {e}")
                    continue
        
        # Apply default values if no config found
        if not config_data:
            config_data = self._get_default_config()
        
        # Merge with environment variables
        config_data = self._merge_env_vars(config_data)
        
        # Cache the config
        self._config_cache[config_name] = config_data
        
        return config_data
    
    def save_config(self, config_data: Dict[str, Any], config_name: str = 'default') -> bool:
        """Save configuration file"""
        try:
            # Create user config directory if it doesn't exist
            self.user_config_dir.mkdir(parents=True, exist_ok=True)
            
            config_file = self.user_config_dir / f"{config_name}.yaml"
            
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            # Update cache
            self._config_cache[config_name] = config_data
            
            return True
            
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get_setting(self, config_name: str, key_path: str, default: Any = None) -> Any:
        """Get specific setting using dot notation"""
        config = self.load_config(config_name)
        
        keys = key_path.split('.')
        value = config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set_setting(self, config_name: str, key_path: str, value: Any) -> bool:
        """Set specific setting using dot notation"""
        config = self.load_config(config_name)
        
        keys = key_path.split('.')
        current = config
        
        # Navigate to parent
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the value
        current[keys[-1]] = value
        
        return self.save_config(config, config_name)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'framework': {
                'name': 'DoS Master Framework',
                'version': '2.0',
                'author': 'Tech Sky'
            },
            'global': {
                'log_level': 'INFO',
                'log_file': '/var/log/dos-master-framework/dmf.log',
               'max_threads': 50,
               'default_timeout': 30
           },
           'profiles': {
               'stealth': {
                   'description': 'Low-rate attacks for detection testing',
                   'max_rate': 100,
                   'max_threads': 5,
                   'default_duration': 300
               },
               'moderate': {
                   'description': 'Balanced attacks for general testing',
                   'max_rate': 1000,
                   'max_threads': 15,
                   'default_duration': 120
               },
               'aggressive': {
                   'description': 'High-intensity attacks for stress testing',
                   'max_rate': 10000,
                   'max_threads': 50,
                   'default_duration': 60
               }
           },
           'attacks': {
               'icmp_flood': {
                   'default_packet_size': 1024,
                   'max_packet_size': 65507,
                   'min_packet_size': 8,
                   'default_threads': 5
               },
               'udp_flood': {
                   'default_packet_size': 1024,
                   'default_ports': [53, 80, 123, 161, 443],
                   'default_threads': 8
               },
               'syn_flood': {
                   'enable_spoofing': True,
                   'default_threads': 8,
                   'sequence_randomization': True
               },
               'http_flood': {
                   'default_threads': 20,
                   'request_timeout': 10
               }
           },
           'monitoring': {
               'enabled': True,
               'update_interval': 5,
               'capture_packets': False,
               'metrics_retention': 3600
           },
           'safety': {
               'require_confirmation': True,
               'max_duration': 3600,
               'blocked_targets': [
                   '8.8.8.8', '1.1.1.1', 'google.com', 'cloudflare.com'
               ],
               'whitelist_mode': False
           }
       }
   
   def _merge_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
       """Merge environment variables into configuration"""
       env_mappings = {
           'DMF_LOG_LEVEL': 'global.log_level',
           'DMF_LOG_FILE': 'global.log_file',
           'DMF_MAX_THREADS': 'global.max_threads',
           'DMF_WEB_PORT': 'web_interface.port',
           'DMF_WEB_HOST': 'web_interface.host'
       }
       
       for env_var, config_path in env_mappings.items():
           env_value = os.getenv(env_var)
           if env_value:
               self._set_nested_value(config, config_path, env_value)
       
       return config
   
   def _set_nested_value(self, config: Dict[str, Any], key_path: str, value: Any):
       """Set nested value in configuration"""
       keys = key_path.split('.')
       current = config
       
       for key in keys[:-1]:
           if key not in current:
               current[key] = {}
           current = current[key]
       
       # Try to convert value to appropriate type
       if isinstance(current.get(keys[-1]), int):
           try:
               value = int(value)
           except ValueError:
               pass
       elif isinstance(current.get(keys[-1]), bool):
           value = value.lower() in ('true', '1', 'yes', 'on')
       
       current[keys[-1]] = value

# Global configuration instance
config_manager = ConfigManager()

def load_config(config_name: str = 'default') -> Dict[str, Any]:
   """Load configuration (convenience function)"""
   return config_manager.load_config(config_name)

def get_setting(key_path: str, default: Any = None, config_name: str = 'default') -> Any:
   """Get configuration setting (convenience function)"""
   return config_manager.get_setting(config_name, key_path, default)

def set_setting(key_path: str, value: Any, config_name: str = 'default') -> bool:
   """Set configuration setting (convenience function)"""
   return config_manager.set_setting(config_name, key_path, value)