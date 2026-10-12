# Design Document: Desktop GUI Application

## Overview

This document specifies the design of a modern desktop GUI application for the Local AI Development Environment. The application provides a user-friendly graphical interface that wraps the existing CLI functionality, enabling users to interact with the AI development environment through an intuitive interface with real-time feedback, visual progress monitoring, configuration management, and task history tracking.

### Design Goals

1. **Ease of Use**: Non-technical users should be able to use the AI development environment without command-line knowledge
2. **Visual Feedback**: Real-time progress updates and status indicators enhance user understanding
3. **Seamless Integration**: Reuse existing backend code without modification to core logic
4. **Professional Appearance**: Modern, clean UI that users enjoy working with
5. **Cross-Platform**: Consistent experience on Windows, macOS, and Linux
6. **Performance**: Responsive UI that remains interactive during long-running tasks
7. **Maintainability**: Clear separation between GUI layer and business logic

### Technology Choice Rationale

**Eel Framework** was selected for several key reasons:

- **Python Integration**: Seamlessly integrates with existing Python codebase
- **Web Technologies**: Leverages HTML/CSS/JavaScript for UI flexibility and modern design
- **Lightweight**: Minimal overhead compared to Electron or Qt
- **Simple Architecture**: Easy to understand and maintain
- **Cross-Platform**: Works consistently across Windows, macOS, and Linux
- **No Framework Lock-in**: HTML/CSS/JS can be plain or use any frontend framework/library

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Desktop GUI Application                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │           Frontend Layer (HTML/CSS/JavaScript)         │    │
│  │                                                          │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐│    │
│  │  │  Task    │  │ Progress │  │ Settings │  │History ││    │
│  │  │  Input   │  │ Display  │  │ Manager  │  │ View   ││    │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────┘│    │
│  │                                                          │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │           UI State Manager (JavaScript)          │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────┘    │
│                            ▲  │                                  │
│                            │  │ eel.expose()                    │
│                            │  ▼ JavaScript calls Python         │
│  ┌────────────────────────────────────────────────────────┐    │
│  │        Python Bridge Layer (Eel Decorators)            │    │
│  │                                                          │    │
│  │  @eel.expose                     @eel.expose            │    │
│  │  run_task()                      get_config()           │    │
│  │  stop_task()                     save_config()          │    │
│  │  get_history()                   validate_config()      │    │
│  │  ...                             ...                    │    │
│  └────────────────────────────────────────────────────────┘    │
│                            │  ▲                                  │
│                            │  │ Callbacks                        │
│                            ▼  │                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         Backend Integration Layer (Python)             │    │
│  │                                                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │    │
│  │  │GUI Task      │  │GUI Config    │  │GUI History  │  │    │
│  │  │Manager       │  │Manager       │  │Manager      │  │    │
│  │  │(Threading)   │  │              │  │(Persistence)│  │    │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  │    │
│  └────────────────────────────────────────────────────────┘    │
│                            │  ▲                                  │
│                            │  │ No modifications                 │
│                            ▼  │ to existing code                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │            Existing Backend (Unchanged)                │    │
│  │                                                          │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐│    │
│  │  │ Task     │  │ Config   │  │ Code     │  │Context ││    │
│  │  │ Executor │  │ Manager  │  │ Agent    │  │Manager ││    │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────┘│    │
│  │                                                          │    │
│  │  ┌──────────┐  ┌──────────┐                            │    │
│  │  │ LLM      │  │ Web      │                            │    │
│  │  │Interface │  │ Research │                            │    │
│  │  └──────────┘  └──────────┘                            │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              │  ▲
                              │  │
                              ▼  │
                    ┌──────────────────┐
                    │  Local LLM       │
                    │  (User's Machine)│
                    └──────────────────┘
```

### Layer Responsibilities

#### 1. Frontend Layer (HTML/CSS/JavaScript)

**Purpose**: User interface rendering and user interaction handling

**Components**:
- **Task Input Panel**: Text area, run/stop buttons, character counter
- **Progress Display**: Real-time output, colored status messages, scroll control
- **Settings Manager**: Form inputs, validation feedback, file browser dialogs
- **History View**: List rendering, search/filter, export functionality
- **UI State Manager**: Central state management, view routing, theme management

**Technologies**:
- HTML5 for structure
- CSS3 for styling (CSS Grid, Flexbox)
- Vanilla JavaScript (no framework required initially, easily extensible)
- Optional: Consider lightweight libraries like Alpine.js or Preact for state management

**Responsibilities**:
- Render UI components
- Handle user input events
- Call Python functions via Eel
- Update UI based on data received from Python
- Manage client-side state (current view, theme, UI preferences)

#### 2. Python Bridge Layer (Eel Decorators)

**Purpose**: Expose Python functions to JavaScript and handle bidirectional communication

**Key Functions**:
```python
@eel.expose
def run_task(task_description: str) -> dict
    """Start executing a task"""

@eel.expose
def stop_task() -> dict
    """Cancel the currently running task"""

@eel.expose
def get_config() -> dict
    """Retrieve current configuration"""

@eel.expose
def save_config(config_data: dict) -> dict
    """Persist configuration changes"""

@eel.expose
def validate_config_field(field: str, value: any) -> dict
    """Validate a single configuration field"""

@eel.expose
def get_history(limit: int, search_query: str) -> list
    """Retrieve task history with optional filtering"""

@eel.expose
def delete_history_entry(entry_id: str) -> dict
    """Remove a history entry"""

@eel.expose
def export_history(format: str) -> dict
    """Export history to JSON or CSV"""

@eel.expose
def browse_directory(initial_path: str) -> dict
    """Open native file browser dialog"""
```

**Responsibilities**:
- Expose Python functions to JavaScript via `@eel.expose` decorator
- Validate input parameters from JavaScript
- Convert Python data structures to JSON-serializable formats
- Handle exceptions and return structured error responses
- Call JavaScript functions from Python via `eel.functionName()`

#### 3. Backend Integration Layer (Python)

**Purpose**: Coordinate between GUI and existing backend, manage threading, persistence

**Modules**:

**GUI Task Manager** (`gui_task_manager.py`):
- Wraps `TaskExecutor` with threading
- Provides callback mechanism for progress updates
- Manages task lifecycle (start, stop, status)
- Converts backend events to GUI-friendly messages

**GUI Config Manager** (`gui_config_manager.py`):
- Wraps existing `Config` class
- Provides validation for GUI inputs
- Handles atomic config file updates
- Monitors external config file changes (file watcher)
- Encrypts/decrypts sensitive values (API keys)

**GUI History Manager** (`gui_history_manager.py`):
- Persists task history to SQLite database
- Provides search and filter capabilities
- Manages history size limits and automatic purging
- Exports history to various formats

**Responsibilities**:
- Run backend operations in separate threads to keep GUI responsive
- Provide progress callbacks that emit updates to GUI
- Handle data persistence (history, session state)
- Manage configuration file safely with atomic operations
- Convert backend exceptions to user-friendly error messages

#### 4. Existing Backend (Unchanged)

**Purpose**: Core business logic for AI development tasks

All existing modules remain unchanged:
- `TaskExecutor`: Orchestrates AI agent loop
- `Config`: Configuration management
- `CodeAgent`: File operations and code manipulation
- `ContextManager`: Code analysis and understanding
- `LLMInterface`: Communication with language model
- `WebResearch`: Documentation fetching

**Interaction Pattern**: Backend Integration Layer calls existing backend, never the reverse. This maintains loose coupling and allows both CLI and GUI to coexist.

### Threading Model

The application uses a multi-threaded architecture to maintain UI responsiveness:

```
┌──────────────────────────────────────────────────────────┐
│                    Main Thread (GUI)                      │
│  - Eel web server                                         │
│  - HTML/CSS/JavaScript rendering                          │
│  - User input handling                                    │
│  - UI updates                                             │
└──────────────────────────────────────────────────────────┘
                    │                  ▲
                    │                  │
                    │  Start Task      │  Progress Callbacks
                    │                  │  eel.update_progress()
                    ▼                  │
┌──────────────────────────────────────────────────────────┐
│              Task Executor Thread                         │
│  - Runs TaskExecutor.execute()                           │
│  - Monitors progress                                      │
│  - Emits callbacks to GUI thread                         │
│  - Handles task cancellation                             │
└──────────────────────────────────────────────────────────┘
                    │                  ▲
                    │                  │
                    │  LLM Requests    │  LLM Responses
                    ▼                  │
┌──────────────────────────────────────────────────────────┐
│              LLM Communication Thread                     │
│  - Sends prompts to local LLM                            │
│  - Receives streaming responses                           │
│  - Handles timeouts                                       │
└──────────────────────────────────────────────────────────┘
```

**Key Threading Rules**:
1. **Never block the main thread**: All long-running operations run in separate threads
2. **Thread-safe communication**: Use thread-safe queues for inter-thread communication
3. **Callback pattern**: Worker threads call `eel.function_name()` to update GUI
4. **Cancellation support**: Worker threads check a `stop_flag` periodically

### Data Flow

#### Task Execution Flow

```
User enters task description
        │
        ▼
JavaScript validates input
        │
        ▼
JavaScript calls eel.run_task(description)
        │
        ▼
Python run_task() receives call
        │
        ▼
GUITaskManager starts new thread
        │
        ▼
Thread executes TaskExecutor.execute()
        │
        ├──► Progress updates
        │    │
        │    ▼
        │    Thread calls eel.update_progress(message)
        │    │
        │    ▼
        │    JavaScript receives progress update
        │    │
        │    ▼
        │    UI updates Progress Display
        │
        ├──► Completion
        │    │
        │    ▼
        │    Thread calls eel.task_completed(result)
        │    │
        │    ▼
        │    JavaScript receives completion
        │    │
        │    ▼
        │    UI shows success/error
        │    │
        │    ▼
        │    GUIHistoryManager saves to database
        │
        └──► Error handling follows same pattern
```

#### Configuration Update Flow

```
User modifies config field
        │
        ▼
JavaScript validates input (client-side)
        │
        ▼
JavaScript calls eel.validate_config_field(field, value)
        │
        ▼
Python validates (server-side)
        │
        ├──► Invalid: Return error message
        │    │
        │    ▼
        │    JavaScript displays error
        │
        └──► Valid: User clicks save
             │
             ▼
             JavaScript calls eel.save_config(config_data)
             │
             ▼
             GUIConfigManager creates backup
             │
             ▼
             GUIConfigManager writes to config.yaml (atomic)
             │
             ├──► Success: Return success message
             │
             └──► Failure: Restore backup, return error
```

## Components and Interfaces

### Frontend Components

#### Task Input Panel Component

**File**: `web/components/task_input.html` (included in main), `web/js/task_input.js`

**UI Elements**:
- Multi-line textarea (min-height: 100px, auto-expand)
- Character counter (displayed below textarea)
- Run button (primary action, green)
- Stop button (danger action, red, only visible when task running)
- Status indicator (idle, running, success, error)

**State**:
```javascript
{
    taskDescription: string,
    isRunning: boolean,
    characterCount: number,
    currentStatus: 'idle' | 'running' | 'success' | 'error'
}
```

**Methods**:
- `handleRunClick()`: Validates input and calls Python `run_task()`
- `handleStopClick()`: Calls Python `stop_task()`
- `updateCharacterCount()`: Updates counter display
- `setRunningState(isRunning)`: Updates UI for running/idle state

**Events**:
- Emits: `task-started`, `task-stopped`
- Listens: `task-completed`, `task-error`

#### Progress Display Component

**File**: `web/components/progress_display.html`, `web/js/progress_display.js`

**UI Elements**:
- Scrollable output container (with syntax highlighting)
- Auto-scroll toggle button
- Clear output button
- Copy to clipboard button
- Status badge (info, warning, error, success)
- Timestamp for each message

**State**:
```javascript
{
    messages: Array<{
        timestamp: Date,
        type: 'info' | 'warning' | 'error' | 'success',
        content: string
    }>,
    autoScroll: boolean,
    taskStatus: 'running' | 'completed' | 'failed'
}
```

**Methods**:
- `addMessage(type, content)`: Appends new message
- `clearMessages()`: Removes all messages
- `copyToClipboard()`: Copies all output to clipboard
- `toggleAutoScroll()`: Enables/disables auto-scroll
- `formatMessage(content)`: Applies syntax highlighting for code blocks

**Events**:
- Listens: `progress-update`, `task-completed`, `task-error`

#### Settings Manager Component

**File**: `web/components/settings.html`, `web/js/settings.js`

**UI Elements**:
- Form with input fields for each config parameter
- Section groupings (LLM Settings, Project Settings, Feature Flags)
- Browse buttons for file paths
- Save button
- Reset to defaults button
- Validation error messages (inline)
- Help tooltips (information icons)

**Configuration Sections**:

1. **LLM Settings**:
   - Endpoint (text input with validation)
   - Model name (text input)
   - Temperature (range slider, 0.0-1.0)
   - Max tokens (number input)
   - Context length (number input)
   - Backend type (dropdown: ollama, llamacpp, openai-compatible)

2. **Project Settings**:
   - Project root (text input with browse button)
   - Log level (dropdown: debug, info, warning, error)

3. **Feature Flags**:
   - Web research enabled (checkbox)
   - Self-improvement enabled (checkbox with warning)

4. **GUI Settings**:
   - Theme (dropdown: light, dark, auto)
   - Minimize to tray (checkbox)
   - Auto-save history (checkbox)
   - History retention days (number input)

**State**:
```javascript
{
    config: Object,
    originalConfig: Object,
    hasChanges: boolean,
    validationErrors: Object<field, errorMessage>,
    isLoading: boolean
}
```

**Methods**:
- `loadConfig()`: Fetches current config from Python
- `handleFieldChange(field, value)`: Validates and updates field
- `validateField(field, value)`: Client-side validation
- `saveConfig()`: Persists changes via Python
- `resetConfig()`: Restores default values
- `browseDirectory(field)`: Opens native file browser
- `markFieldError(field, message)`: Shows validation error
- `clearFieldError(field)`: Removes validation error

**Events**:
- Emits: `config-saved`, `config-error`
- Listens: `config-external-change` (when config modified outside app)

#### History View Component

**File**: `web/components/history.html`, `web/js/history.js`

**UI Elements**:
- List of history entries (virtual scrolling for performance)
- Search input (filters by task description)
- Date range filter
- Status filter (all, success, failed, cancelled)
- Sort options (newest first, oldest first)
- Entry details panel (expanded view)
- Re-run button (per entry)
- Delete button (per entry)
- Clear all button
- Export button (JSON/CSV)

**History Entry Display**:
```
┌─────────────────────────────────────────────────────────┐
│ 🟢 Create calculator module with tests                 │
│ 2024-01-15 14:32:45 | Duration: 2m 34s | Success       │
│                                                          │
│ [Re-run] [View Details] [Delete]                       │
└─────────────────────────────────────────────────────────┘
```

**Expanded Entry**:
```
┌─────────────────────────────────────────────────────────┐
│ 🟢 Create calculator module with tests                 │
│ 2024-01-15 14:32:45 | Duration: 2m 34s | Success       │
│                                                          │
│ Full Description:                                       │
│ Create a new Python module called calculator.py...     │
│                                                          │
│ Output: (first 500 chars)                              │
│ Created file: src/calculator.py                        │
│ Created file: tests/test_calculator.py                 │
│ ...                                                     │
│                                                          │
│ [Re-run] [View Full Output] [Delete]                   │
└─────────────────────────────────────────────────────────┘
```

**State**:
```javascript
{
    entries: Array<HistoryEntry>,
    filteredEntries: Array<HistoryEntry>,
    searchQuery: string,
    statusFilter: 'all' | 'success' | 'failed' | 'cancelled',
    sortOrder: 'newest' | 'oldest',
    selectedEntry: HistoryEntry | null,
    isLoading: boolean
}
```

**Methods**:
- `loadHistory()`: Fetches history from Python
- `filterEntries()`: Applies search and filters
- `sortEntries()`: Applies sort order
- `selectEntry(id)`: Shows entry details
- `rerunTask(id)`: Executes same task again
- `deleteEntry(id)`: Removes entry from history
- `clearAllHistory()`: Removes all entries (with confirmation)
- `exportHistory(format)`: Downloads history file

**Events**:
- Emits: `history-rerun` (when user re-runs a task)
- Listens: `task-completed` (to add new entry)

### Backend Interfaces

#### GUI Task Manager

**File**: `src/gui/gui_task_manager.py`

**Class**: `GUITaskManager`

**Purpose**: Wraps `TaskExecutor` to provide thread-safe, GUI-friendly task execution

**Interface**:
```python
class GUITaskManager:
    def __init__(self, config: Config):
        """Initialize with application configuration"""
        self.config = config
        self.task_executor = TaskExecutor(config)
        self.current_thread = None
        self.stop_flag = threading.Event()
        
    def run_task(self, task_description: str, progress_callback: Callable) -> str:
        """
        Execute a task in a separate thread
        
        Args:
            task_description: User's task description
            progress_callback: Function to call with progress updates
            
        Returns:
            task_id: Unique identifier for this task execution
            
        Raises:
            TaskAlreadyRunningError: If a task is currently executing
        """
        
    def stop_task(self) -> bool:
        """
        Cancel the currently running task
        
        Returns:
            True if task was stopped, False if no task running
        """
        
    def is_running(self) -> bool:
        """Check if a task is currently executing"""
        
    def get_status(self) -> dict:
        """
        Get current task status
        
        Returns:
            {
                'is_running': bool,
                'task_id': str | None,
                'start_time': datetime | None,
                'elapsed_seconds': float | None
            }
        """
```

**Progress Callback Signature**:
```python
def progress_callback(event_type: str, data: dict) -> None:
    """
    Called when task progress updates occur
    
    Args:
        event_type: Type of event ('start', 'progress', 'complete', 'error')
        data: Event-specific data
            - start: {'task_id': str, 'description': str}
            - progress: {'message': str, 'type': 'info'|'warning'|'error'}
            - complete: {'task_id': str, 'result': dict, 'duration': float}
            - error: {'task_id': str, 'error': str, 'traceback': str}
    """
```

**Threading Implementation**:
- Creates daemon thread for each task execution
- Uses `threading.Event` for stop signal
- Periodically checks stop flag during execution
- Emits progress via callback (thread-safe via Eel)

#### GUI Config Manager

**File**: `src/gui/gui_config_manager.py`

**Class**: `GUIConfigManager`

**Purpose**: Provides GUI-specific configuration management with validation and encryption

**Interface**:
```python
class GUIConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize with path to config file"""
        self.config_path = config_path
        self.config = Config.load(config_path)
        self.file_watcher = FileWatcher(config_path)
        self.encryption_key = self._load_or_create_key()
        
    def get_config_for_gui(self) -> dict:
        """
        Get configuration in GUI-friendly format
        
        Returns:
            Dictionary with all config values, sensitive values masked
        """
        
    def validate_field(self, field_name: str, value: any) -> tuple[bool, str]:
        """
        Validate a single configuration field
        
        Args:
            field_name: Dot-notation field name (e.g., 'llm.endpoint')
            value: Value to validate
            
        Returns:
            (is_valid, error_message)
        """
        
    def save_config(self, config_data: dict) -> tuple[bool, str]:
        """
        Save configuration with atomic write and backup
        
        Args:
            config_data: Complete configuration dictionary
            
        Returns:
            (success, message)
        """
        
    def reset_to_defaults(self) -> dict:
        """Reset configuration to default values"""
        
    def check_external_changes(self) -> bool:
        """
        Check if config file was modified externally
        
        Returns:
            True if changes detected
        """
        
    def reload_config(self) -> None:
        """Reload configuration from disk"""
        
    def encrypt_sensitive_value(self, value: str) -> str:
        """Encrypt sensitive value (e.g., API key)"""
        
    def decrypt_sensitive_value(self, encrypted: str) -> str:
        """Decrypt sensitive value"""
```

**Validation Rules**:
- `llm.endpoint`: Must be valid URL
- `llm.temperature`: Must be float between 0.0 and 1.0
- `llm.max_tokens`: Must be positive integer
- `project_root`: Must be valid directory path
- `log_level`: Must be one of: debug, info, warning, error

**Atomic Write Process**:
1. Create backup: `config.yaml.backup`
2. Write to temporary file: `config.yaml.tmp`
3. Atomic rename: `config.yaml.tmp` → `config.yaml`
4. If error, restore from backup

#### GUI History Manager

**File**: `src/gui/gui_history_manager.py`

**Class**: `GUIHistoryManager`

**Purpose**: Persist and manage task execution history

**Interface**:
```python
class GUIHistoryManager:
    def __init__(self, db_path: str = None):
        """
        Initialize history manager
        
        Args:
            db_path: Path to SQLite database (default: ~/.local-ai-dev/history.db)
        """
        self.db_path = db_path or self._get_default_db_path()
        self._init_database()
        
    def add_entry(self, entry: HistoryEntry) -> str:
        """
        Add a new history entry
        
        Args:
            entry: HistoryEntry object
            
        Returns:
            entry_id: UUID of the created entry
        """
        
    def get_entries(self, 
                    limit: int = 100, 
                    search_query: str = None,
                    status_filter: str = None,
                    start_date: datetime = None,
                    end_date: datetime = None) -> list[HistoryEntry]:
        """
        Retrieve history entries with optional filtering
        
        Args:
            limit: Maximum number of entries to return
            search_query: Filter by task description (case-insensitive)
            status_filter: Filter by status ('success', 'failed', 'cancelled')
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            
        Returns:
            List of HistoryEntry objects, sorted by timestamp (newest first)
        """
        
    def get_entry_by_id(self, entry_id: str) -> HistoryEntry | None:
        """Get a specific history entry by ID"""
        
    def delete_entry(self, entry_id: str) -> bool:
        """Delete a history entry"""
        
    def clear_all(self) -> int:
        """
        Delete all history entries
        
        Returns:
            Number of entries deleted
        """
        
    def purge_old_entries(self, days: int = 90) -> int:
        """
        Delete entries older than specified days
        
        Returns:
            Number of entries deleted
        """
        
    def export_to_json(self, filepath: str) -> bool:
        """Export all history to JSON file"""
        
    def export_to_csv(self, filepath: str) -> bool:
        """Export all history to CSV file"""
        
    def get_statistics(self) -> dict:
        """
        Get history statistics
        
        Returns:
            {
                'total_entries': int,
                'success_count': int,
                'failed_count': int,
                'cancelled_count': int,
                'total_duration_seconds': float,
                'average_duration_seconds': float
            }
        """
```

**Data Model**:
```python
@dataclass
class HistoryEntry:
    entry_id: str  # UUID
    task_description: str
    timestamp: datetime
    duration_seconds: float
    status: str  # 'success', 'failed', 'cancelled'
    output: str  # Truncated to max 10MB
    error_message: str | None
    config_snapshot: dict  # Config used for this task
```

**Database Schema**:
```sql
CREATE TABLE history_entries (
    entry_id TEXT PRIMARY KEY,
    task_description TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    duration_seconds REAL,
    status TEXT NOT NULL,
    output TEXT,
    error_message TEXT,
    config_snapshot TEXT,  -- JSON
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp ON history_entries(timestamp),
    INDEX idx_status ON history_entries(status)
);
```

### Eel Communication Protocol

#### Python to JavaScript

Python calls JavaScript functions to update the GUI:

```python
# Update progress display
eel.update_progress({
    'type': 'info',  # 'info', 'warning', 'error', 'success'
    'message': 'Processing file: src/main.py',
    'timestamp': datetime.now().isoformat()
})

# Task completed
eel.task_completed({
    'task_id': 'uuid',
    'status': 'success',
    'duration': 45.2,
    'summary': 'Created 3 files, ran 12 tests'
})

# Task failed
eel.task_error({
    'task_id': 'uuid',
    'error_type': 'LLMConnectionError',
    'error_message': 'Could not connect to LLM at http://localhost:11434',
    'suggestion': 'Verify your LLM server is running'
})

# Configuration externally changed
eel.config_external_change({
    'message': 'Configuration file was modified externally'
})
```

#### JavaScript to Python

JavaScript calls Python functions (returns await-able promises):

```javascript
// Run a task
const result = await eel.run_task(taskDescription)();
// Returns: { success: true, task_id: 'uuid' }
//     or:  { success: false, error: 'Task already running' }

// Stop task
const result = await eel.stop_task()();
// Returns: { success: true }

// Get configuration
const config = await eel.get_config()();
// Returns: { llm: {...}, project_root: '...', ... }

// Save configuration
const result = await eel.save_config(configData)();
// Returns: { success: true, message: 'Configuration saved' }
//     or:  { success: false, error: 'Invalid endpoint URL' }

// Validate field
const result = await eel.validate_config_field('llm.temperature', 0.5)();
// Returns: { valid: true }
//     or:  { valid: false, error: 'Must be between 0.0 and 1.0' }

// Get history
const entries = await eel.get_history(100, searchQuery)();
// Returns: [ { entry_id, task_description, timestamp, ... }, ... ]

// Browse directory
const result = await eel.browse_directory('/home/user')();
// Returns: { success: true, path: '/home/user/selected/path' }
//     or:  { success: false, cancelled: true }
```

## Data Models

### Frontend Data Models (TypeScript-style)

```typescript
interface AppState {
    currentView: 'task' | 'history' | 'settings';
    theme: 'light' | 'dark';
    isTaskRunning: boolean;
    currentTaskId: string | null;
}

interface TaskInputState {
    description: string;
    characterCount: number;
    isRunning: boolean;
    status: 'idle' | 'running' | 'success' | 'error';
}

interface ProgressMessage {
    timestamp: Date;
    type: 'info' | 'warning' | 'error' | 'success';
    content: string;
}

interface ProgressDisplayState {
    messages: ProgressMessage[];
    autoScroll: boolean;
    taskStatus: 'running' | 'completed' | 'failed';
}

interface Config {
    llm: {
        endpoint: string;
        model_name: string;
        temperature: number;
        max_tokens: number;
        context_length: number;
        backend_type: 'ollama' | 'llamacpp' | 'openai-compatible';
    };
    project_root: string;
    log_level: 'debug' | 'info' | 'warning' | 'error';
    web_research_enabled: boolean;
    self_improvement_enabled: boolean;
    gui: {
        theme: 'light' | 'dark' | 'auto';
        minimize_to_tray: boolean;
        auto_save_history: boolean;
        history_retention_days: number;
    };
}

interface HistoryEntry {
    entry_id: string;
    task_description: string;
    timestamp: string;  // ISO 8601
    duration_seconds: number;
    status: 'success' | 'failed' | 'cancelled';
    output: string;
    error_message: string | null;
}

interface HistoryViewState {
    entries: HistoryEntry[];
    filteredEntries: HistoryEntry[];
    searchQuery: string;
    statusFilter: 'all' | 'success' | 'failed' | 'cancelled';
    sortOrder: 'newest' | 'oldest';
    selectedEntry: HistoryEntry | null;
}
```

### Backend Data Models (Python)

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal

@dataclass
class GUIConfig:
    """GUI-specific configuration"""
    theme: Literal['light', 'dark', 'auto'] = 'auto'
    minimize_to_tray: bool = False
    auto_save_history: bool = True
    history_retention_days: int = 90
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False

@dataclass
class TaskStatus:
    """Current task execution status"""
    is_running: bool
    task_id: Optional[str]
    start_time: Optional[datetime]
    elapsed_seconds: Optional[float]
    description: Optional[str]

@dataclass
class HistoryEntry:
    """Task history entry"""
    entry_id: str
    task_description: str
    timestamp: datetime
    duration_seconds: float
    status: Literal['success', 'failed', 'cancelled']
    output: str
    error_message: Optional[str]
    config_snapshot: dict

@dataclass
class ProgressEvent:
    """Progress update event"""
    event_type: Literal['start', 'progress', 'complete', 'error']
    timestamp: datetime
    data: dict

@dataclass
class ValidationResult:
    """Configuration validation result"""
    is_valid: bool
    error_message: Optional[str]
    field_name: str
    validated_value: any
```

## UI/UX Design

### Visual Design Principles

1. **Clarity**: Every element should have a clear purpose
2. **Consistency**: Consistent spacing, colors, and typography throughout
3. **Feedback**: Immediate visual feedback for all user actions
4. **Efficiency**: Keyboard shortcuts for power users
5. **Aesthetics**: Clean, modern design that's pleasant to use

### Layout Structure

#### Main Application Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Local AI Development Environment                      [_][□][X]│
├──────────────────────────────────────────────────────────────┤
│  [📝 Task]  [📚 History]  [⚙️ Settings]                    │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│                                                                │
│                     CONTENT AREA                               │
│                  (View-specific content)                       │
│                                                                │
│                                                                │
│                                                                │
│                                                                │
│                                                                │
│                                                                │
│                                                                │
├──────────────────────────────────────────────────────────────┤
│  Status: Ready  |  Theme: Light ☀️                            │
└──────────────────────────────────────────────────────────────┘
```

#### Task View Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Task Input                                                    │
│  ┌──────────────────────────────────────────────────────────┐│
│  │ Enter your development task here...                      ││
│  │                                                            ││
│  │                                                            ││
│  │                                                            ││
│  └──────────────────────────────────────────────────────────┘│
│  Characters: 0 / 5000                                          │
│  [▶️ Run Task]  [⏹️ Stop]                                      │
├──────────────────────────────────────────────────────────────┤
│  Progress                                                      │
│  ┌──────────────────────────────────────────────────────────┐│
│  │ ℹ️ [14:32:45] Starting task execution...                 ││
│  │ ℹ️ [14:32:46] Analyzing project structure...             ││
│  │ ✅ [14:32:48] Created file: src/calculator.py            ││
│  │ ℹ️ [14:32:49] Running tests...                           ││
│  │ ✅ [14:32:52] All tests passed (12 passed)               ││
│  │                                                            ││
│  │                                                            ││
│  └──────────────────────────────────────────────────────────┘│
│  [🗑️ Clear]  [📋 Copy]  [⬇️] Auto-scroll: ON                 │
└──────────────────────────────────────────────────────────────┘
```

#### History View Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Task History                                                  │
│  ┌──────────────────────────────────────────────────────────┐│
│  │ 🔍 Search tasks...                [All] [✓] [✗] [Clear] ││
│  └──────────────────────────────────────────────────────────┘│
│  ┌──────────────────────────────────────────────────────────┐│
│  │ ✅ Create calculator module with tests                   ││
│  │    2024-01-15 14:32:45 | 2m 34s | Success                ││
│  │    [Re-run] [Details] [Delete]                            ││
│  ├──────────────────────────────────────────────────────────┤│
│  │ ✅ Add REST API endpoint for user registration           ││
│  │    2024-01-15 13:15:22 | 3m 12s | Success                ││
│  │    [Re-run] [Details] [Delete]                            ││
│  ├──────────────────────────────────────────────────────────┤│
│  │ ❌ Fix date picker crash                                 ││
│  │    2024-01-15 12:45:10 | 1m 5s | Failed                  ││
│  │    [Re-run] [Details] [Delete]                            ││
│  ├──────────────────────────────────────────────────────────┤│
│  │ ...                                                        ││
│  └──────────────────────────────────────────────────────────┘│
│  [📤 Export to JSON]  [📤 Export to CSV]                      │
└──────────────────────────────────────────────────────────────┘
```

#### Settings View Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Settings                                                      │
│  ┌──────────────────────────────────────────────────────────┐│
│  │ LLM Settings                                              ││
│  │                                                            ││
│  │ Endpoint:        [http://localhost:11434           ] ℹ️  ││
│  │ Model Name:      [codellama:13b                    ] ℹ️  ││
│  │ Temperature:     [━━━━━━━━━━○━━━━━━] 0.5                 ││
│  │ Max Tokens:      [4096                             ] ℹ️  ││
│  │ Context Length:  [16384                            ] ℹ️  ││
│  │ Backend Type:    [Ollama ▼                         ] ℹ️  ││
│  │                                                            ││
│  │ Project Settings                                          ││
│  │                                                            ││
│  │ Project Root:    [/home/user/projects/myproject    ] 📁  ││
│  │ Log Level:       [Info ▼                           ] ℹ️  ││
│  │                                                            ││
│  │ Feature Flags                                             ││
│  │                                                            ││
│  │ [✓] Enable web research                            ℹ️    ││
│  │ [ ] Enable self-improvement (⚠️ Use with caution)  ℹ️    ││
│  │                                                            ││
│  │ GUI Settings                                              ││
│  │                                                            ││
│  │ Theme:           [Auto (System) ▼                  ] ℹ️  ││
│  │ [✓] Minimize to system tray                        ℹ️    ││
│  │ [✓] Auto-save task history                         ℹ️    ││
│  │ History Retention: [90] days                       ℹ️    ││
│  │                                                            ││
│  └──────────────────────────────────────────────────────────┘│
│  [💾 Save Changes]  [↺ Reset to Defaults]                    │
└──────────────────────────────────────────────────────────────┘
```

### Color Scheme

#### Light Theme

**Primary Colors**:
- Primary: `#2563eb` (Blue 600) - Main actions, links
- Success: `#10b981` (Green 500) - Success states, run button
- Warning: `#f59e0b` (Amber 500) - Warnings, caution states
- Error: `#ef4444` (Red 500) - Errors, stop button
- Info: `#3b82f6` (Blue 500) - Informational messages

**Neutral Colors**:
- Background: `#ffffff` (White)
- Surface: `#f9fafb` (Gray 50) - Cards, panels
- Border: `#e5e7eb` (Gray 200)
- Text Primary: `#111827` (Gray 900)
- Text Secondary: `#6b7280` (Gray 500)
- Text Disabled: `#9ca3af` (Gray 400)

**Component Colors**:
- Input Background: `#ffffff`
- Input Border: `#d1d5db` (Gray 300)
- Input Focus Border: `#2563eb` (Primary)
- Button Background: `#2563eb` (Primary)
- Button Hover: `#1d4ed8` (Blue 700)

#### Dark Theme

**Primary Colors**:
- Primary: `#3b82f6` (Blue 500)
- Success: `#10b981` (Green 500)
- Warning: `#f59e0b` (Amber 500)
- Error: `#ef4444` (Red 500)
- Info: `#60a5fa` (Blue 400)

**Neutral Colors**:
- Background: `#111827` (Gray 900)
- Surface: `#1f2937` (Gray 800) - Cards, panels
- Border: `#374151` (Gray 700)
- Text Primary: `#f9fafb` (Gray 50)
- Text Secondary: `#9ca3af` (Gray 400)
- Text Disabled: `#6b7280` (Gray 500)

**Component Colors**:
- Input Background: `#1f2937` (Gray 800)
- Input Border: `#4b5563` (Gray 600)
- Input Focus Border: `#3b82f6` (Primary)
- Button Background: `#3b82f6` (Primary)
- Button Hover: `#2563eb` (Blue 600)

### Typography

**Font Families**:
- UI Font: `system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- Monospace: `"Fira Code", "Cascadia Code", "JetBrains Mono", "Source Code Pro", Consolas, monospace`

**Font Sizes**:
- Title: `24px` / `1.5rem` (600 weight)
- Heading: `18px` / `1.125rem` (600 weight)
- Body: `14px` / `0.875rem` (400 weight)
- Small: `12px` / `0.75rem` (400 weight)
- Code: `13px` / `0.8125rem` (400 weight)

**Line Heights**:
- Title: `1.2`
- Heading: `1.3`
- Body: `1.5`
- Code: `1.6`

### Spacing System

**Base Unit**: `4px`

**Scale**:
- xs: `4px`
- sm: `8px`
- md: `16px`
- lg: `24px`
- xl: `32px`
- 2xl: `48px`

**Component Spacing**:
- Padding (buttons): `8px 16px`
- Padding (inputs): `8px 12px`
- Padding (panels): `16px`
- Margin (between sections): `24px`
- Gap (flex/grid): `16px`

### Component Styling

#### Buttons

**Primary Button**:
```css
.btn-primary {
    background: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: background 150ms ease;
}

.btn-primary:hover {
    background: #1d4ed8;
}

.btn-primary:disabled {
    background: #9ca3af;
    cursor: not-allowed;
}
```

**Success Button** (Run Task):
```css
.btn-success {
    background: #10b981;
    color: #ffffff;
}

.btn-success:hover {
    background: #059669;
}
```

**Danger Button** (Stop Task):
```css
.btn-danger {
    background: #ef4444;
    color: #ffffff;
}

.btn-danger:hover {
    background: #dc2626;
}
```

#### Input Fields

```css
.input-text {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
    color: #111827;
    transition: border-color 150ms ease;
}

.input-text:focus {
    outline: none;
    border-color: #2563eb;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.input-text.error {
    border-color: #ef4444;
}

.input-error-message {
    color: #ef4444;
    font-size: 12px;
    margin-top: 4px;
}
```

#### Progress Messages

```css
.progress-message {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    padding: 8px;
    border-left: 3px solid transparent;
    font-family: monospace;
    font-size: 13px;
}

.progress-message.info {
    border-color: #3b82f6;
    background: #eff6ff;
}

.progress-message.success {
    border-color: #10b981;
    background: #ecfdf5;
}

.progress-message.warning {
    border-color: #f59e0b;
    background: #fffbeb;
}

.progress-message.error {
    border-color: #ef4444;
    background: #fef2f2;
}
```

### Navigation

**Tab Navigation**:
- Three main tabs: Task, History, Settings
- Active tab: Bold text, bottom border (2px, primary color)
- Inactive tab: Normal weight, gray text
- Hover: Background color change
- Keyboard navigation: Tab key to cycle, Enter to activate

**Keyboard Shortcuts**:
- `Ctrl+Enter` (Windows/Linux) / `Cmd+Enter` (macOS): Run task
- `Ctrl+,` / `Cmd+,`: Open settings
- `Ctrl+H` / `Cmd+H`: View history
- `Ctrl+1`: Switch to Task view
- `Ctrl+2`: Switch to History view
- `Ctrl+3`: Switch to Settings view
- `Esc`: Cancel/close dialog
- `Ctrl+C`: Copy progress output (when Progress Display focused)

### Responsive Behavior

**Minimum Window Size**: 800x600 pixels

**Breakpoints**:
- Compact: < 1000px width
  - Reduce padding
  - Stack some side-by-side elements
- Normal: 1000px - 1400px width
  - Standard layout
- Wide: > 1400px width
  - Use extra space for wider text areas

**Scaling**:
- Support system DPI scaling (100%, 125%, 150%, 200%)
- Use relative units (rem, em) where appropriate
- Icons should scale proportionally

## Icon Design

### Icon Concept

**Design Direction**: Modern, geometric robot/AI symbol with code elements

**Concept**: A stylized robot head or AI brain composed of geometric shapes, with subtle code brackets or binary elements

**Style**:
- Flat design (no gradients in small sizes)
- Bold, recognizable silhouette
- Works in monochrome
- Distinctive at small sizes (16x16)

### Color Palette

**Primary Icon Colors**:
- Main: `#2563eb` (Blue 600) - Primary brand color
- Accent: `#10b981` (Green 500) - Represents "active" or "intelligent"
- Dark Variant: `#1e40af` (Blue 800) - For light backgrounds
- Light Variant: `#60a5fa` (Blue 400) - For dark backgrounds

**Icon Variations**:
1. **Full Color**: Blue and green on transparent background
2. **Monochrome**: Single color (adapts to system theme)
3. **White**: For dark backgrounds/taskbar
4. **Black**: For light backgrounds

### Required Formats and Sizes

**Windows (ICO)**:
- 16x16 pixels (taskbar, system tray)
- 24x24 pixels
- 32x32 pixels (desktop shortcut)
- 48x48 pixels (large icons)
- 64x64 pixels
- 128x128 pixels
- 256x256 pixels (high DPI)

**macOS (ICNS)**:
- 16x16@1x, 32x32@2x
- 32x32@1x, 64x64@2x
- 128x128@1x, 256x256@2x
- 256x256@1x, 512x512@2x
- 512x512@1x, 1024x1024@2x

**Linux (PNG)**:
- 16x16, 24x24, 32x32, 48x48, 64x64, 128x128, 256x256, 512x512

**Favicon** (for Eel web view):
- favicon.ico (16x16, 32x32)
- favicon.png (32x32, 180x180 for Apple)

### Icon Design Specifications

**16x16 (Minimum Size)**:
- Must be recognizable
- Simplified version of main icon
- No fine details
- Bold outlines (2px minimum)

**32x32 to 64x64 (Standard Sizes)**:
- Full detail version
- Clear shapes and symbols
- Good contrast

**128x256 (Large Sizes)**:
- Refined details
- Subtle shadows or depth (if desired)
- Crisp edges

### Icon Production

**Source File**:
- Create in vector format (SVG)
- Maintain at highest resolution
- Export to required formats using:
  - ImageMagick for ICO
  - png2icns for ICNS
  - Direct PNG exports for Linux

**Example SVG Structure**:
```xml
<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <!-- Robot head outline -->
  <path d="..." fill="#2563eb"/>
  
  <!-- Code bracket accent -->
  <path d="..." fill="#10b981"/>
  
  <!-- AI/brain symbol -->
  <circle cx="256" cy="200" r="20" fill="#2563eb"/>
</svg>
```

## File Structure

### Project Directory Structure

```
Local dev ai/
├── src/
│   ├── gui/                        # NEW: GUI-specific code
│   │   ├── __init__.py
│   │   ├── gui_app.py              # Main Eel application entry point
│   │   ├── gui_task_manager.py    # Task execution with threading
│   │   ├── gui_config_manager.py  # Config management for GUI
│   │   ├── gui_history_manager.py # History persistence
│   │   └── gui_utils.py            # Utility functions
│   │
│   ├── web/                        # NEW: Frontend files
│   │   ├── index.html              # Main application HTML
│   │   ├── css/
│   │   │   ├── main.css            # Main stylesheet
│   │   │   ├── themes/
│   │   │   │   ├── light.css       # Light theme
│   │   │   │   └── dark.css        # Dark theme
│   │   │   └── components/
│   │   │       ├── buttons.css
│   │   │       ├── inputs.css
│   │   │       └── progress.css
│   │   │
│   │   ├── js/
│   │   │   ├── main.js             # Application initialization
│   │   │   ├── state.js            # State management
│   │   │   ├── components/
│   │   │   │   ├── task_input.js
│   │   │   │   ├── progress_display.js
│   │   │   │   ├── settings.js
│   │   │   │   └── history.js
│   │   │   └── utils/
│   │   │       ├── validation.js
│   │   │       └── formatting.js
│   │   │
│   │   └── assets/
│   │       ├── icon.svg            # Source SVG icon
│   │       ├── icon.ico            # Windows icon
│   │       ├── icon.icns           # macOS icon
│   │       └── icons/              # UI icons (PNG/SVG)
│   │           ├── run.svg
│   │           ├── stop.svg
│   │           ├── settings.svg
│   │           └── history.svg
│   │
│   ├── core/                       # Existing backend (unchanged)
│   ├── agents/                     # Existing backend (unchanged)
│   ├── context/                    # Existing backend (unchanged)
│   ├── web/                        # Existing backend (unchanged)
│   ├── self_improvement/           # Existing backend (unchanged)
│   └── main.py                     # Existing CLI entry point (unchanged)
│
├── tests/
│   ├── gui/                        # NEW: GUI tests
│   │   ├── test_gui_task_manager.py
│   │   ├── test_gui_config_manager.py
│   │   └── test_gui_history_manager.py
│   ├── unit/                       # Existing tests
│   ├── integration/                # Existing tests
│   └── properties/                 # Existing tests
│
├── build/                          # NEW: Build configuration
│   ├── pyinstaller/
│   │   ├── local-ai-dev.spec      # PyInstaller spec file
│   │   ├── hooks/                  # PyInstaller hooks
│   │   └── resources/              # Additional resources
│   └── installers/
│       ├── windows.nsi             # NSIS installer script (Windows)
│       ├── macos.pkgproj           # Packages project (macOS)
│       └── linux.desktop           # Desktop entry (Linux)
│
├── dist/                           # NEW: Build output (git-ignored)
│   ├── windows/
│   ├── macos/
│   └── linux/
│
├── config.yaml                     # Existing config (unchanged)
├── config.example.yaml             # Existing example (unchanged)
├── requirements.txt                # Updated with Eel
├── requirements-gui.txt            # NEW: GUI-specific dependencies
├── README.md                       # Updated with GUI info
└── CONTRIBUTING.md                 # Updated with GUI dev info
```

### Key File Descriptions

**src/gui/gui_app.py**:
- Main entry point for GUI application
- Initializes Eel
- Exposes Python functions to JavaScript
- Starts Eel web server
- Handles application lifecycle

**src/web/index.html**:
- Main HTML structure
- Loads CSS and JavaScript
- Defines component containers
- Includes Eel JavaScript bridge

**src/web/js/main.js**:
- Application initialization
- Eel connection setup
- Event listener registration
- View routing

**src/web/js/state.js**:
- Central state management
- State updates and notifications
- Persistence (localStorage for UI preferences)

**build/pyinstaller/local-ai-dev.spec**:
- PyInstaller configuration
- Defines what to bundle
- Icon embedding
- Platform-specific settings

### Integration with Existing Structure

**No Changes to Existing Files**:
- All existing backend code remains unchanged
- CLI functionality (src/main.py) continues to work independently
- Tests for existing code unchanged

**New Dependencies Only**:
- Eel and its dependencies added to requirements-gui.txt
- Development dependencies (PyInstaller) separate
- No new dependencies for existing CLI functionality

**Shared Configuration**:
- Both CLI and GUI read/write same config.yaml
- GUI adds new section: `gui` settings
- Backward compatible: CLI ignores `gui` section

## Implementation Details

### Eel Communication Implementation

#### Python Side (src/gui/gui_app.py)

```python
import eel
import threading
from typing import Callable
from src.gui.gui_task_manager import GUITaskManager
from src.gui.gui_config_manager import GUIConfigManager
from src.gui.gui_history_manager import GUIHistoryManager
from src.core.config import Config

# Initialize managers
config = Config.load("config.yaml")
task_manager = GUITaskManager(config)
config_manager = GUIConfigManager("config.yaml")
history_manager = GUIHistoryManager()

# Initialize Eel
eel.init('src/web')

@eel.expose
def run_task(task_description: str) -> dict:
    """Start executing a task"""
    try:
        if task_manager.is_running():
            return {'success': False, 'error': 'A task is already running'}
        
        # Progress callback that sends updates to frontend
        def progress_callback(event_type: str, data: dict):
            if event_type == 'progress':
                eel.update_progress(data)
            elif event_type == 'complete':
                eel.task_completed(data)
                # Save to history
                history_manager.add_entry(HistoryEntry(
                    entry_id=data['task_id'],
                    task_description=task_description,
                    timestamp=datetime.now(),
                    duration_seconds=data['duration'],
                    status='success',
                    output=data.get('output', ''),
                    error_message=None,
                    config_snapshot=config.to_dict()
                ))
            elif event_type == 'error':
                eel.task_error(data)
                # Save failed task to history
                history_manager.add_entry(HistoryEntry(
                    entry_id=data['task_id'],
                    task_description=task_description,
                    timestamp=datetime.now(),
                    duration_seconds=data.get('duration', 0),
                    status='failed',
                    output=data.get('output', ''),
                    error_message=data['error'],
                    config_snapshot=config.to_dict()
                ))
        
        task_id = task_manager.run_task(task_description, progress_callback)
        return {'success': True, 'task_id': task_id}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

@eel.expose
def stop_task() -> dict:
    """Stop the currently running task"""
    try:
        if task_manager.stop_task():
            return {'success': True}
        else:
            return {'success': False, 'error': 'No task is running'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@eel.expose
def get_config() -> dict:
    """Get current configuration"""
    try:
        return config_manager.get_config_for_gui()
    except Exception as e:
        return {'error': str(e)}

@eel.expose
def save_config(config_data: dict) -> dict:
    """Save configuration"""
    try:
        success, message = config_manager.save_config(config_data)
        return {'success': success, 'message': message}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@eel.expose
def validate_config_field(field_name: str, value) -> dict:
    """Validate a configuration field"""
    try:
        is_valid, error_message = config_manager.validate_field(field_name, value)
        return {'valid': is_valid, 'error': error_message}
    except Exception as e:
        return {'valid': False, 'error': str(e)}

@eel.expose
def get_history(limit: int = 100, search_query: str = None) -> list:
    """Get task history"""
    try:
        entries = history_manager.get_entries(limit, search_query)
        # Convert to dict for JSON serialization
        return [
            {
                'entry_id': e.entry_id,
                'task_description': e.task_description,
                'timestamp': e.timestamp.isoformat(),
                'duration_seconds': e.duration_seconds,
                'status': e.status,
                'output': e.output[:500],  # Truncate for list view
                'error_message': e.error_message
            }
            for e in entries
        ]
    except Exception as e:
        return []

@eel.expose
def browse_directory(initial_path: str = None) -> dict:
    """Open native directory browser"""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()  # Hide main window
        
        path = filedialog.askdirectory(initialdir=initial_path)
        
        if path:
            return {'success': True, 'path': path}
        else:
            return {'success': False, 'cancelled': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def start_gui():
    """Start the GUI application"""
    # Check for external config changes periodically
    def config_watcher():
        while True:
            time.sleep(5)
            if config_manager.check_external_changes():
                eel.config_external_change({
                    'message': 'Configuration file was modified externally'
                })
    
    # Start config watcher in background thread
    watcher_thread = threading.Thread(target=config_watcher, daemon=True)
    watcher_thread.start()
    
    # Start Eel
    eel.start('index.html', size=(1200, 800), port=8080)

if __name__ == '__main__':
    start_gui()
```

#### JavaScript Side (src/web/js/main.js)

```javascript
// Application state
const state = {
    currentView: 'task',
    theme: 'light',
    isTaskRunning: false,
    currentTaskId: null
};

// Initialize application
async function initApp() {
    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
    
    // Load saved window size
    // (Eel doesn't directly support this, handled by PyInstaller settings)
    
    // Setup navigation
    setupNavigation();
    
    // Setup components
    TaskInput.init();
    ProgressDisplay.init();
    Settings.init();
    History.init();
    
    // Register Eel callbacks from Python
    registerPythonCallbacks();
    
    // Show initial view
    showView('task');
    
    console.log('Application initialized');
}

// Register callbacks that Python will call
function registerPythonCallbacks() {
    // These functions will be called from Python via eel.function_name()
    window.update_progress = function(data) {
        ProgressDisplay.addMessage(data.type, data.message, data.timestamp);
    };
    
    window.task_completed = function(data) {
        state.isTaskRunning = false;
        TaskInput.setRunningState(false);
        ProgressDisplay.setTaskStatus('completed');
        ProgressDisplay.addMessage('success', 
            `Task completed successfully in ${data.duration.toFixed(1)}s`);
        History.refresh();
    };
    
    window.task_error = function(data) {
        state.isTaskRunning = false;
        TaskInput.setRunningState(false);
        ProgressDisplay.setTaskStatus('failed');
        ProgressDisplay.addMessage('error', 
            `Task failed: ${data.error_message}`);
        History.refresh();
    };
    
    window.config_external_change = function(data) {
        showNotification('warning', data.message, 'Reload?', () => {
            Settings.loadConfig();
        });
    };
}

// Navigation
function setupNavigation() {
    document.querySelectorAll('[data-view]').forEach(button => {
        button.addEventListener('click', (e) => {
            const view = e.currentTarget.dataset.view;
            showView(view);
        });
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + Enter: Run task
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            if (state.currentView === 'task') {
                TaskInput.handleRunClick();
            }
        }
        
        // Ctrl/Cmd + 1/2/3: Switch views
        if (e.ctrlKey || e.metaKey) {
            if (e.key === '1') showView('task');
            else if (e.key === '2') showView('history');
            else if (e.key === '3') showView('settings');
        }
    });
}

function showView(viewName) {
    state.currentView = viewName;
    
    // Update navigation tabs
    document.querySelectorAll('[data-view]').forEach(button => {
        if (button.dataset.view === viewName) {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });
    
    // Show/hide view content
    document.querySelectorAll('.view').forEach(view => {
        if (view.id === `${viewName}-view`) {
            view.classList.remove('hidden');
        } else {
            view.classList.add('hidden');
        }
    });
}

// Theme management
function setTheme(theme) {
    state.theme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
}

// Notification system
function showNotification(type, message, actionLabel = null, actionCallback = null) {
    // Simple notification implementation
    // Could be replaced with a library like Notyf
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    if (actionLabel && actionCallback) {
        const button = document.createElement('button');
        button.textContent = actionLabel;
        button.onclick = () => {
            actionCallback();
            notification.remove();
        };
        notification.appendChild(button);
    }
    
    document.body.appendChild(notification);
    
    setTimeout(() => notification.remove(), 5000);
}

// Start application when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}
```

### Threading Implementation

#### GUI Task Manager Threading

```python
# src/gui/gui_task_manager.py
import threading
import time
from typing import Callable
from datetime import datetime
import uuid

class GUITaskManager:
    def __init__(self, config):
        self.config = config
        self.task_executor = TaskExecutor(config)
        self.current_thread = None
        self.stop_flag = threading.Event()
        self.current_task_id = None
        self.start_time = None
        
    def run_task(self, task_description: str, progress_callback: Callable) -> str:
        """Execute task in separate thread"""
        if self.is_running():
            raise TaskAlreadyRunningError("A task is already running")
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        self.current_task_id = task_id
        self.start_time = datetime.now()
        
        # Clear stop flag
        self.stop_flag.clear()
        
        # Create and start thread
        self.current_thread = threading.Thread(
            target=self._execute_task,
            args=(task_id, task_description, progress_callback),
            daemon=True
        )
        self.current_thread.start()
        
        return task_id
    
    def _execute_task(self, task_id: str, task_description: str, 
                      progress_callback: Callable):
        """Internal method that runs in separate thread"""
        try:
            # Notify start
            progress_callback('start', {
                'task_id': task_id,
                'description': task_description
            })
            
            # Wrapper callback that checks stop flag
            def monitored_callback(message: str, message_type: str = 'info'):
                # Check if task should stop
                if self.stop_flag.is_set():
                    raise TaskCancelledException("Task was cancelled by user")
                
                # Send progress update
                progress_callback('progress', {
                    'message': message,
                    'type': message_type,
                    'timestamp': datetime.now().isoformat()
                })
            
            # Execute task with monitored callback
            result = self.task_executor.execute(
                task_description,
                progress_callback=monitored_callback,
                stop_flag=self.stop_flag
            )
            
            # Calculate duration
            duration = (datetime.now() - self.start_time).total_seconds()
            
            # Notify completion
            progress_callback('complete', {
                'task_id': task_id,
                'result': result,
                'duration': duration,
                'output': result.get('output', '')
            })
            
        except TaskCancelledException:
            progress_callback('error', {
                'task_id': task_id,
                'error': 'Task was cancelled',
                'duration': (datetime.now() - self.start_time).total_seconds()
            })
            
        except Exception as e:
            # Handle errors
            import traceback
            progress_callback('error', {
                'task_id': task_id,
                'error_type': type(e).__name__,
                'error': str(e),
                'traceback': traceback.format_exc(),
                'duration': (datetime.now() - self.start_time).total_seconds()
            })
            
        finally:
            # Cleanup
            self.current_thread = None
            self.current_task_id = None
            self.start_time = None
    
    def stop_task(self) -> bool:
        """Signal task to stop"""
        if not self.is_running():
            return False
        
        self.stop_flag.set()
        return True
    
    def is_running(self) -> bool:
        """Check if task is running"""
        return self.current_thread is not None and self.current_thread.is_alive()
```

### Progress Update Mechanism

Progress updates flow from backend to frontend:

1. **Backend emits progress**:
   ```python
   progress_callback("Analyzing file: main.py", "info")
   ```

2. **GUITaskManager wraps and forwards**:
   ```python
   progress_callback('progress', {
       'message': "Analyzing file: main.py",
       'type': 'info',
       'timestamp': datetime.now().isoformat()
   })
   ```

3. **Eel bridge sends to JavaScript**:
   ```python
   eel.update_progress({
       'message': "Analyzing file: main.py",
       'type': 'info',
       'timestamp': '2024-01-15T14:32:45.123456'
   })
   ```

4. **JavaScript receives and updates UI**:
   ```javascript
   window.update_progress = function(data) {
       ProgressDisplay.addMessage(data.type, data.message, data.timestamp);
   };
   ```

**Performance Optimization**: If updates are too frequent (>30/second), implement batching:

```python
class ProgressBatcher:
    def __init__(self, callback, batch_interval=0.033):  # 30 fps
        self.callback = callback
        self.batch_interval = batch_interval
        self.pending_messages = []
        self.last_send = time.time()
        self.lock = threading.Lock()
        
    def add_message(self, message_type, message):
        with self.lock:
            self.pending_messages.append({
                'type': message_type,
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
            
            # Send if interval elapsed
            if time.time() - self.last_send >= self.batch_interval:
                self._flush()
    
    def _flush(self):
        if self.pending_messages:
            self.callback('progress_batch', {
                'messages': self.pending_messages
            })
            self.pending_messages = []
            self.last_send = time.time()
```

### History Persistence Implementation

**Database Schema**:

```sql
-- src/gui/schema.sql
CREATE TABLE IF NOT EXISTS history_entries (
    entry_id TEXT PRIMARY KEY,
    task_description TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    duration_seconds REAL,
    status TEXT NOT NULL CHECK(status IN ('success', 'failed', 'cancelled')),
    output TEXT,
    error_message TEXT,
    config_snapshot TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_timestamp ON history_entries(timestamp DESC);
CREATE INDEX idx_status ON history_entries(status);
CREATE INDEX idx_task_description ON history_entries(task_description);

-- Full-text search (optional, for better search performance)
CREATE VIRTUAL TABLE IF NOT EXISTS history_fts USING fts5(
    entry_id UNINDEXED,
    task_description,
    output
);
```

**History Manager Implementation**:

```python
# src/gui/gui_history_manager.py
import sqlite3
import json
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class HistoryEntry:
    entry_id: str
    task_description: str
    timestamp: datetime
    duration_seconds: float
    status: str
    output: str
    error_message: Optional[str]
    config_snapshot: dict

class GUIHistoryManager:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Platform-specific data directory
            if sys.platform == 'win32':
                base = Path(os.environ['APPDATA'])
            elif sys.platform == 'darwin':
                base = Path.home() / 'Library' / 'Application Support'
            else:
                base = Path.home() / '.local' / 'share'
            
            db_path = base / 'local-ai-dev' / 'history.db'
            db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.db_path = str(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Read schema from file
        schema_path = Path(__file__).parent / 'schema.sql'
        with open(schema_path) as f:
            cursor.executescript(f.read())
        
        conn.commit()
        conn.close()
    
    def add_entry(self, entry: HistoryEntry) -> str:
        """Add new history entry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO history_entries 
            (entry_id, task_description, timestamp, duration_seconds, 
             status, output, error_message, config_snapshot)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.entry_id,
            entry.task_description,
            entry.timestamp.isoformat(),
            entry.duration_seconds,
            entry.status,
            entry.output,
            entry.error_message,
            json.dumps(entry.config_snapshot)
        ))
        
        # Also add to FTS table for search
        cursor.execute("""
            INSERT INTO history_fts (entry_id, task_description, output)
            VALUES (?, ?, ?)
        """, (entry.entry_id, entry.task_description, entry.output))
        
        conn.commit()
        conn.close()
        
        return entry.entry_id
    
    def get_entries(self, limit: int = 100, search_query: Optional[str] = None,
                   status_filter: Optional[str] = None) -> List[HistoryEntry]:
        """Retrieve history entries with filtering"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build query
        if search_query:
            # Use FTS for search
            query = """
                SELECT h.* FROM history_entries h
                JOIN history_fts fts ON h.entry_id = fts.entry_id
                WHERE history_fts MATCH ?
            """
            params = [search_query]
        else:
            query = "SELECT * FROM history_entries WHERE 1=1"
            params = []
        
        # Add status filter
        if status_filter and status_filter != 'all':
            query += " AND status = ?"
            params.append(status_filter)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to HistoryEntry objects
        entries = []
        for row in rows:
            entries.append(HistoryEntry(
                entry_id=row[0],
                task_description=row[1],
                timestamp=datetime.fromisoformat(row[2]),
                duration_seconds=row[3],
                status=row[4],
                output=row[5],
                error_message=row[6],
                config_snapshot=json.loads(row[7])
            ))
        
        return entries
```

### Packaging with PyInstaller

**PyInstaller Spec File** (`build/pyinstaller/local-ai-dev.spec`):

```python
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Determine platform
IS_WINDOWS = sys.platform == 'win32'
IS_MACOS = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')

# Paths
src_path = Path('../../src').resolve()
web_path = src_path / 'web'
assets_path = web_path / 'assets'

# Icon file
if IS_WINDOWS:
    icon_file = str(assets_path / 'icon.ico')
elif IS_MACOS:
    icon_file = str(assets_path / 'icon.icns')
else:
    icon_file = str(assets_path / 'icon.png')

block_cipher = None

a = Analysis(
    [str(src_path / 'gui' / 'gui_app.py')],
    pathex=[],
    binaries=[],
    datas=[
        # Include all web files
        (str(web_path), 'web'),
        # Include config example
        ('../../config.example.yaml', '.'),
    ],
    hiddenimports=[
        'eel',
        'bottle',
        'bottle_websocket',
        'gevent',
        'geventwebsocket',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='local-ai-dev',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='local-ai-dev',
)

# macOS app bundle
if IS_MACOS:
    app = BUNDLE(
        coll,
        name='Local AI Dev.app',
        icon=icon_file,
        bundle_identifier='com.localaidev.app',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '1.0.0',
        },
    )
```

**Build Script** (`build/build.py`):

```python
#!/usr/bin/env python3
"""Build script for creating executables"""

import sys
import os
import shutil
import subprocess
from pathlib import Path

def build_icons():
    """Generate icon files from SVG source"""
    print("Building icons...")
    
    # This would use tools like ImageMagick, png2icns, etc.
    # For now, assume icons are already created
    
    pass

def build_executable():
    """Build executable using PyInstaller"""
    print(f"Building for platform: {sys.platform}")
    
    spec_file = Path('pyinstaller/local-ai-dev.spec')
    
    cmd = [
        'pyinstaller',
        '--clean',
        '--noconfirm',
        str(spec_file)
    ]
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    if result.returncode != 0:
        print("Build failed!")
        sys.exit(1)
    
    print("Build successful!")

def create_installer():
    """Create platform-specific installer"""
    if sys.platform == 'win32':
        print("Creating Windows installer with NSIS...")
        # Run NSIS script
        pass
    elif sys.platform == 'darwin':
        print("Creating macOS installer...")
        # Run pkgbuild or create DMG
        pass
    else:
        print("Creating Linux AppImage...")
        # Create AppImage
        pass

if __name__ == '__main__':
    build_icons()
    build_executable()
    create_installer()
```



## Error Handling

### Error Categories

#### 1. User Input Errors

**Validation Errors**:
- Invalid configuration values (malformed URLs, out-of-range numbers)
- Empty required fields
- File paths that don't exist

**Handling Strategy**:
- Client-side validation (immediate feedback)
- Server-side validation (security and correctness)
- Clear error messages with suggestions
- Highlight invalid fields visually
- Prevent form submission until valid

**Example**:
```javascript
// JavaScript validation
function validateEndpoint(url) {
    if (!url) {
        return { valid: false, error: 'Endpoint cannot be empty' };
    }
    try {
        new URL(url);
        return { valid: true };
    } catch {
        return { valid: false, error: 'Invalid URL format. Example: http://localhost:11434' };
    }
}
```

```python
# Python validation
def validate_endpoint(url: str) -> tuple[bool, Optional[str]]:
    if not url:
        return False, "Endpoint cannot be empty"
    
    try:
        parsed = urlparse(url)
        if not parsed.scheme in ['http', 'https']:
            return False, "URL must start with http:// or https://"
        if not parsed.netloc:
            return False, "URL must include hostname"
        return True, None
    except Exception as e:
        return False, f"Invalid URL: {str(e)}"
```

#### 2. Backend Errors

**LLM Connection Errors**:
- Server unreachable
- Connection timeout
- Authentication failure

**Handling Strategy**:
- Detect specific error types
- Provide actionable error messages
- Suggest troubleshooting steps
- Link to documentation

**Example Error Messages**:
```
❌ Could not connect to LLM server

The application cannot reach the LLM server at http://localhost:11434

Possible causes:
• The LLM server is not running
• The endpoint URL is incorrect
• A firewall is blocking the connection

Try this:
• Verify the server is running: ollama list
• Check the endpoint in Settings
• Review the documentation: [link]

[Retry] [Open Settings] [Help]
```

**Task Execution Errors**:
- File permission denied
- Out of disk space
- Code syntax errors
- Test failures

**Handling Strategy**:
- Display full error message in Progress Display
- Highlight error type (syntax, permission, etc.)
- Provide context (which file, which operation)
- Allow user to review and retry

#### 3. System Errors

**File System Errors**:
- Config file corrupted
- Database locked
- Insufficient permissions

**Handling Strategy**:
- Automatic backup restoration for config
- Database retry logic with exponential backoff
- Clear error messages with file paths
- Graceful degradation where possible

**Memory/Resource Errors**:
- Out of memory
- Too many threads
- Disk full

**Handling Strategy**:
- Monitor resource usage
- Warn before critical levels
- Graceful degradation (disable features if needed)
- Clear explanation of the problem

#### 4. Unexpected Errors

**Crash Handling**:
- Uncaught exceptions
- Segmentation faults
- Python interpreter errors

**Handling Strategy**:
- Global exception handler
- Log error to file before exit
- Show crash dialog with option to report bug
- Preserve user's work (auto-save)

**Example Crash Handler**:
```python
import sys
import traceback
from datetime import datetime

def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler"""
    # Log to file
    log_file = Path.home() / '.local-ai-dev' / 'crash_logs' / f'crash_{datetime.now().isoformat()}.log'
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, 'w') as f:
        f.write(f"Crash at {datetime.now()}\n")
        f.write(f"Exception: {exc_type.__name__}: {exc_value}\n\n")
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    
    # Show error dialog
    eel.show_crash_dialog({
        'error_type': exc_type.__name__,
        'error_message': str(exc_value),
        'log_file': str(log_file)
    })

