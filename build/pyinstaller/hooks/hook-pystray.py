# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller hook for pystray

This hook ensures that pystray's platform-specific backends are properly included.

Requirements addressed: 8.3 - Bundle modules with data files
Related to: Requirement 9 (System tray integration)

pystray has different backends for each platform:
- Windows: _win32
- Linux: _xorg, _gtk
- macOS: _darwin

This hook includes the appropriate platform-specific modules.
"""

import sys
from PyInstaller.utils.hooks import collect_submodules

# Collect all pystray submodules
hiddenimports = collect_submodules('pystray')

# Add platform-specific backends
if sys.platform.startswith('win'):
    hiddenimports += [
        'pystray._win32',
        'pystray._util.win32',
    ]
elif sys.platform.startswith('linux'):
    hiddenimports += [
        'pystray._xorg',
        'pystray._gtk',
        'pystray._util.xorg',
    ]
elif sys.platform.startswith('darwin'):
    hiddenimports += [
        'pystray._darwin',
        'pystray._util.darwin',
    ]

# Ensure PIL is included (required by pystray)
hiddenimports += [
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
]
