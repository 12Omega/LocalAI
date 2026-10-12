"""
GUI module for Desktop Application

This module provides a graphical user interface for the Local AI Development Environment
using the Eel framework to bridge Python backend with HTML/CSS/JavaScript frontend.
"""

__version__ = "0.1.0"

# Lazy imports to avoid requiring GUI dependencies during testing
def start_gui():
    """Start the GUI application."""
    from .gui_app import start_gui as _start_gui
    return _start_gui()

# Export platform-specific path utilities for external use
from .platform_paths import get_config_dir, get_data_dir, get_log_dir, PlatformPaths

__all__ = ["start_gui", "get_config_dir", "get_data_dir", "get_log_dir", "PlatformPaths"]