sys.excepthook = handle_uncaught_exception
```

### Error Dialog Design

**Error Dialog Components**:
- Error icon (⚠️ for warnings, ❌ for errors)
- Clear headline ("Connection Failed", "Task Error", etc.)
- Detailed explanation
- Suggested actions (buttons or links)
- Technical details (expandable section)
- Copy to clipboard button

**Example Error Dialog Structure**:
```
┌─────────────────────────────────────────────┐
│ ❌ Task Execution Failed                    │
├─────────────────────────────────────────────┤
│                                             │
│ The task could not be completed due to a   │
│ syntax error in the generated code.        │
│                                             │
│ File: src/calculator.py                    │
│ Line 15: unexpected indent                 │
│                                             │
│ [▼ Show Technical Details]                 │
│                                             │
│ What would you like to do?                 │
│                                             │
│ [Retry Task] [Edit Config] [Copy Error]   │
│ [Report Bug] [Close]                       │
└─────────────────────────────────────────────┘
```

### Logging Strategy

**Log Levels**:
- **DEBUG**: Detailed diagnostic information
- **INFO**: Confirmation of expected operations
- **WARNING**: Something unexpected but not critical
- **ERROR**: A failure occurred but app continues
- **CRITICAL**: Serious error, app may terminate

**Log Files**:
- Main log: `~/.local-ai-dev/logs/app.log`
- Crash logs: `~/.local-ai-dev/crash_logs/crash_YYYY-MM-DD_HH-MM-SS.log`
- Task logs: Stored in history database

**Log Rotation**:
- Keep last 10 log files
- Max 10 MB per file
- Automatic compression of old logs

## Testing Strategy

### Testing Approach

The Desktop GUI Application feature requires a **multi-layered testing strategy** that combines:
- **Unit tests** for pure functions and business logic
- **Integration tests** for component interactions
- **End-to-end tests** for complete workflows
- **Manual testing** for UI/UX validation

**Property-Based Testing (PBT) is NOT the primary testing approach for this feature** because:

1. **UI Components**: HTML/CSS/JavaScript rendering and interaction are not suitable for PBT
2. **Side Effects**: File I/O, database operations, and threading involve external state
3. **Integration Layer**: The Eel bridge and IPC mechanisms require integration testing
4. **User Experience**: Visual design, responsiveness, and usability require manual testing

However, **PBT IS applicable** to specific pure functions within the feature:
- Configuration validation functions
- Data serialization/deserialization
- Input sanitization and formatting

### Unit Testing

**Backend Python Tests**:

Test each Python module independently:

**GUIConfigManager Tests**:
```python
# tests/gui/test_gui_config_manager.py

