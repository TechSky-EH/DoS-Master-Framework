#!/usr/bin/env python3
"""
DoS Master Framework - Main Source Package
Professional DoS Testing Framework for Authorized Security Testing
"""

import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Package version
__version__ = '2.0.0'
__author__ = 'Tech Sky'
__license__ = 'MIT'

# Try to import main components
try:
    from . import core
    from . import ui
    from . import utils  
    from . import attacks
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    import warnings
    warnings.warn(f"Some modules could not be imported: {e}")
    IMPORTS_SUCCESSFUL = False

__all__ = ['core', 'ui', 'utils', 'attacks', '__version__', '__author__']