# GUI Application - Quick Manual Testing Guide

This guide provides a streamlined approach to manually test the Desktop GUI Application for Task 14 checkpoint completion.

## Prerequisites

1. Ensure all dependencies are installed:
   ```bash
   pip install -r requirements-gui.txt
   ```

2. Ensure you have a valid LLM running locally (e.g., Ollama with llama2 model)

## Quick Start Test (5 minutes)

### 1. Launch Application
```bash
python -m src.gui.gui_app
```

**Check**: Application window opens within 5 seconds ✓

### 2. Basic Task Execution
1. In the Task Input panel, enter: `Create a simple hello world function`
2. Click the **Run** button (or press Ctrl+Enter)
3. Watch the Progress Display for real-time updates

**Check**: 
- Progress messages appear ✓
- Task completes ✓
- Status changes from "Running" to "Completed" ✓

### 3. View History
1. Click the **History** tab (or press Ctrl+H)
2. Verify your task appears in the list

**Check**: History entry shows task description, timestamp, and status ✓

### 4. Theme Switch
1. Click the theme toggle button (🌙/☀️) in the header
2. Observe the color scheme change

**Check**: Application switches between light and dark themes ✓

### 5. Settings
1. Click the **Settings** tab (or press Ctrl+,)
2. View the LLM endpoint configuration
3. Click **Save Settings** (no changes needed)

**Check**: Settings panel loads and displays current configuration ✓

**If all 5 quick tests pass, the core functionality is working!** ✅

---

## Comprehensive Testing (30 minutes)

### Test Suite A: Task Execution Workflow

#### A1: Run Task with Real Output
```
Task: "List all Python files in the src directory"
Expected: Task runs, shows file listing in output
Time: 1 minute
```

#### A2: Stop Running Task
```
1. Enter a long-running task
2. Click Run
3. Click Stop button while running
Expected: Task cancels, status shows "Cancelled"
Time: 30 seconds
```

#### A3: Character Counter
```
1. Type in task input area
2. Watch character counter update
Expected: Shows "X / 5000" and updates in real-time
Time: 15 seconds
```

#### A4: Copy Output
```
1. Run a task that produces output
2. Click the copy button (📋)
3. Paste into notepad
Expected: Output copied to clipboard
Time: 30 seconds
```

#### A5: Clear Output
```
1. Click the clear button (🗑️)
Expected: Output panel clears
Time: 10 seconds
```

### Test Suite B: History Management

#### B1: Search History
```
1. Go to History tab
2. Type in search box: "hello"
Expected: Only entries matching "hello" appear
Time: 30 seconds
```

#### B2: Filter by Status
```
1. Use Status dropdown
2. Select "Success"
Expected: Only successful tasks shown
Time: 20 seconds
```

#### B3: Sort History
```
1. Use Sort dropdown
2. Select "Oldest First"
Expected: List reverses order
Time: 20 seconds
```

#### B4: View Entry Details
```
1. Click on a history entry
2. Details panel slides in
Expected: Shows full description, output, timestamp
Time: 30 seconds
```

#### B5: Re-run Task
```
1. In details panel, click "Re-run Task"
Expected: Task input fills with description, task starts
Time: 30 seconds
```

#### B6: Delete Entry
```
1. In details panel, click "Delete Entry"
2. Confirm deletion
Expected: Entry removed from list
Time: 20 seconds
```

#### B7: Export History
```
1. Click "Export History" button
2. Choose JSON format
Expected: File dialog opens, JSON file created
Time: 30 seconds
```

#### B8: Clear All History
```
1. Click "Clear History" button
2. Confirm
Expected: All entries removed
Time: 20 seconds
```

### Test Suite C: Configuration Management

#### C1: Modify LLM Settings
```
1. Go to Settings
2. Change temperature from 0.7 to 0.8
3. Click Save Settings
Expected: Success message appears
Time: 30 seconds
```

#### C2: Settings Persistence
```
1. Modify a setting and save
2. Close application
3. Reopen application
4. Check settings
Expected: Modified value still there
Time: 1 minute
```

#### C3: Browse Directory
```
1. Find "Project Root" setting
2. Click Browse button
Expected: File dialog opens
Time: 20 seconds
```

#### C4: Invalid Input Validation
```
1. In LLM Endpoint field, type "not-a-url"
2. Click Save
Expected: Error message appears, settings not saved
Time: 30 seconds
```

#### C5: Reset Settings
```
1. Click "Reset to Defaults"
2. Confirm
Expected: All settings revert to defaults
Time: 30 seconds
```

### Test Suite D: Keyboard Shortcuts

Test each shortcut by pressing the keys:

| Shortcut | Expected Action | Time |
|----------|----------------|------|
| Ctrl+Enter | Runs current task | 5s |
| Ctrl+, | Opens Settings | 5s |
| Ctrl+H | Opens History | 5s |
| Ctrl+1 | Switches to Task view | 5s |
| Ctrl+2 | Switches to History view | 5s |
| Ctrl+3 | Switches to Settings view | 5s |
| Esc | Closes detail panel | 5s |
| Ctrl+C | Copies output (when focused) | 5s |

**Total time**: 1 minute

### Test Suite E: Theme and Visual

#### E1: Theme Persistence
```
1. Toggle theme to dark
2. Close and reopen app
Expected: Dark theme still active
Time: 1 minute
```

#### E2: All Components Themed
```
1. Toggle theme
2. Check each tab (Task, History, Settings)
Expected: All panels respect theme colors
Time: 1 minute
```

