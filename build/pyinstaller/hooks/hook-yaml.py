# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller hook for PyYAML

This hook ensures that PyYAML's loaders, dumpers, and C extensions
are properly bundled with the executable.

Requirements addressed: 8.3 - Bundle modules with data files
Related to: Requirements 4.6, 12.1 (config.yaml file management)

PyYAML includes:
- Pure Python and C implementations
- Different loaders (safe, full, unsafe)
- Different dumpers

This hook ensures all components are available.
"""

from PyInstaller.utils.hooks import collect_submodules

# Collect all yaml submodules
hiddenimports = collect_submodules('yaml')

# Ensure critical yaml modules are included
hiddenimports += [
    'yaml',
    'yaml.loader',
    'yaml.dumper',
    'yaml.constructor',
    'yaml.representer',
    'yaml.resolver',
    'yaml.parser',
    'yaml.scanner',
    'yaml.composer',
    'yaml.emitter',
    'yaml.serializer',
    'yaml.tokens',
    'yaml.events',
    'yaml.nodes',
    'yaml.error',
]

# Include C extensions if available (for performance)
try:
    import _yaml
    hiddenimports.append('_yaml')
except ImportError:
    # C extension not available, will use pure Python version
    pass
