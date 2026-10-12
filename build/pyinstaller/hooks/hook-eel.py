# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller hook for Eel framework

This hook ensures that Eel's internal web server files and bottle framework
dependencies are properly bundled with the executable.

Requirements addressed: 8.3 - Bundle Eel framework HTML/CSS/JS files

The Eel framework uses:
- bottle (web server framework)
- bottle_websocket (WebSocket support)
- gevent (async support)

This hook collects:
1. Eel's internal template files
2. All submodules from eel package
3. Data files from eel package
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all submodules from eel package
hiddenimports = collect_submodules('eel')

# Collect data files from eel (templates, etc.)
datas = collect_data_files('eel')

# Ensure bottle and dependencies are included
hiddenimports += [
    'bottle',
    'bottle_websocket',
    'gevent',
    'gevent.pywsgi',
    'gevent.monkey',
    'geventwebsocket',
    'geventwebsocket.handler',
]
