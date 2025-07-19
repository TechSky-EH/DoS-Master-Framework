#!/usr/bin/env python3
"""
DoS Master Framework - User Interface Module
Command-line and web interfaces
"""

# Import UI components with error handling
try:
    from .cli import DoSMasterCLI
    CLI_AVAILABLE = True
except ImportError as e:
    CLI_AVAILABLE = False
    DoSMasterCLI = None

try:
    from .web import create_app
    WEB_AVAILABLE = True
except ImportError as e:
    WEB_AVAILABLE = False
    create_app = None

__all__ = ['DoSMasterCLI', 'create_app', 'CLI_AVAILABLE', 'WEB_AVAILABLE']