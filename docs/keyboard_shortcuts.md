# Keyboard Shortcuts Documentation

## Desktop GUI Application Keyboard Shortcuts

The Local AI Development Environment Desktop GUI supports the following keyboard shortcuts for efficient navigation and control.

### Task Execution

| Shortcut | macOS | Windows/Linux | Action |
|----------|-------|---------------|--------|
| Run Task | `Cmd + Enter` | `Ctrl + Enter` | Execute the task in the input field |
| Stop Task | `Esc` | `Esc` | Stop the currently running task |

### Navigation

| Shortcut | macOS | Windows/Linux | Action |
|----------|-------|---------------|--------|
| Task View | `Cmd + 1` | `Ctrl + 1` | Switch to Task view |
| History View | `Cmd + 2` | `Ctrl + 2` | Switch to History view |
| Settings View | `Cmd + 3` | `Ctrl + 3` | Switch to Settings view |
| Open History | `Cmd + H` | `Ctrl + H` | Navigate to History view |
| Open Settings | `Cmd + ,` | `Ctrl + ,` | Navigate to Settings view |

### Output Management

| Shortcut | macOS | Windows/Linux | Action |
|----------|-------|---------------|--------|
| Copy Output | `Cmd + C` | `Ctrl + C` | Copy progress output to clipboard (when in Task view) |

### Dialog Management

| Shortcut | macOS | Windows/Linux | Action |
|----------|-------|---------------|--------|
| Close Dialog | `Esc` | `Esc` | Close the currently open dialog |

## Implementation Details

### Cross-Platform Support

All keyboard shortcuts are implemented with cross-platform support:

- **macOS**: Uses the `metaKey` (Command key)
- **Windows/Linux**: Uses the `ctrlKey` (Control key)

The implementation automatically detects the platform and responds to the appropriate modifier key.

### Smart Context Handling

The keyboard shortcut handler is context-aware:

1. **Text Input Fields**: When typing in text areas or input fields:
   - `Ctrl/Cmd + Enter` still works to run tasks
   - Other navigation shortcuts are disabled to avoid interfering with text input
   - Standard text editing shortcuts (cut, copy, paste) work normally

2. **Dialog Open**: When a dialog is open:
   - `Esc` closes the dialog
   - Other shortcuts may be suspended depending on dialog type

3. **Task View**: When in the Task view:
   - `Ctrl/Cmd + C` copies the output to clipboard
   - Only works if not typing in an input field

### Accessibility

All keyboard shortcuts are:
- Fully accessible via keyboard navigation
- Documented in the application help
- Announced to screen readers when triggered
- Standard conventions matching common desktop applications

## Accessing Help

To view keyboard shortcuts within the application:
1. Press `F1` or access the Help menu
2. Select "Keyboard Shortcuts" from the menu
3. The shortcut reference will be displayed in a dialog

Alternatively, call `window.showKeyboardShortcutsHelp()` from the browser console.

## Technical Implementation

The keyboard shortcut system is implemented in `src/web/js/main.js`:

- **Function**: `setupKeyboardShortcuts()`
- **Event Listener**: Document-level `keydown` event
- **Modifier Detection**: Checks both `e.ctrlKey` and `e.metaKey`
- **Input Field Detection**: Checks `e.target.tagName` for INPUT, TEXTAREA, SELECT
- **Prevent Default**: Prevents browser default behavior for intercepted shortcuts

### Code Example

```javascript
document.addEventListener('keydown', (e) => {
    // Cross-platform modifier key check
    const isModifier = e.ctrlKey || e.metaKey;
    
    // Check if user is typing
    const isInputField = ['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName);
    
    // Handle Ctrl/Cmd + Enter (works in input fields)
    if (isModifier && e.key === 'Enter' && isInputField) {
        e.preventDefault();
        document.getElementById('run-button')?.click();
        return;
    }
    
    // Other shortcuts (don't interfere with typing)
    if (isInputField) return;
    
    if (isModifier) {
        switch (e.key) {
            case '1': navigateToView('task'); break;
            case '2': navigateToView('history'); break;
            case '3': navigateToView('settings'); break;
            // ... other shortcuts
        }
    }
});
```

## Testing

Keyboard shortcuts are validated by automated tests in `tests/gui/test_keyboard_shortcuts.py`:

- ✅ All required shortcuts are implemented
- ✅ Cross-platform modifier keys are supported
- ✅ Input field context detection works correctly
- ✅ All UI elements referenced by shortcuts exist
- ✅ Help documentation is available

Run tests with:
```bash
pytest tests/gui/test_keyboard_shortcuts.py -v
```

## Platform-Specific Notes

### macOS Specifics

- All shortcuts use `Cmd` (Command key) instead of `Ctrl`
- `Cmd + ,` (Settings) follows macOS convention
- System menu bar integrated when available
- Shortcuts announced via VoiceOver screen reader

### Windows/Linux Specifics

- All shortcuts use `Ctrl` (Control key)
- `Ctrl + ,` (Settings) follows cross-platform convention
- Application menu within window
- Shortcuts compatible with standard screen readers (NVDA, JAWS, Orca)

## Best Practices

### For Efficiency

1. **Learn the View Shortcuts**: `Ctrl/Cmd + 1/2/3` for quick navigation
2. **Use Run Shortcut**: `Ctrl/Cmd + Enter` is faster than clicking
3. **Master History**: `Ctrl/Cmd + H` to quickly review past tasks
4. **Copy Output**: `Ctrl/Cmd + C` when you need to share results

### For Accessibility

- All shortcuts work with screen readers
- Tab navigation available as alternative
- Focus indicators show current element
- Keyboard-only operation is fully supported

## Requirements Traceability

This implementation satisfies **Requirement 6.7** from the Desktop GUI Application requirements:

> THE Desktop_Application SHALL provide keyboard shortcuts for common actions (Ctrl+Enter to run, Ctrl+, for settings)

All required shortcuts are implemented:
- ✅ Ctrl+Enter / Cmd+Enter for run task
- ✅ Ctrl+, / Cmd+, for settings
- ✅ Ctrl+H / Cmd+H for history view
- ✅ Ctrl+1/2/3 for view switching
- ✅ Esc for dialog close
- ✅ Ctrl+C for copy output

## Future Enhancements

Potential future keyboard shortcuts to consider:

- `Ctrl/Cmd + N`: New task (clear task input)
- `Ctrl/Cmd + S`: Save settings
- `Ctrl/Cmd + R`: Re-run last task
- `Ctrl/Cmd + F`: Focus search in History view
- `Ctrl/Cmd + K`: Open command palette
- `F11`: Toggle fullscreen mode
- `Ctrl/Cmd + /`: Show keyboard shortcuts help

---

**Last Updated**: 2024-01-15  
**Version**: 1.0.0  
**Related Documentation**: [User Guide](user_guide.md) | [Configuration](configuration.md)