def test_validate_endpoint_accepts_valid_urls():
    """Valid URLs should pass validation"""
    manager = GUIConfigManager()
    
    valid_urls = [
        "http://localhost:11434",
        "https://example.com:8080",
        "http://192.168.1.1:3000"
    ]
    
    for url in valid_urls:
        is_valid, error = manager.validate_field('llm.endpoint', url)
        assert is_valid, f"URL {url} should be valid but got error: {error}"

def test_validate_endpoint_rejects_invalid_urls():
    """Invalid URLs should fail validation"""
    manager = GUIConfigManager()
    
    invalid_urls = [
        "",
        "not a url",
        "ftp://example.com",
        "http://",
        "localhost:11434"  # missing scheme
    ]
    
    for url in invalid_urls:
        is_valid, error = manager.validate_field('llm.endpoint', url)
        assert not is_valid, f"URL {url} should be invalid"
        assert error is not None

def test_validate_temperature_range():
    """Temperature must be between 0.0 and 1.0"""
    manager = GUIConfigManager()
    
    # Valid values
    for temp in [0.0, 0.5, 1.0]:
        is_valid, error = manager.validate_field('llm.temperature', temp)
        assert is_valid
    
    # Invalid values
    for temp in [-0.1, 1.1, 2.0]:
        is_valid, error = manager.validate_field('llm.temperature', temp)
        assert not is_valid

