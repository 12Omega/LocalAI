# Local AI Dev - GUI Release Notes

## Version 1.0.0

### New Features
- Desktop GUI application built with Eel framework
- Task execution with real-time progress display
- Configuration management with GUI settings panel
- Task history with search, filter, and export
- System tray integration (optional)
- Dark/light theme support
- Keyboard shortcuts (Ctrl/Cmd+Enter, Ctrl/Cmd+Comma, etc.)
- First-run setup wizard for LLM endpoint configuration
- Loading indicators and smooth view transitions
- Virtual scrolling for performance with large history lists

### Platform Support
- Windows 10/11: Windows installer (NSIS)
- macOS: .app bundle via PyInstaller
- Linux: .deb package / AppImage

### Installation
See README.md for installation instructions.

### Configuration
The GUI shares config.yaml with the CLI. Both modes are fully compatible.

### Known Limitations
- Requires Python 3.8+ to build from source
- System tray on Linux requires libappindicator
