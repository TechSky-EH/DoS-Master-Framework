#!/usr/bin/env python3
"""
DoS Master Framework - User Interface Module
Command-line and web interfaces
"""

# Import main UI components
try:
    from .cli import DoSMasterCLI
except ImportError:
    DoSMasterCLI = None

try:
    from .web import create_app
except ImportError:
    create_app = None

__all__ = [
    'DoSMasterCLI',
    'create_app'
]