def test_config_save_creates_backup():
    """Saving config should create backup file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'config.yaml'
        # Create initial config
        with open(config_path, 'w') as f:
            f.write("llm:\n  endpoint: http://localhost:11434\n")
        
        manager = GUIConfigManager(str(config_path))
        manager.save_config({'llm': {'endpoint': 'http://localhost:8080'}})
        
        backup_path = Path(tmpdir) / 'config.yaml.backup'
        assert backup_path.exists()

def test_config_save_is_atomic():
    """Config save should be atomic (all-or-nothing)"""
    # Test that partial writes don't corrupt config
    # This would involve simulating failures during write
    pass
```

**GUITaskManager Tests**:
```python
# tests/gui/test_gui_task_manager.py

def test_run_task_starts_thread():
    """Running a task should start a background thread"""
    config = Config.load("config.yaml")
    manager = GUITaskManager(config)
    
    callback_called = threading.Event()
    
    def callback(event_type, data):
        if event_type == 'start':
            callback_called.set()
    
    task_id = manager.run_task("Test task", callback)
    
    assert manager.is_running()
    assert task_id is not None
    assert callback_called.wait(timeout=5)

def test_cannot_run_concurrent_tasks():
    """Only one task should run at a time"""
    config = Config.load("config.yaml")
    manager = GUITaskManager(config)
    
    manager.run_task("Task 1", lambda t, d: None)
    
    with pytest.raises(TaskAlreadyRunningError):
        manager.run_task("Task 2", lambda t, d: None)

def test_stop_task_sets_flag():
    """Stopping a task should set the stop flag"""
    config = Config.load("config.yaml")
    manager = GUITaskManager(config)
    
    manager.run_task("Test task", lambda t, d: None)
    result = manager.stop_task()
    
    assert result is True
    assert manager.stop_flag.is_set()
```

**GUIHistoryManager Tests**:
```python
# tests/gui/test_gui_history_manager.py

def test_add_and_retrieve_entry():
    """Adding an entry should make it retrievable"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / 'history.db'
        manager = GUIHistoryManager(str(db_path))
        
        entry = HistoryEntry(
            entry_id="test-123",
            task_description="Test task",
            timestamp=datetime.now(),
            duration_seconds=10.5,
            status="success",
            output="Test output",
            error_message=None,
            config_snapshot={}
        )
        
        manager.add_entry(entry)
        
        entries = manager.get_entries(limit=10)
        assert len(entries) == 1
        assert entries[0].entry_id == "test-123"

