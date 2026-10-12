# PyInstaller Hooks Directory

This directory contains custom PyInstaller hooks that help PyInstaller correctly bundle all necessary dependencies for the Local AI Development Environment Desktop GUI Application.

## What are PyInstaller Hooks?

PyInstaller hooks are Python files that tell PyInstaller how to handle specific packages. They specify:
- Hidden imports (modules that are imported dynamically)
- Data files that need to be bundled (templates, icons, etc.)
- Binary files (.so, .dll, .dylib) that need to be included

## Available Hooks

### hook-eel.py
**Purpose**: Bundle Eel framework dependencies

**What it does**:
- Collects all Eel submodules
- Includes bottle web server framework
- Includes bottle_websocket for WebSocket support
- Includes gevent for async support
- Bundles Eel's internal template files

**Requirements addressed**: 8.3 (Bundle Eel framework HTML/CSS/JS files)

---

### hook-tree_sitter.py
**Purpose**: Bundle tree-sitter language parser binaries

**What it does**:
- Collects tree-sitter core library
- Includes binary parser libraries (.so/.dll/.dylib) for each language:
  - Python
  - JavaScript/TypeScript
  - Java
  - Go
  - Rust
  - C/C++
  - C#, Ruby, PHP (if installed)
- Handles platform-specific binary formats

**Requirements addressed**: 8.3 (Bundle modules with data files)

---

### hook-PIL.py
**Purpose**: Bundle Pillow (PIL) image processing library

**What it does**:
- Collects all PIL image format plugins
- Includes font data files
- Includes color profile data
- Ensures common image formats are supported (PNG, JPEG, GIF, ICO, BMP)

**Requirements addressed**: 8.3 (Bundle modules with data files)

**Used by**: pystray (system tray icon), icon generation

---

### hook-pystray.py
**Purpose**: Bundle pystray system tray library

**What it does**:
- Includes platform-specific backends:
  - Windows: _win32
  - Linux: _xorg, _gtk
  - macOS: _darwin
- Ensures PIL dependencies are included

**Requirements addressed**: 8.3, Requirement 9 (System tray integration)

---

### hook-cryptography.py
**Purpose**: Bundle cryptography library

**What it does**:
- Collects binary cryptographic extensions
- Includes OpenSSL backend
- Includes Fernet encryption module
- Includes hazmat primitives
- Bundles _cffi_backend dependency

**Requirements addressed**: 8.3, Requirements 4.11, 14.2 (Encryption of sensitive values)

---

### hook-watchdog.py
**Purpose**: Bundle watchdog file monitoring library

**What it does**:
- Includes platform-specific file observers:
  - Windows: WindowsApiObserver
  - Linux: InotifyObserver
  - macOS: FSEventsObserver, KqueueObserver
- Ensures real-time file change detection works

**Requirements addressed**: 8.3, Requirement 12.3 (Detect external config file changes)

---

### hook-yaml.py
**Purpose**: Bundle PyYAML configuration parser

**What it does**:
- Collects all YAML loaders and dumpers
- Includes C extensions for performance (if available)
- Falls back to pure Python implementation if C extension not available

**Requirements addressed**: 8.3, Requirements 4.6, 12.1 (config.yaml file management)

---

### hook-lxml.py
**Purpose**: Bundle lxml XML/HTML parser

**What it does**:
- Collects C extensions for XML/HTML parsing
- Includes libxml2 and libxslt binary libraries
- Bundles etree, html, and objectify modules

**Requirements addressed**: 8.3 (Bundle modules with data files)

**Used by**: Web scraping functionality

---

## How Hooks Are Used

The PyInstaller spec file (`local-ai-dev.spec`) references this directory:

```python
HOOKS_DIR = os.path.join(SPEC_DIR, 'hooks')

a = Analysis(
    ...,
    hookspath=[HOOKS_DIR],
    ...
)
```

When PyInstaller builds the executable, it automatically runs these hooks to collect all necessary files.

## Testing Hooks

After adding or modifying hooks, test by:

1. **Build the executable**:
   ```bash
   pyinstaller build/pyinstaller/local-ai-dev.spec
   ```

2. **Test on a clean system** (without Python installed):
   - Run the executable
   - Test all features that use the hooked module
   - Check for missing module errors in logs

3. **Check executable size**:
   - Should be under 150MB (Requirement 8.5)
   - If too large, review what files are being bundled

## Troubleshooting

### Module Not Found Error
If you get "ModuleNotFoundError" when running the executable:
1. Add the missing module to the appropriate hook's `hiddenimports` list
2. Or create a new hook file if it's a new dependency

### Data Files Missing
If data files (icons, templates, etc.) are missing:
1. Add them using `collect_data_files()` in the appropriate hook
2. Verify the files exist in the package directory

### Binary Library Missing
If .so/.dll/.dylib files are missing:
1. Add them using `collect_dynamic_libs()` in the appropriate hook
2. Check platform-specific paths

### Executable Size Too Large
If the executable exceeds 150MB:
1. Review what's being collected by each hook
2. Use `include_py_files=False` for binary-only collections
3. Add unnecessary modules to the `excludes` list in the spec file

## Adding New Hooks

To add a hook for a new package:

1. **Create hook file**: `hook-packagename.py`
2. **Import utilities**:
   ```python
   from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs
   ```
3. **Collect dependencies**:
   ```python
   hiddenimports = collect_submodules('packagename')
   datas = collect_data_files('packagename')
   binaries = collect_dynamic_libs('packagename')
   ```
4. **Test the hook**
5. **Document it** in this README

## References

- [PyInstaller Hooks Documentation](https://pyinstaller.org/en/stable/hooks.html)
- [PyInstaller Hook Utilities API](https://pyinstaller.org/en/stable/hooks.html#hook-configuration-options)
- [Writing Custom Hooks](https://pyinstaller.org/en/stable/when-things-go-wrong.html#helping-pyinstaller-find-modules)
