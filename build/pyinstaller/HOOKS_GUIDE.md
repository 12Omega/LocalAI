# PyInstaller Hooks Implementation Guide

## Overview

This document explains the PyInstaller hooks implementation for the Local AI Development Environment Desktop GUI Application. It covers what hooks are, why they're needed, and how they integrate with the build process.

**Requirements Addressed**: 8.3 - Bundle Eel framework HTML/CSS/JS files and modules with data files

## What Are PyInstaller Hooks?

PyInstaller hooks are Python modules that provide PyInstaller with additional information about how to package specific third-party libraries. They solve three main problems:

1. **Hidden Imports**: Modules imported dynamically (e.g., via `__import__()` or plugin systems) that PyInstaller can't detect through static analysis
2. **Data Files**: Non-Python files (templates, images, config files) that need to be bundled
3. **Binary Libraries**: Compiled extensions (.so, .dll, .dylib) that are loaded at runtime

Without hooks, these files would be missing from the executable, causing runtime errors.

## Hook Directory Structure

```
build/pyinstaller/
├── local-ai-dev.spec          # Main PyInstaller spec file
└── hooks/                      # Custom hooks directory
    ├── README.md               # Hook documentation
    ├── hook-eel.py             # Eel framework hook
    ├── hook-tree_sitter.py     # Tree-sitter parsers hook
    ├── hook-PIL.py             # Pillow/PIL hook
    ├── hook-pystray.py         # System tray hook
    ├── hook-cryptography.py    # Cryptography library hook
    ├── hook-watchdog.py        # File monitoring hook
    ├── hook-yaml.py            # YAML parser hook
    └── hook-lxml.py            # XML/HTML parser hook
```

## Integration with Spec File

The spec file references the hooks directory:

```python
# Path to custom hooks directory
HOOKS_DIR = os.path.join(SPEC_DIR, 'hooks')

a = Analysis(
    [ENTRY_POINT],
    ...
    hookspath=[HOOKS_DIR],  # PyInstaller will load hooks from this directory
    ...
)
```

When PyInstaller runs, it:
1. Loads all `hook-*.py` files from the hooks directory
2. Executes each hook to collect dependencies
3. Merges the results into the final executable bundle

## Hook Implementation Details

### 1. hook-eel.py - Eel Framework

**Why needed**: Eel uses bottle web server and geventwebsocket, which are loaded dynamically.

**What it collects**:
- All Eel submodules
- Bottle web framework
- WebSocket support (bottle_websocket, geventwebsocket)
- Async support (gevent)

**Key code**:
```python
hiddenimports = collect_submodules('eel')
datas = collect_data_files('eel')
hiddenimports += ['bottle', 'bottle_websocket', 'gevent', 'gevent.pywsgi']
```

### 2. hook-tree_sitter.py - Code Parsers

**Why needed**: Tree-sitter language parsers are binary libraries (.so/.dll/.dylib) loaded dynamically.

**What it collects**:
- Tree-sitter core library
- Binary parser libraries for Python, JavaScript, TypeScript, Java, Go, Rust, C/C++
- Language-specific submodules

**Key code**:
```python
binaries = collect_dynamic_libs('tree_sitter')
for parser in ['tree_sitter_python', 'tree_sitter_javascript', ...]:
    binaries += collect_dynamic_libs(parser)
    datas += collect_data_files(parser)
```

**Platform-specific**: Collects .dll on Windows, .so on Linux, .dylib on macOS.

### 3. hook-PIL.py - Image Processing

**Why needed**: PIL/Pillow has plugin architecture for image formats, loaded dynamically.

**What it collects**:
- All PIL plugins (PngImagePlugin, JpegImagePlugin, etc.)
- Font data files
- Color profile data

**Key code**:
```python
hiddenimports = collect_submodules('PIL')
datas = collect_data_files('PIL')
hiddenimports += ['PIL.Image', 'PIL.ImageDraw', 'PIL.PngImagePlugin', ...]
```

**Used by**: pystray (for system tray icon rendering)

### 4. hook-pystray.py - System Tray

**Why needed**: Pystray has different backends for each OS, selected at runtime.