def test_search_filters_entries():
    """Search should filter by task description"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / 'history.db'
        manager = GUIHistoryManager(str(db_path))
        
        # Add multiple entries
        for i in range(5):
            entry = HistoryEntry(
                entry_id=f"test-{i}",
                task_description=f"Task {i}" if i % 2 == 0 else f"Other {i}",
                timestamp=datetime.now(),
                duration_seconds=10.0,
                status="success",
                output="",
                error_message=None,
                config_snapshot={}
            )
            manager.add_entry(entry)
        
        # Search for "Task"
        results = manager.get_entries(search_query="Task")
        assert len(results) == 3  # 0, 2, 4

def test_purge_old_entries():
    """Purging should remove entries older than specified days"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / 'history.db'
        manager = GUIHistoryManager(str(db_path))
        
        # Add old entry
        old_entry = HistoryEntry(
            entry_id="old",
            task_description="Old task",
            timestamp=datetime.now() - timedelta(days=100),
            duration_seconds=10.0,
            status="success",
            output="",
            error_message=None,
            config_snapshot={}
        )
        manager.add_entry(old_entry)
        
        # Add recent entry
        recent_entry = HistoryEntry(
            entry_id="recent",
            task_description="Recent task",
            timestamp=datetime.now(),
            duration_seconds=10.0,
            status="success",
            output="",
            error_message=None,
            config_snapshot={}
        )
        manager.add_entry(recent_entry)
        
        # Purge entries older than 90 days
        deleted = manager.purge_old_entries(days=90)
        assert deleted == 1
        
        entries = manager.get_entries()
        assert len(entries) == 1
        assert entries[0].entry_id == "recent"