### Test Suite F: Responsive Design

#### F1: Window Resize
```
1. Resize window to very small (800x600)
2. Resize to very large (1920x1080)
Expected: Layout adapts, no broken UI
Time: 1 minute
```

#### F2: Text Scaling
```
1. Change Windows display scaling to 150%
2. Relaunch application
Expected: UI scales appropriately
Time: 2 minutes
```

### Test Suite G: Error Handling

#### G1: Invalid LLM Endpoint
```
1. Settings > LLM Endpoint > "http://invalid:9999"
2. Save and run a task
Expected: Clear error message about connection
Time: 1 minute
```

#### G2: Network Disconnection
```
1. Stop LLM service
2. Run a task
Expected: User-friendly error message
Time: 1 minute
```

### Test Suite H: Accessibility

#### H1: Keyboard Navigation
```
1. Press Tab repeatedly
2. Navigate through all controls
Expected: Focus indicators visible, all elements reachable
Time: 2 minutes
```

#### H2: Screen Reader
```
1. Enable Windows Narrator (Win+Ctrl+Enter)
2. Navigate application
Expected: Elements announced properly
Time: 3 minutes (if available)
```

### Test Suite I: System Tray (Optional Feature)

#### I1: Minimize to Tray
```
1. Enable "Minimize to Tray" in Settings
2. Close window
Expected: App minimizes to system tray
Time: 30 seconds
```

#### I2: Restore from Tray
```
1. Click tray icon
Expected: Window restores
Time: 10 seconds
```

#### I3: Tray Context Menu
```
1. Right-click tray icon
Expected: Menu with Show, Settings, Exit
Time: 10 seconds
```

#### I4: Running Task Indicator
```
1. Start a task
2. Minimize to tray
Expected: Tray icon shows running indicator
Time: 30 seconds
```

---

## Test Results Template

Copy this template to record your results:

```
## Manual Testing Results - [Date]

### Quick Start Test
- [ ] Application Launch (5 seconds)
- [ ] Basic Task Execution
- [ ] View History
- [ ] Theme Switch
- [ ] Settings Access

### Comprehensive Tests
- [ ] Suite A: Task Execution (5/5 tests)
- [ ] Suite B: History Management (8/8 tests)
- [ ] Suite C: Configuration (5/5 tests)
- [ ] Suite D: Keyboard Shortcuts (8/8 tests)
- [ ] Suite E: Theme and Visual (2/2 tests)
- [ ] Suite F: Responsive Design (2/2 tests)
- [ ] Suite G: Error Handling (2/2 tests)
- [ ] Suite H: Accessibility (2/2 tests)
- [ ] Suite I: System Tray (4/4 tests - optional)

### Issues Found
1. [Describe any issues]
2. [Describe any issues]

### Overall Assessment
- [ ] Ready for release
- [ ] Needs minor fixes
- [ ] Needs major fixes

### Notes
[Any additional observations]
```

---

## Common Issues and Solutions

### Issue: Application won't start
**Solution**: 
1. Check `requirements-gui.txt` dependencies installed
2. Verify Python version ≥ 3.8
3. Check for port conflicts (default Eel port: 8080)

### Issue: Task runs but no output
**Solution**:
1. Check LLM is running (`curl http://localhost:11434`)
2. Verify endpoint in Settings matches LLM location
3. Check console for error messages

### Issue: History not saving
**Solution**:
1. Check SQLite database file permissions
2. Look in `~/.local-ai-dev/history.db`
3. Check crash logs for database errors

### Issue: Theme not persisting
**Solution**:
1. Check browser localStorage support (Eel uses Chrome/Edge)
2. Verify application data directory writable

### Issue: Settings not saving
**Solution**:
1. Check `config.yaml` file permissions
2. Verify config directory exists
3. Look for validation errors in UI

---

## Performance Benchmarks

Expected performance metrics:

| Metric | Target | How to Test |
|--------|--------|-------------|
| Application startup | < 5 seconds | Time from launch to UI ready |
| Task start latency | < 500ms | Time from Run click to first progress update |
| UI responsiveness | < 100ms | Click to visual feedback |
| History load (100 entries) | < 1 second | Open History tab |
| View switching | < 200ms | Tab navigation |
| Memory usage (idle) | < 200MB | Task Manager |
| Memory usage (running) | < 500MB | Task Manager during execution |

---

## Reporting Results

After completing tests, report results by:

1. **Creating an issue** (if problems found):
   - Title: "GUI Test Failed: [Test Name]"
   - Include: Steps to reproduce, expected vs actual behavior, screenshots

2. **Update checkpoint status**:
   - If all tests pass: Mark Task 14 as complete ✓
   - If issues found: List issues and recommended fixes

3. **Document findings**:
   - Save completed test results template
   - Note any performance concerns
   - Suggest improvements

---

## Next Steps After Testing

1. ✅ If all tests pass → Proceed to Task 15 (Executable Packaging)
2. ⚠️ If minor issues → Fix and re-test affected areas
3. ❌ If major issues → Document blockers and prioritize fixes

---

**Quick Reference Commands:**

```bash
# Launch GUI
python -m src.gui.gui_app

# Run automated tests
python test_gui_checkpoint.py

# Check dependencies
pip list | grep -E "(eel|pystray|cryptography)"

# View logs
cat ~/.local-ai-dev/crash_logs/*.log
```

---

**Estimated Testing Time:**
- Quick Start: 5 minutes
- Comprehensive: 30 minutes
- Full accessibility testing: 45 minutes

**Good luck with testing!** 🚀
