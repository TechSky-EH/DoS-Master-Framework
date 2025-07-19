#!/usr/bin/env python3
"""
DoS Master Framework - Main Package
Professional DoS Testing Framework for Authorized Security Testing

Author: Tech Sky
License: MIT
Version: 2.0
"""

__version__ = '2.0.0'
__author__ = 'Tech Sky'
__license__ = 'MIT'
__description__ = 'Professional DoS Testing Framework for Authorized Security Testing'

# Import main components
from .core.engine import DoSEngine
from .core.monitor import Monitor
from .core.analyzer import TrafficAnalyzer
from .core.reporter import ReportGenerator

# Import attack modules
from .attacks.icmp_flood import ICMPFlood
from .attacks.udp_flood import UDPFlood
from .attacks.syn_flood import SYNFlood
from .attacks.http_flood import HTTPFlood
from .attacks.slowloris import Slowloris

# Import utilities
from .utils.config import load_config, get_setting, set_setting
from .utils.logger import setup_logger, get_logger
from .utils.validation import validate_target, validate_attack_params

# Package metadata
FRAMEWORK_INFO = {
    'name': 'DoS Master Framework',
    'version': __version__,
    'author': __author__,
    'license': __license__,
    'description': __description__,
    'github': 'https://github.com/TechSky/dos-master-framework',
    'documentation': 'https://github.com/TechSky/dos-master-framework/docs'
}

# Legal notice
LEGAL_NOTICE = """
⚠️  LEGAL WARNING ⚠️

This framework is designed for authorized security testing only.
Unauthorized use against systems you do not own is illegal and may 
result in criminal prosecution.

By using this framework, you agree to:
- Only test systems you own or have explicit written permission to test
- Comply with all applicable laws and regulations
- Use the framework for defensive security purposes only
- Not cause harm or disruption to any systems or networks

The authors and contributors are not responsible for any misuse of this tool.
"""

def print_banner():
    """Print framework banner"""
    banner = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    DoS Master Framework v{__version__}                    ║
║              Professional DoS Testing Framework                  ║
║                                                                  ║
║  Author: {__author__:<50}  ║
║  License: {__license__:<49}  ║
║  GitHub: TechSky/dos-master-framework                            ║
╚══════════════════════════════════════════════════════════════════╝

{LEGAL_NOTICE}
"""
    print(banner)

def get_version():
    """Get framework version"""
    return __version__

def get_info():
    """Get framework information"""
    return FRAMEWORK_INFO.copy()

# Expose main classes for easy import
__all__ = [
    'DoSEngine',
    'Monitor', 
    'TrafficAnalyzer',
    'ReportGenerator',
    'ICMPFlood',
    'UDPFlood',
    'SYNFlood',
    'HTTPFlood',
    'Slowloris',
    'load_config',
    'setup_logger',
    'validate_target',
    'print_banner',
    'get_version',
    'get_info',
    'FRAMEWORK_INFO',
    'LEGAL_NOTICE'
]