```

### Property-Based Testing (Limited Scope)

**Configuration Validation Properties**:

```python
# tests/properties/test_config_validation_properties.py
from hypothesis import given, strategies as st

@given(st.text())
def test_validate_endpoint_accepts_only_valid_urls(url):
    """Property: Only well-formed HTTP(S) URLs should pass validation"""
    manager = GUIConfigManager()
    is_valid, error = manager.validate_field('llm.endpoint', url)
    
    # If valid, should be a proper HTTP(S) URL
    if is_valid:
        assert url.startswith('http://') or url.startswith('https://')
        # Should be parseable by urlparse
        from urllib.parse import urlparse
        parsed = urlparse(url)
        assert parsed.netloc  # Must have a hostname

@given(st.floats(min_value=0.0, max_value=1.0))
def test_validate_temperature_accepts_valid_range(temperature):
    """Property: All floats in [0.0, 1.0] should be valid temperatures"""
    manager = GUIConfigManager()
    is_valid, error = manager.validate_field('llm.temperature', temperature)
    assert is_valid

@given(st.floats())
def test_validate_temperature_rejects_outside_range(temperature):
    """Property: Floats outside [0.0, 1.0] should be rejected"""
    from hypothesis import assume
    assume(temperature < 0.0 or temperature > 1.0)
    
    manager = GUIConfigManager()
    is_valid, error = manager.validate_field('llm.temperature', temperature)
    assert not is_valid
    assert error is not None
