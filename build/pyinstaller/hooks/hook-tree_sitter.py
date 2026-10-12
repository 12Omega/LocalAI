# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller hook for tree-sitter and language parsers

This hook ensures that tree-sitter's binary language parser libraries (.so/.dll/.dylib)
are properly bundled with the executable.

Requirements addressed: 8.3 - Bundle modules with data files (binary parsers)

Tree-sitter uses dynamically loaded shared libraries for each language parser:
- Windows: .dll files
- Linux: .so files  
- macOS: .dylib files

This hook collects all binary files from tree_sitter and language-specific packages.
"""

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files, collect_submodules

# Collect tree-sitter core
hiddenimports = collect_submodules('tree_sitter')
datas = collect_data_files('tree_sitter')
binaries = collect_dynamic_libs('tree_sitter')

# List of tree-sitter language parser packages
language_parsers = [
    'tree_sitter_python',
    'tree_sitter_javascript', 
    'tree_sitter_typescript',
    'tree_sitter_java',
    'tree_sitter_go',
    'tree_sitter_rust',
    'tree_sitter_cpp',
    'tree_sitter_c',
    'tree_sitter_c_sharp',
    'tree_sitter_ruby',
    'tree_sitter_php',
]

# Collect binaries and data from each language parser
for parser in language_parsers:
    try:
        # Collect dynamic libraries (.so, .dll, .dylib)
        binaries += collect_dynamic_libs(parser)
        # Collect any data files
        datas += collect_data_files(parser)
        # Collect submodules
        hiddenimports += collect_submodules(parser)
    except Exception:
        # Parser package might not be installed, skip it
        pass
