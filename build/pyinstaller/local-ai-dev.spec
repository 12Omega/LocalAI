# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Specification File for Local AI Development Environment Desktop GUI Application

This spec file configures PyInstaller to create standalone executables for Windows, macOS, and Linux.

Requirements implemented:
- 8.1: Create standalone executable for Windows (exe), macOS (app), and Linux (AppImage or binary)
- 8.2: Bundle all Python dependencies within the executable
- 8.3: Bundle Eel framework HTML/CSS/JS files within the executable
- 8.4: Executable runs on systems without Python installation
- 7.4: Embed Icon_Asset in the executable

Target executable size: <150MB (Requirement 8.5)

Usage:
    Windows: pyinstaller build/pyinstaller/local-ai-dev.spec
    macOS: pyinstaller build/pyinstaller/local-ai-dev.spec
    Linux: pyinstaller build/pyinstaller/local-ai-dev.spec
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================

# Application metadata
APP_NAME = 'LocalAIDev'
APP_VERSION = '1.0.0'
APP_DESCRIPTION = 'Local AI Development Environment - Desktop GUI'
APP_AUTHOR = 'Local AI Dev Team'

# Determine platform
IS_WINDOWS = sys.platform.startswith('win')
IS_MAC = sys.platform.startswith('darwin')
IS_LINUX = sys.platform.startswith('linux')

# Project paths (relative to spec file location)
SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))
PROJECT_ROOT = os.path.abspath(os.path.join(SPEC_DIR, '..', '..'))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
WEB_DIR = os.path.join(SRC_DIR, 'web')
ASSETS_DIR = os.path.join(WEB_DIR, 'assets')

# Entry point
ENTRY_POINT = os.path.join(SRC_DIR, 'gui', 'gui_app.py')

# Icon paths (platform-specific)
if IS_WINDOWS:
    ICON_PATH = os.path.join(ASSETS_DIR, 'icon.ico')
elif IS_MAC:
    ICON_PATH = os.path.join(ASSETS_DIR, 'icon.icns')
else:  # Linux
    ICON_PATH = os.path.join(ASSETS_DIR, 'icon-256x256.png')

# ============================================================================
# Data Files and Resources
# ============================================================================

# Web files (HTML, CSS, JavaScript, assets) - Requirement 8.3
web_datas = []

# Add entire web directory
web_datas.append((WEB_DIR, 'web'))

# Explicitly include all web subdirectories
web_datas.append((os.path.join(WEB_DIR, 'css'), 'web/css'))
web_datas.append((os.path.join(WEB_DIR, 'js'), 'web/js'))
web_datas.append((os.path.join(ASSETS_DIR), 'web/assets'))
web_datas.append((os.path.join(WEB_DIR, 'index.html'), 'web'))

# Include example configuration file
config_example = os.path.join(PROJECT_ROOT, 'config.example.yaml')
if os.path.exists(config_example):
    web_datas.append((config_example, '.'))

# Include documentation files
docs_dir = os.path.join(PROJECT_ROOT, 'docs')
if os.path.exists(docs_dir):
    web_datas.append((docs_dir, 'docs'))

# ============================================================================
# Hidden Imports - Requirement 8.6
# ============================================================================

