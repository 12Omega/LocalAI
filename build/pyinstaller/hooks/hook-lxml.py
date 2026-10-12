# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller hook for lxml

This hook ensures that lxml's C extensions and data files are properly bundled.

Requirements addressed: 8.3 - Bundle modules with data files

lxml includes:
- C extensions for XML/HTML parsing (libxml2, libxslt)
- etree and html modules
- objectify module

This hook collects all necessary binaries and submodules.
"""

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules, collect_data_files

# Collect all lxml submodules
hiddenimports = collect_submodules('lxml')

# Collect binary libraries (libxml2, libxslt)
binaries = collect_dynamic_libs('lxml')

# Collect data files
datas = collect_data_files('lxml')

# Ensure critical lxml modules are included
hiddenimports += [
    'lxml.etree',
    'lxml.html',
    'lxml.html.clean',
    'lxml.objectify',
    'lxml._elementpath',
]
