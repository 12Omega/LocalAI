# Accessibility Testing Checklist

## Quick Verification Tests for Task 10.2

This checklist helps verify that all accessibility features are working correctly.

## 1. Keyboard Navigation Tests

### Skip Link Test
- [ ] **Load the page and press Tab once**
  - Expected: Skip link appears with "Skip to main content" text
  - Expected: Link has visible focus indicator (blue outline)
- [ ] **Press Enter on the skip link**
  - Expected: Focus jumps to main content area

### Tab Navigation Test
- [ ] **Press Tab repeatedly through the entire page**
  - Expected: All interactive elements receive visible focus
  - Expected: Focus order is logical (left-to-right, top-to-bottom)
  - Expected: No keyboard traps (you can always tab forward/backward)

### Focus Indicators Test
- [ ] **Tab through buttons**
  - Expected: 2px blue outline with subtle shadow
  - Expected: Slight upward transform effect
- [ ] **Tab through form inputs**
  - Expected: 2px blue outline with blue border
  - Expected: Subtle shadow around input
- [ ] **Tab through navigation tabs**
  - Expected: Blue outline with bottom border accent
- [ ] **Tab through history entries (if visible)**
  - Expected: Blue outline with light blue background

### Keyboard Shortcuts Test
- [ ] **In task input, type some text and press Ctrl+Enter** (Cmd+Enter on Mac)
  - Expected: Task starts running (if backend is connected)
- [ ] **Press Alt+1** (or Cmd+1 on Mac)
  - Expected: Switches to Task view
- [ ] **Press Alt+2**
  - Expected: Switches to History view
- [ ] **Press Alt+3**
  - Expected: Switches to Settings view

## 2. Screen Reader Tests

### Setup
Test with one of these screen readers:
- **Windows**: NVDA (free) or JAWS (commercial) or Narrator (built-in)
- **macOS**: VoiceOver (built-in, press Cmd+F5 to enable)
- **Linux**: Orca (free)

### Screen Reader Announcements Test
- [ ] **Start a task (if backend connected)**
  - Expected: "Task is now running" announced
- [ ] **Wait for task to complete**
  - Expected: "Task completed successfully" announced with duration
- [ ] **Stop a running task**
  - Expected: "Task was cancelled" announced
- [ ] **If task fails**
  - Expected: "Task failed" announced with error message (assertive priority)
- [ ] **Clear output**
  - Expected: "Output cleared" announced
- [ ] **Copy output**
  - Expected: "Output copied to clipboard" announced
- [ ] **Switch between views using tabs**
  - Expected: "Switched to [view name] view" announced
- [ ] **In Settings, save configuration**
  - Expected: "Settings saved successfully" announced
- [ ] **In Settings, trigger a validation error**
  - Expected: Error message announced immediately (assertive)
- [ ] **In History, delete an entry**
  - Expected: "History entry deleted" announced
- [ ] **In History, clear all entries**
  - Expected: "All history cleared" announced

### ARIA Labels Test
- [ ] **Navigate to all buttons with screen reader**
  - Expected: Each button announces its purpose
  - Examples: "Run task", "Stop task", "Clear output", "Copy output"
- [ ] **Navigate to all form inputs with screen reader**
  - Expected: Each input announces its label and current value
  - Expected: Required fields announce "required"
  - Expected: Invalid fields announce "invalid" with error message
- [ ] **Navigate to status badges**
  - Expected: Status is announced (Idle, Running, Success, Error, etc.)

## 3. Color and Contrast Tests

### Visual Inspection
- [ ] **Check all text**
  - Expected: All text is easily readable
  - Expected: No color-only information (icons/labels supplement)
- [ ] **Check status indicators**
  - Expected: Each status has unique icon AND color
  - Expected: Success = green, Error = red, Warning = yellow, Info = blue

### Automated Test (Optional)
Use browser tools:
1. Open Chrome/Edge DevTools (F12)
2. Go to Lighthouse tab
3. Click "Generate report" with "Accessibility" checked
4. Look for "Background and foreground colors must have sufficient contrast ratio"

Or use browser extensions:
- **axe DevTools** (free)
- **WAVE** (free)

## 4. Mouse-Free Operation Test

### Complete Task Flow (Keyboard Only)
- [ ] **Open the application**
- [ ] **Press Tab to reach task input**
- [ ] **Type a task description**
- [ ] **Press Ctrl+Enter to run** (if backend connected)
- [ ] **Tab to Progress Display controls**
- [ ] **Use Space/Enter to activate Copy or Clear buttons**
- [ ] **Press Alt+2 to switch to History view**
- [ ] **Tab through history entries**
- [ ] **Press Enter on an entry to view details**
- [ ] **Tab to action buttons and use them**
- [ ] **Press Alt+3 to switch to Settings**
- [ ] **Tab through all form fields**
- [ ] **Make changes and press Tab to Save button**
- [ ] **Press Enter to save**

Expected: Everything above can be done without touching the mouse

## 5. History Entries Keyboard Test

- [ ] **Navigate to History view**
- [ ] **Press Tab until focus reaches first history entry**
  - Expected: Entry gets visible focus (blue outline, light background)
- [ ] **Press Enter or Space**
  - Expected: Entry details appear