# These modules are imported dynamically and PyInstaller may miss them
hidden_imports = [
    # Core modules
    'src.core.config',
    'src.core.llm_interface',
    'src.core.task_executor',
    'src.core.error_handler',
    'src.core.models',
    
    # Agent modules
    'src.agents.code_agent',
    'src.agents.command_executor',
    'src.agents.file_operations',
    'src.agents.code_search',
    
    # Context modules
    'src.context.context_manager',
    'src.context.ast_parser',
    
    # GUI modules
    'src.gui.gui_task_manager',
    'src.gui.gui_config_manager',
    'src.gui.gui_history_manager',
    'src.gui.crash_logger',
    
    # Web research module
    'src.web.web_research',
    
    # Eel framework
    'eel',
    'bottle',  # Eel uses bottle for web server
    'bottle_websocket',  # WebSocket support for Eel
    'gevent',  # Eel async support
    'gevent.pywsgi',
    
    # PyYAML
    'yaml',
    'yaml.loader',
    'yaml.dumper',
    
    # Requests and web scraping
    'requests',
    'urllib3',
    'bs4',
    'beautifulsoup4',
    'lxml',
    'lxml.html',
    'lxml.etree',
    
    # Cryptography
    'cryptography',
    'cryptography.fernet',
    'cryptography.hazmat',
    'cryptography.hazmat.primitives',
    'cryptography.hazmat.primitives.ciphers',
    'cryptography.hazmat.backends',
    
    # Watchdog (file monitoring)
    'watchdog',
    'watchdog.observers',
    'watchdog.events',
    
    # System tray
    'pystray',
    'pystray._win32' if IS_WINDOWS else 'pystray._xorg' if IS_LINUX else 'pystray._darwin',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    
    # Tree-sitter (code parsing)
    'tree_sitter',
    'tree_sitter_python',
    'tree_sitter_javascript',
    'tree_sitter_typescript',
    'tree_sitter_java',
    'tree_sitter_go',
    'tree_sitter_rust',
    'tree_sitter_cpp',
    
    # Testing frameworks (may be used by self-improvement)
    'pytest',
    'hypothesis',
    'hypothesis.strategies',
    
    # Standard library modules that may be missed
    'sqlite3',
    'json',
    'threading',
    'queue',
    'tkinter',  # For file dialogs
    'tkinter.filedialog',
    'webbrowser',
    'subprocess',
    'pathlib',
    'datetime',
    'uuid',
    'hashlib',
    'base64',
    'logging',
    'logging.handlers',
    'traceback',
    'platform',
]

# Collect all submodules from key packages
hidden_imports.extend(collect_submodules('eel'))
hidden_imports.extend(collect_submodules('cryptography'))
hidden_imports.extend(collect_submodules('yaml'))

# ============================================================================
# Binary Dependencies
# ============================================================================

# Collect binary files from dependencies
binaries = []

# Tree-sitter language libraries (.so/.dll files)
binaries.extend(collect_data_files('tree_sitter', include_py_files=False))
binaries.extend(collect_data_files('tree_sitter_python', include_py_files=False))
binaries.extend(collect_data_files('tree_sitter_javascript', include_py_files=False))
binaries.extend(collect_data_files('tree_sitter_typescript', include_py_files=False))
binaries.extend(collect_data_files('tree_sitter_java', include_py_files=False))
binaries.extend(collect_data_files('tree_sitter_go', include_py_files=False))
binaries.extend(collect_data_files('tree_sitter_rust', include_py_files=False))
binaries.extend(collect_data_files('tree_sitter_cpp', include_py_files=False))

# ============================================================================
# Analysis Configuration
# ============================================================================

# Hooks directory for custom PyInstaller hooks
HOOKS_DIR = os.path.join(SPEC_DIR, 'hooks')

a = Analysis(
    [ENTRY_POINT],
    pathex=[PROJECT_ROOT, SRC_DIR],
    binaries=binaries,
    datas=web_datas,
    hiddenimports=hidden_imports,
    hookspath=[HOOKS_DIR],  # Use custom hooks from build/pyinstaller/hooks/
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'tk',  # Exclude tkinter if not needed (keep for file dialogs)
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,  # No bytecode encryption (slows startup)
    noarchive=False,
)

# ============================================================================
# PYZ Archive (Python bytecode)
# ============================================================================

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None
)

# ============================================================================
# Executable Configuration
# ============================================================================

exe = EXE(
    pyz,
    a.scripts,
    [],  # Empty - using COLLECT for one-folder bundle
    exclude_binaries=True,  # Use COLLECT
    name=APP_NAME,
    debug=False,  # Set to True for debugging
    bootloader_ignore_signals=False,
    strip=False,  # Don't strip symbols (better error reports)
    upx=True,  # Compress with UPX (reduces size significantly)
    upx_exclude=[],
    console=False,  # No console window (GUI application)
    disable_windowed_traceback=False,
    argv_emulation=False,  # macOS compatibility
    target_arch=None,
    codesign_identity=None,  # Set for code signing
    entitlements_file=None,
    icon=ICON_PATH,  # Application icon - Requirement 7.4
    version_file=None,  # Windows version info (can be added)
)