```

**History Entry Serialization Properties**:

```python
# tests/properties/test_history_serialization_properties.py
from hypothesis import given, strategies as st
import json

# Strategy for generating HistoryEntry objects
@st.composite
def history_entry_strategy(draw):
    return HistoryEntry(
        entry_id=draw(st.uuids()).hex,
        task_description=draw(st.text(min_size=1, max_size=500)),
        timestamp=datetime.now(),
        duration_seconds=draw(st.floats(min_value=0.0, max_value=3600.0)),
        status=draw(st.sampled_from(['success', 'failed', 'cancelled'])),
        output=draw(st.text(max_size=1000)),
        error_message=draw(st.one_of(st.none(), st.text(max_size=200))),
        config_snapshot={}
    )

@given(history_entry_strategy())
def test_history_entry_database_round_trip(entry):
    """Property: Any history entry can be saved and retrieved unchanged"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / 'test.db'
        manager = GUIHistoryManager(str(db_path))
        
        # Save entry
        manager.add_entry(entry)
        
        # Retrieve entry
        retrieved = manager.get_entry_by_id(entry.entry_id)
        
        # Should match original
        assert retrieved is not None
        assert retrieved.entry_id == entry.entry_id
        assert retrieved.task_description == entry.task_description
        assert retrieved.status == entry.status
        # Note: timestamps may have precision differences, so compare as strings
        assert retrieved.timestamp.isoformat()[:19] == entry.timestamp.isoformat()[:19]
```

### Integration Testing

**Eel Communication Tests**:

Test the Python-JavaScript bridge:

```python
# tests/integration/test_eel_communication.py

def test_run_task_calls_javascript_callback(selenium_driver):
    """Running a task should trigger JavaScript callbacks"""
    # Start GUI app in test mode
    app_process = start_test_gui()
    
    # Use Selenium to interact with the web interface
    driver = selenium_driver
    driver.get("http://localhost:8080")
    
    # Enter task description
    task_input = driver.find_element(By.ID, "task-description")
    task_input.send_keys("Test task")
    
    # Click run button
    run_button = driver.find_element(By.ID, "run-button")
    run_button.click()
    
    # Wait for progress messages
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "progress-message"))
    )
    
    # Verify progress was displayed
    messages = driver.find_elements(By.CLASS_NAME, "progress-message")
    assert len(messages) > 0
    
    app_process.terminate()
```

**Config Save/Load Tests**:

```python
# tests/integration/test_config_persistence.py

def test_config_changes_persist_across_restarts():
    """Config changes should survive app restart"""
    # Start app, change config, close
    # Start app again, verify config was saved
    pass
```

### End-to-End Testing

**Complete Workflow Tests**:

```python
# tests/e2e/test_complete_workflows.py

def test_complete_task_execution_workflow():
    """Complete workflow: enter task, run, view progress, check history"""
    # 1. Start application
    # 2. Enter task description
    # 3. Click run
    # 4. Wait for completion
    # 5. Verify success message
    # 6. Switch to history view
    # 7. Verify task appears in history
    # 8. Re-run task from history
    # 9. Verify second execution
    pass

def test_config_modification_workflow():
    """Complete workflow: open settings, change values, save, verify applied"""
    # 1. Start application
    # 2. Open settings
    # 3. Change LLM endpoint
    # 4. Save
    # 5. Verify config file updated
    # 6. Run a task
    # 7. Verify task uses new config
    pass
```

### Manual Testing Checklist

**UI/UX Testing**:
- [ ] Visual consistency across views
- [ ] Color contrast meets WCAG AA standards
- [ ] Fonts are readable at all sizes
- [ ] Buttons have clear hover/focus states
- [ ] Animations are smooth (60fps)
- [ ] Layout works at 800x600 minimum
- [ ] Layout works at 3840x2160 maximum
- [ ] Window resize works smoothly
- [ ] Theme switching works correctly

**Platform Testing**:
- [ ] Windows 10, 11 (32-bit and 64-bit)
- [ ] macOS 10.14+
- [ ] Ubuntu 20.04+ (or equivalent Linux distros)
- [ ] Different DPI settings (100%, 125%, 150%, 200%)

**Functionality Testing**:
- [ ] Task execution completes successfully
- [ ] Task cancellation works
- [ ] Real-time progress updates appear
- [ ] Config saves correctly
- [ ] Invalid config values rejected
- [ ] History displays correctly
- [ ] History search works
- [ ] History export works
- [ ] Application icon appears correctly
- [ ] Minimize to tray works (if enabled)
- [ ] Keyboard shortcuts work

**Error Handling Testing**:
- [ ] LLM server unreachable
- [ ] Invalid API key
- [ ] Config file corrupted
- [ ] Disk full
- [ ] Out of memory
- [ ] Network disconnected (during web research)
- [ ] Concurrent CLI and GUI usage

### Testing Summary

**Test Coverage Goals**:
- Unit tests: 85%+ code coverage for Python modules
- Integration tests: All major component interactions
- End-to-end tests: Critical user workflows
- Property tests: Pure validation and serialization functions
- Manual tests: Complete UI/UX validation

**Continuous Testing**:
- Run unit tests on every commit
- Run integration tests before releases
- Run end-to-end tests on release candidates
- Manual testing for each platform build

**Test Configuration**:
```yaml
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --cov=src/gui
    --cov-report=html
    --cov-report=term
    --hypothesis-profile=ci

[tool:pytest]
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    property: Property-based tests
    gui: GUI-specific tests
    slow: Slow-running tests

# Hypothesis settings for property tests
[hypothesis]
profiles =
    default:
        max_examples = 100
        deadline = None
    ci:
        max_examples = 200
        deadline = None
    thorough:
        max_examples = 1000
        deadline = None
```

## Conclusion

This design provides a comprehensive architecture for the Desktop GUI Application feature that:

1. **Seamlessly integrates** with existing backend code without modification
2. **Uses modern web technologies** for a flexible, attractive UI
3. **Maintains responsiveness** through proper threading and async patterns
4. **Provides excellent UX** with real-time feedback and clear error handling
5. **Works cross-platform** with platform-specific optimizations
6. **Is maintainable** with clear separation of concerns and comprehensive testing

The implementation follows best practices for desktop application development while leveraging the power of web technologies for the UI layer. The Eel framework provides the perfect bridge between Python and web technologies, allowing rapid development of a modern desktop application.

### Next Steps

1. **Implementation Phase**: Follow the design to implement GUI components
2. **Testing Phase**: Write tests as specified in the testing strategy
3. **Icon Design**: Create the application icon in required formats
4. **Build Configuration**: Set up PyInstaller and create installers
5. **Documentation**: Update user documentation with GUI instructions
6. **Beta Testing**: Gather feedback from users before final release