- [ ] **Tab to action buttons (View, Re-run, Delete)**
  - Expected: Each button gets focus and can be activated with Enter/Space
- [ ] **Press Escape or Tab out**
  - Expected: Can exit detail view

## 6. Form Accessibility Test

### Settings Form Test
- [ ] **Tab to each form field**
  - Expected: Label is read before input value
- [ ] **Enter invalid value (e.g., negative number in Max Tokens)**
  - Expected: Error appears below field
  - Expected: Field marked as invalid
  - Expected: Error announced to screen reader
- [ ] **Correct the error**
  - Expected: Error clears
  - Expected: Field no longer marked as invalid
- [ ] **Tab to checkboxes**
  - Expected: Current state (checked/unchecked) is announced
- [ ] **Press Space to toggle checkbox**
  - Expected: Checkbox toggles
  - Expected: New state announced

## 7. Reduced Motion Test (Optional)

### Setup
Enable reduced motion in your OS:
- **Windows 11**: Settings > Accessibility > Visual effects > Animation effects (OFF)
- **macOS**: System Preferences > Accessibility > Display > Reduce motion (ON)
- **Linux**: Depends on desktop environment

### Test
- [ ] **Reload page with reduced motion enabled**
  - Expected: No animations or transitions
  - Expected: All functionality still works
  - Expected: Transitions happen instantly

## 8. High Contrast Test (Optional)

### Setup
Enable high contrast mode:
- **Windows**: Alt+Left Shift+Print Screen
- **macOS**: System Preferences > Accessibility > Display > Increase contrast

### Test
- [ ] **Enable high contrast mode**
  - Expected: All buttons still visible
  - Expected: All text still readable
  - Expected: Borders become more prominent
  - Expected: Active states clearly visible

## 9. Touch Target Size Test

### Mobile/Touch Device (Optional)
- [ ] **View on mobile device or resize browser to mobile width**
- [ ] **Try tapping all buttons**
  - Expected: All buttons are at least 44x44px and easy to tap
  - Expected: No accidental taps on adjacent buttons

## 10. Live Region Test

### Screen Reader Running
- [ ] **Start screen reader**
- [ ] **Start a task** (if backend connected)
  - Expected: Progress updates announced periodically
  - Expected: Not too frequent (batched for performance)
  - Expected: Final status announced when complete

## Pass Criteria

✅ **PASS**: All tests in sections 1-4 must pass
✅ **RECOMMENDED**: Tests in sections 5-6 should pass
✅ **OPTIONAL**: Tests in sections 7-10 are nice-to-have

## Common Issues and Solutions

### Issue: Focus indicators not visible
- **Solution**: Check that `accessibility.css` is loaded
- **Solution**: Verify no custom CSS is overriding focus styles

### Issue: Screen reader announcements not working
- **Solution**: Check that `accessibility.js` is loaded before component files
- **Solution**: Verify screen reader is actually running
- **Solution**: Check browser console for JavaScript errors

### Issue: Tab order is wrong
- **Solution**: Check for elements with `tabindex > 0` (should avoid)
- **Solution**: Verify DOM order matches visual order

### Issue: Skip link not appearing
- **Solution**: Check that CSS for `.skip-link:focus` is present
- **Solution**: Verify link is first element in body

## Automated Testing Tools

### Browser Extensions
1. **axe DevTools** - Comprehensive accessibility testing
2. **WAVE** - Visual feedback of accessibility issues
3. **Lighthouse** - Built into Chrome DevTools

### Command Line Tools
1. **pa11y** - Automated testing in CI/CD
2. **axe-core** - Headless testing

### Online Tools
1. **WebAIM Contrast Checker** - Color contrast testing
2. **WAVE Web Accessibility Evaluation Tool** - Full page analysis

## Reporting Issues

If you find any accessibility issues:
1. Note which test failed
2. Note your browser and version
3. Note your OS and version
4. Note your screen reader (if applicable) and version
5. Describe expected vs. actual behavior
6. Provide screenshots if helpful

## Success Indicators

The implementation is successful if:
- ✅ All keyboard navigation tests pass
- ✅ All screen reader announcements work
- ✅ All focus indicators are clearly visible
- ✅ Color contrast meets WCAG AA standards
- ✅ Complete workflows possible without mouse
- ✅ Form validation errors are accessible
- ✅ Status changes are announced in real-time
- ✅ Tab order is logical throughout the application

## WCAG 2.1 Level AA Compliance

This implementation targets WCAG 2.1 Level AA compliance. Key requirements:
- ✅ 1.4.3 Contrast (Minimum) - 4.5:1 ratio
- ✅ 2.1.1 Keyboard - All functionality via keyboard
- ✅ 2.1.2 No Keyboard Trap - Can always escape
- ✅ 2.4.3 Focus Order - Logical and meaningful
- ✅ 2.4.7 Focus Visible - Visible focus indicator
- ✅ 3.2.4 Consistent Identification - Consistent components
- ✅ 3.3.2 Labels or Instructions - All inputs labeled
- ✅ 4.1.2 Name, Role, Value - Proper ARIA usage
- ✅ 4.1.3 Status Messages - Proper live regions

---

**Last Updated**: Task 10.2 Implementation
**Test Coverage**: Comprehensive accessibility features
**Status**: Ready for testing
