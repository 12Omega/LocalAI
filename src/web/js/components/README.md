# GUI Components

This directory contains the JavaScript components for the Desktop GUI Application.

## Task Input Panel (`task_input.js`)

The Task Input Panel component manages user input for task descriptions and controls task execution.

### Features

- **Character Counting**: Real-time character count with 5000 character limit
- **Input Validation**: Ensures task description is non-empty before enabling run button
- **Run/Stop Controls**: Toggle between run and stop buttons based on task state
- **Status Indicators**: Display task status (idle, running, success, error, cancelled)
- **Keyboard Shortcuts**: Ctrl+Enter (Cmd+Enter on macOS) to run task
- **State Management**: Integrates with global state manager for reactive updates
- **Error Handling**: Graceful error handling with user-friendly messages

### Usage

The component is automatically initialized by `main.js` when the application starts:

```javascript
// Component is initialized in main.js
if (typeof taskInputPanel !== 'undefined' && taskInputPanel.init) {
    taskInputPanel.init();
}
```

### API

#### Methods

- `init()` - Initialize the component and attach event listeners
- `handleRunClick()` - Start task execution via Eel backend
- `handleStopClick()` - Cancel running task
- `setTaskDescription(description)` - Set the task description text
- `getTaskDescription()` - Get the current task description
- `clearTaskDescription()` - Clear the task description
- `setRunningState(isRunning)` - Update UI based on running state
- `setStatus(type, message)` - Update status indicator
- `focus()` - Focus on the task input textarea
- `destroy()` - Clean up and remove event listeners

#### Callbacks (called from Python via Eel)

- `eel_task_completed(result)` - Called when task completes successfully
- `eel_task_error(error)` - Called when task encounters an error

### Requirements Satisfied

This component implements the following requirements from the specification:

- **Requirement 2.1**: Multi-line text area accepting 5000 characters
- **Requirement 2.2**: Character count indicator
- **Requirement 2.3**: Run button enabled when text is entered
- **Requirement 2.4**: Run button disabled when text area is empty
- **Requirement 2.5**: Task description passed to backend via Eel
- **Requirement 2.6**: Run button disabled with "Running..." status during execution
- **Requirement 2.7**: Run button re-enabled after task completion
- **Requirement 2.8**: Stop button to cancel running tasks
- **Requirement 2.9**: Task termination via backend

### Testing

Unit tests are available in `/tests/test_task_input_panel.html`. Open this file in a browser to run the tests:

```bash
# Open in browser (adjust path as needed)
open tests/test_task_input_panel.html
# or
firefox tests/test_task_input_panel.html
# or
chrome tests/test_task_input_panel.html
```

### Integration

The component integrates with:

1. **State Manager** (`state.js`): Subscribes to `isTaskRunning` state changes
2. **Eel Backend** (`gui_app.py`): Calls `eel.run_task()` and `eel.stop_task()`
3. **Progress Display Component**: Emits events that progress display listens to
4. **Main Application** (`main.js`): Initialized during app startup

### Event Flow

```
User enters text
    ↓
Character counter updates
    ↓
Input validation runs
    ↓
Run button enabled/disabled
    ↓
User clicks Run
    ↓
Component calls eel.run_task(description)
    ↓
Backend starts task execution
    ↓
Progress updates streamed to UI
    ↓
Task completes or errors
    ↓
Component receives callback (eel_task_completed or eel_task_error)
    ↓
UI updated to idle state
```

## Future Components

The following components are planned but not yet implemented:

- **Progress Display** (`progress_display.js`) - Real-time output and progress messages
- **Settings Manager** (`settings.js`) - Configuration management
- **History View** (`history.js`) - Task history display and management

