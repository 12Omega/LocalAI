# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller hook for Pillow (PIL)

This hook ensures that PIL/Pillow image format plugins and data files
are properly bundled with the executable.

Requirements addressed: 8.3 - Bundle modules with data files

Pillow includes:
- Image format plugins (JPEG, PNG, GIF, etc.)
- Font data files
- Color profile data

This hook is particularly important for pystray which uses PIL.Image.
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all PIL/Pillow submodules (plugins)
hiddenimports = collect_submodules('PIL')

# Collect data files (fonts, color profiles, etc.)
datas = collect_data_files('PIL')

# Ensure common image format plugins are included
hiddenimports += [
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'PIL.ImageTk',
    'PIL.PngImagePlugin',
    'PIL.JpegImagePlugin',
    'PIL.GifImagePlugin',
    'PIL.IcoImagePlugin',
    'PIL.BmpImagePlugin',
]