# ============================================================================
# Collect Files (One-folder bundle)
# ============================================================================

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)

# ============================================================================
# macOS Bundle Configuration
# ============================================================================

if IS_MAC:
    app = BUNDLE(
        coll,
        name=f'{APP_NAME}.app',
        icon=ICON_PATH,
        bundle_identifier=f'com.localaidev.{APP_NAME.lower()}',
        version=APP_VERSION,
        info_plist={
            'CFBundleName': APP_NAME,
            'CFBundleDisplayName': 'Local AI Development Environment',
            'CFBundleVersion': APP_VERSION,
            'CFBundleShortVersionString': APP_VERSION,
            'CFBundleIdentifier': f'com.localaidev.{APP_NAME.lower()}',
            'CFBundleExecutable': APP_NAME,
            'CFBundleIconFile': 'icon.icns',
            'NSHighResolutionCapable': 'True',
            'NSRequiresAquaSystemAppearance': 'False',  # Support dark mode
            'LSMinimumSystemVersion': '10.14.0',  # Requirement 15.2 (macOS 10.14 Mojave)
            'NSHumanReadableCopyright': f'Copyright © 2024 {APP_AUTHOR}',
        },
    )

# ============================================================================
# Notes and Recommendations
# ============================================================================

"""
Build Instructions:

1. Install dependencies:
   pip install -r requirements.txt
   pip install -r requirements-gui.txt

2. Build executable:
   pyinstaller build/pyinstaller/local-ai-dev.spec

3. Find output in:
   - dist/LocalAIDev/ (one-folder bundle)
   - dist/LocalAIDev.app/ (macOS only)

Platform-Specific Notes:

Windows:
- Output: dist/LocalAIDev/LocalAIDev.exe
- Icon: icon.ico is embedded in the executable
- Consider creating installer with Inno Setup or NSIS

macOS:
- Output: dist/LocalAIDev.app
- Icon: icon.icns is embedded in the app bundle
- Consider code signing: codesign --deep --force --sign "Developer ID" dist/LocalAIDev.app
- Create DMG for distribution: hdiutil create -volname "Local AI Dev" -srcfolder dist/LocalAIDev.app -ov -format UDZO LocalAIDev.dmg

Linux:
- Output: dist/LocalAIDev/LocalAIDev
- Icon: icon-256x256.png (used by desktop entry)
- Create AppImage for distribution (requires additional tools)
- Create .desktop file for menu integration

Size Optimization:

Current configuration should produce executables around 80-120MB (compressed with UPX).
If size exceeds 150MB (Requirement 8.5):
- Add more modules to excludes list
- Remove unused tree-sitter language parsers
- Consider using PyInstaller's --onefile mode (slower startup but single file)
- Review binaries and datas for unnecessary inclusions

Testing:

1. Test on clean system without Python installed (Requirement 8.4)
2. Verify all GUI features work in packaged version
3. Test file dialogs, configuration saving, task execution
4. Check that web files are accessible (HTML/CSS/JS)
5. Verify icons appear correctly in taskbar and window
6. Test on minimum OS versions (Windows 10, macOS 10.14, Linux with GTK 3.0)

Troubleshooting:

- If modules are missing, add them to hidden_imports
- If data files are missing, add them to web_datas
- If app fails to start, run with --debug flag in EXE section
- Check console output even with console=False by redirecting stderr
- Use PyInstaller's --log-level DEBUG for build issues

Code Signing (for production):

Windows:
- Use SignTool.exe with code signing certificate
- signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist/LocalAIDev/LocalAIDev.exe

macOS:
- Use codesign with Apple Developer certificate
- codesign --deep --force --sign "Developer ID Application: Your Name" dist/LocalAIDev.app
- Notarize with Apple: xcrun altool --notarize-app

Linux:
- No standard code signing for binaries
- Consider PGP signature of AppImage for distribution verification
"""
