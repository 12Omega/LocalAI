# Error Handling & Help System - Quick Reference

## Error Handling

### JavaScript Error Handler

```javascript
// Import automatically via error_handler.js in index.html

// Handle network errors
window.errorHandler.handleNetworkError(error, { url: 'http://example.com' });

// Handle LLM API errors
window.errorHandler.handleLLMApiError(error, { statusCode: 429 });

// Handle file operation errors
window.errorHandler.handleFileOperationError(error, { path: '/path/to/file', operation: 'read' });

// Handle validation errors
window.errorHandler.handleValidationError('fieldName', 'Invalid value');

// Generic error handling with custom category
window.errorHandler.handleError(
    error,
    window.errorHandler.ErrorCategory.SYSTEM,
    window.errorHandler.ErrorSeverity.ERROR,
    { context: 'additional info' }
);

// Get error statistics
const stats = window.errorHandler.getErrorStatistics();

// Export error log for debugging
const errorLog = window.errorHandler.exportErrorLog();
```

### Python Crash Logger

```python
# Already installed globally in gui_app.py

from src.gui.crash_logger import get_crash_logger

# Get crash logger instance
crash_logger = get_crash_logger()

# Get recent crashes
recent_crashes = crash_logger.get_recent_crashes(limit=10)

# Clear old crash logs
crash_logger.clear_old_crashes(keep_days=30)

# Crash logs are automatically saved to:
# Windows: %LOCALAPPDATA%\LocalAIDev\logs\
# macOS: ~/Library/Logs/LocalAIDev/
# Linux: ~/.local/share/local-ai-dev/logs/
```

## Help System

### Show Help Dialogs

```javascript
// Show help menu
window.showHelpMenu();

// Show user guide
window.showUserGuide();

// Show documentation links
window.showDocumentation();

// Show about dialog
window.showAboutDialog();

// Show keyboard shortcuts
window.showKeyboardShortcutsHelp();

// Show bug report dialog
window.showBugReportDialog();

// Check for updates
window.checkForUpdates();
```

### Add Tooltips to HTML Elements

```html
<!-- Simple tooltip -->
<input type="text" data-tooltip="This is a helpful tooltip">

<!-- With help icon -->
<label>
    Setting Name
    <span class="help-icon" title="Explanation of this setting">??</span>
</label>
```

### Open External Links

```javascript
// From JavaScript (uses Eel to call Python)
eel.open_external('https://github.com')();
eel.open_external('docs/README.md')();
```

```python
# From Python
from src.gui.gui_app import open_external

result = open_external('https://example.com')
# Returns: {'success': True/False, 'message': '...'}
```

## Error Categories

- `ErrorCategory.NETWORK` - Connection issues, timeouts
- `ErrorCategory.LLM_API` - Rate limits, invalid keys, model errors
- `ErrorCategory.FILE_OPERATION` - File not found, permission denied
- `ErrorCategory.VALIDATION` - Input validation failures
- `ErrorCategory.SYSTEM` - Unhandled errors, crashes
- `ErrorCategory.UNKNOWN` - Uncategorized errors

## Error Severity Levels

- `ErrorSeverity.INFO` - Informational messages
- `ErrorSeverity.WARNING` - Warning notifications (toast)
- `ErrorSeverity.ERROR` - Error dialogs
- `ErrorSeverity.CRITICAL` - Critical error dialogs

## CSS Classes for Custom Dialogs

```css
.dialog-overlay[data-type="error"]    /* Red/error theme */
.dialog-overlay[data-type="warning"]  /* Yellow/warning theme */
.dialog-overlay[data-type="success"]  /* Green/success theme */
.dialog-overlay[data-type="info"]     /* Blue/info theme */

.error-message                        /* Formatted error messages */
.toast-notification                   /* Toast notifications */
.toast-warning                        /* Warning toast */
```

## Testing

Run error handling and help system tests:
```bash
python -m pytest tests/unit/test_error_handling_and_help.py -v
```

