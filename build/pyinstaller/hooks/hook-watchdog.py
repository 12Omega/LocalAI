# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller hook for watchdog

This hook ensures that watchdog's platform-specific observers are properly included.

Requirements addressed: 8.3 - Bundle modules with data files
Related to: Requirement 12.3 (detect external config file changes)

watchdog has different observer implementations for each platform:
- Windows: WindowsApiObserver
- Linux: InotifyObserver
- macOS: FSEventsObserver, KqueueObserver

This hook includes the appropriate platform-specific modules.
"""

import sys
from PyInstaller.utils.hooks import collect_submodules

# Collect all watchdog submodules
hiddenimports = collect_submodules('watchdog')

# Add platform-specific observers
if sys.platform.startswith('win'):
    hiddenimports += [
        'watchdog.observers.read_directory_changes',
        'watchdog.observers.winapi',
    ]
elif sys.platform.startswith('linux'):
    hiddenimports += [
        'watchdog.observers.inotify',
        'watchdog.observers.inotify_buffer',
        'watchdog.observers.inotify_c',
    ]
elif sys.platform.startswith('darwin'):
    hiddenimports += [
        'watchdog.observers.fsevents',
        'watchdog.observers.fsevents2',
        'watchdog.observers.kqueue',
    ]

# Core watchdog modules
hiddenimports += [
    'watchdog.observers',
    'watchdog.observers.api',
    'watchdog.events',
    'watchdog.utils',
]