**What it collects**:
- Platform-specific backends (_win32, _xorg, _darwin)
- PIL dependencies

**Key code**:
```python
if sys.platform.startswith('win'):
    hiddenimports += ['pystray._win32']
elif sys.platform.startswith('linux'):
    hiddenimports += ['pystray._xorg', 'pystray._gtk']
elif sys.platform.startswith('darwin'):
    hiddenimports += ['pystray._darwin']
```

**Related requirement**: 9 (System Tray Integration)

### 5. hook-cryptography.py - Encryption

**Why needed**: Cryptography library has C extensions and multiple backends.

**What it collects**:
- Binary cryptographic extensions
- OpenSSL backend
- Hazmat primitives
- CFFI backend

**Key code**:
```python
binaries = collect_dynamic_libs('cryptography')
hiddenimports = collect_submodules('cryptography')
hiddenimports += ['cryptography.fernet', 'cryptography.hazmat', '_cffi_backend']
```

**Related requirements**: 4.11, 14.2 (Encryption of API keys)

### 6. hook-watchdog.py - File Monitoring

**Why needed**: Watchdog uses different file system observers for each OS.

**What it collects**:
- Platform-specific observers (WindowsApi, Inotify, FSEvents)
- Core watchdog modules

**Key code**:
```python
if sys.platform.startswith('win'):
    hiddenimports += ['watchdog.observers.read_directory_changes']
elif sys.platform.startswith('linux'):
    hiddenimports += ['watchdog.observers.inotify']
elif sys.platform.startswith('darwin'):
    hiddenimports += ['watchdog.observers.fsevents']
```

**Related requirement**: 12.3 (Detect external config file changes)

### 7. hook-yaml.py - Configuration Parser

**Why needed**: PyYAML has C extensions that may be missed.

**What it collects**:
- All YAML loaders and dumpers
- C extension (_yaml) if available
- Pure Python fallback modules

**Key code**:
```python
hiddenimports = collect_submodules('yaml')
hiddenimports += ['yaml.loader', 'yaml.dumper', 'yaml.constructor', ...]
try:
    import _yaml
    hiddenimports.append('_yaml')
except ImportError:
    pass  # Will use pure Python version
```

**Related requirements**: 4.6, 12.1 (config.yaml management)

### 8. hook-lxml.py - XML/HTML Parser

**Why needed**: lxml has C extensions (libxml2, libxslt) that need explicit collection.

**What it collects**:
- C extensions for XML/HTML parsing
- Binary libraries (libxml2, libxslt)
- etree, html, and objectify modules

**Key code**:
```python
binaries = collect_dynamic_libs('lxml')
hiddenimports = collect_submodules('lxml')
hiddenimports += ['lxml.etree', 'lxml.html', 'lxml.objectify']
```

**Used by**: Web scraping functionality

## Hook Utilities Reference

PyInstaller provides utility functions for hooks:

### collect_submodules(package_name)
Finds all submodules of a package.
```python
hiddenimports = collect_submodules('mypackage')
# Returns: ['mypackage.module1', 'mypackage.module2', ...]
```

### collect_data_files(package_name)
Finds all non-Python files in a package.
```python
datas = collect_data_files('mypackage')
# Returns: [('path/to/file', 'destination'), ...]
```

### collect_dynamic_libs(package_name)
Finds all binary libraries (.so, .dll, .dylib).
```python
binaries = collect_dynamic_libs('mypackage')
# Returns: [('path/to/lib.so', 'destination'), ...]
```

## Testing Hooks

### 1. Build the Executable

```bash
# From project root
pyinstaller build/pyinstaller/local-ai-dev.spec
```

### 2. Test on Clean System

The best test is on a system **without Python installed**:
- Windows: Test on clean VM or use Windows Sandbox
- macOS: Test on different user account without Python
- Linux: Test in Docker container without Python

### 3. Check for Missing Dependencies

Run the executable and watch for errors:
```
ModuleNotFoundError: No module named 'xyz'
```

If this occurs:
1. Add 'xyz' to the appropriate hook's `hiddenimports`
2. Or create a new hook for the package

### 4. Verify Data Files

Check that data files are accessible:
```python
# In your app code, verify files are found
import os
import sys

if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    bundle_dir = sys._MEIPASS
else:
    # Running as script
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

# Check if file exists
file_path = os.path.join(bundle_dir, 'web', 'index.html')
print(f"File exists: {os.path.exists(file_path)}")
```

### 5. Check Executable Size

```bash
# Windows
dir dist\LocalAIDev\LocalAIDev.exe

# Linux/macOS
du -sh dist/LocalAIDev/LocalAIDev
```

Should be under 150MB (Requirement 8.5).

## Troubleshooting

### Problem: Module not found in executable

**Symptoms**: `ModuleNotFoundError` when running executable

**Solutions**:
1. Check if module is imported dynamically
2. Add to hook's `hiddenimports` list
3. Run `pyinstaller --log-level DEBUG` to see what's being collected

### Problem: Data files missing

**Symptoms**: `FileNotFoundError` for templates, images, etc.

**Solutions**:
1. Add to hook using `collect_data_files()`
2. Or explicitly add to spec file's `datas` list
3. Verify files exist in source package

### Problem: Binary library missing

**Symptoms**: `ImportError: DLL load failed` or similar

**Solutions**:
1. Add to hook using `collect_dynamic_libs()`
2. Check if library is platform-specific
3. Ensure library is in package directory

### Problem: Executable too large

**Symptoms**: Executable exceeds 150MB

**Solutions**:
1. Review hook collections - are you collecting too much?
2. Use `include_py_files=False` for binary-only collections
3. Add unnecessary packages to spec file's `excludes` list
4. Consider using `--onefile` mode (slower startup but smaller)

### Problem: Hook not being loaded

**Symptoms**: No effect when adding hook

**Solutions**:
1. Verify hook filename: must be `hook-packagename.py`
2. Check hook directory path in spec file
3. Ensure hook has no syntax errors
4. Run `pyinstaller --log-level DEBUG` to see hook loading

## Best Practices

1. **Minimize Collections**: Only collect what's needed
   ```python
   # Good: Specific modules
   hiddenimports = ['pkg.module1', 'pkg.module2']
   
   # Less ideal: Everything (but sometimes necessary)
   hiddenimports = collect_submodules('pkg')
   ```

2. **Handle Platform Differences**:
   ```python
   import sys
   if sys.platform.startswith('win'):
       hiddenimports += ['pkg.windows_specific']
   ```

3. **Graceful Failures**:
   ```python
   try:
       binaries += collect_dynamic_libs('optional_pkg')
   except Exception:
       pass  # Package not installed, skip it
   ```

4. **Document Requirements**:
   ```python
   """
   Hook for mypackage
   
   Requirements addressed: X.Y (Description)
   Related to: Requirement Z
   """
   ```

5. **Test Incrementally**: Add one hook at a time, test, then add next

## Performance Considerations

Hooks affect:
- **Build time**: More collections = slower builds
- **Executable size**: More files = larger executable
- **Startup time**: More files to extract = slower startup

Balance completeness with efficiency.

## Maintenance

When updating dependencies:
1. Check if new modules need hooks
2. Test executable still works
3. Check for new warnings in PyInstaller output
4. Update hooks if API changes

## References

- [PyInstaller Documentation](https://pyinstaller.org/)
- [PyInstaller Hooks](https://pyinstaller.org/en/stable/hooks.html)
- [When Things Go Wrong](https://pyinstaller.org/en/stable/when-things-go-wrong.html)
- [Hook Utilities API](https://pyinstaller.org/en/stable/hooks.html#hook-configuration-options)

## Summary

This hooks implementation ensures that the Desktop GUI Application:
- ✅ Bundles all Eel framework dependencies (Requirement 8.3)
- ✅ Includes tree-sitter language parsers
- ✅ Supports system tray integration (Requirement 9)
- ✅ Includes encryption capabilities (Requirements 4.11, 14.2)
- ✅ Supports config file monitoring (Requirement 12.3)
- ✅ Handles image processing for icons
- ✅ Parses YAML configuration files
- ✅ Supports web scraping functionality

The hooks are platform-aware and gracefully handle optional dependencies, ensuring the executable works correctly on Windows, macOS, and Linux.
