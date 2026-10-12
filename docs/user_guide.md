# Desktop GUI User Guide

Welcome to the Local AI Development Environment Desktop GUI Application! This guide will help you get started and make the most of the application's features.

## Table of Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [First Run Setup](#first-run-setup)
- [Task Execution](#task-execution)
- [Settings](#settings)
- [History](#history)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

## Introduction

The Local AI Development Environment Desktop GUI provides a user-friendly graphical interface for autonomous AI-powered development tasks. The application:

- **Runs Entirely Locally**: Your code never leaves your machine
- **Easy to Use**: Intuitive interface with tabs for Tasks, History, and Settings
- **Real-Time Progress**: Watch your tasks execute with live progress updates
- **Task History**: Track all completed tasks with search and filtering
- **Flexible Configuration**: Customize LLM settings, project paths, and feature flags
- **Cross-Platform**: Works on Windows, macOS, and Linux

The GUI wraps all the power of the CLI tool in an accessible interface, perfect for users who prefer visual applications over command-line tools.

## Installation

### Windows

1. **Download the Installer**: Get `LocalAIDev-Setup.exe` from the releases page
2. **Run the Installer**: Double-click the installer and follow the prompts
3. **Choose Install Location**: Select where to install (default: `C:\Program Files\LocalAIDev\`)
4. **Create Shortcuts**: Optionally create desktop and Start menu shortcuts
5. **Launch**: Click "Finish" to launch the application, or find it in your Start menu

**System Requirements:**
- Windows 10 or Windows 11
- 8 GB RAM minimum (16 GB recommended)
- 500 MB free disk space for application
- Additional space for LLM models (varies by model)

### macOS

1. **Download the Package**: Get `LocalAIDev.pkg` from the releases page
2. **Open the Package**: Double-click to open the installer
3. **Follow Installer**: Follow the macOS installer prompts
4. **Grant Permissions**: Allow the app in System Preferences > Security & Privacy if prompted
5. **Launch**: Find "Local AI Dev" in Applications folder

**System Requirements:**
- macOS 10.15 (Catalina) or later
- 8 GB RAM minimum (16 GB recommended)
- 500 MB free disk space for application
- Additional space for LLM models (varies by model)

### Linux

#### Debian/Ubuntu (Using Installation Script)

1. **Download the Package**: Get the Linux distribution archive
2. **Extract the Archive**: `tar -xzf LocalAIDev-linux.tar.gz`
3. **Run Installer**: `bash LocalAIDev/build/installers/linux-install.sh`
4. **Choose Install Type**: Select user-only (`~/.local/share/`) or system-wide (`/opt/`, requires sudo)
5. **Launch**: Find "Local AI Dev" in your application menu, or run `localaidev` from terminal

**System Requirements:**
- Ubuntu 20.04+, Debian 11+, or equivalent distribution
- 8 GB RAM minimum (16 GB recommended)
- 500 MB free disk space for application
- Additional space for LLM models (varies by model)

#### Other Distributions

For Fedora, Arch, and other distributions, use the generic installation script or run directly from the extracted executable:

```bash
cd LocalAIDev
./LocalAIDev
```

### Installing from Source

For developers or advanced users who want to run from source:

```bash
# Clone repository
git clone <repository-url>
cd local-ai-dev-environment

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-gui.txt

# Run GUI
python -m src.gui.gui_app
```

## First Run Setup

When you launch the application for the first time, a setup wizard guides you through initial configuration.

### Setup Wizard Steps

#### 1. Welcome Screen

The wizard explains what needs to be configured:
- LLM endpoint connection
- Model selection
- Working directory

Click "Next" to continue.

#### 2. LLM Endpoint Configuration

**LLM Endpoint URL:**
- Enter the URL where your local LLM server is running
- Common examples:
  - Ollama: `http://localhost:11434`
  - llama.cpp server: `http://localhost:8080`
  - Other OpenAI-compatible servers: `http://localhost:<port>`
- The endpoint must be accessible from your machine

**Model Name:**
- Enter the name of the model to use
- For Ollama: Use format like `codellama:13b`, `llama2:7b`, `mistral:7b`
- For llama.cpp: Use the model filename or identifier
- Ensure the model is already downloaded/available on your LLM server

**Backend Type:**
- Select the type of LLM backend:
  - **Ollama**: If using Ollama (recommended for beginners)
  - **llama.cpp**: If using llama.cpp server
  - **OpenAI-compatible**: For other servers implementing OpenAI API format

**Test Connection:**
- Click "Test Connection" to verify the LLM is accessible
- A successful connection shows a green checkmark
- If the test fails, verify:
  - LLM server is running
  - Endpoint URL is correct
  - No firewall blocking the connection

#### 3. Project Settings

**Project Root Directory:**
- Click "Browse" to select your working directory
- This is where the AI will create and modify files
- Choose an existing project or an empty directory for new projects
- The application needs write permissions in this directory

**Recommended:**
- Use a dedicated directory for testing
- Ensure the directory is backed up or under version control
- Don't point to sensitive system directories

#### 4. Review and Save

- Review all settings
- Click "Save and Continue" to complete setup
- Configuration is saved to a platform-specific location:
  - Windows: `%APPDATA%\local-ai-dev\config.yaml`
  - macOS: `~/Library/Application Support/local-ai-dev/config.yaml`
  - Linux: `~/.config/local-ai-dev/config.yaml`

After setup completes, the main application window opens with the Task view.

### Skipping Setup

If you need to exit setup:
- Click "Skip for Now" (if available)
- Or close the setup window
- Note: Task execution requires valid configuration, so you'll need to complete setup in Settings before running tasks

## Task Execution

The Task view is the primary interface for running development tasks.

### Running a Task

#### 1. Enter Task Description

In the **Task Input** panel:
- Type or paste your task description
- Be specific about what you want the AI to do
- Maximum 5000 characters
- Character count shown in bottom-right corner

**Example Task Descriptions:**

Simple tasks:
```
Create a Python script called hello.py that prints "Hello, World!"
```

Complex tasks:
```
Create a REST API using Flask with the following endpoints:
- GET /api/users - list all users
- POST /api/users - create a new user
- GET /api/users/<id> - get a specific user
- PUT /api/users/<id> - update a user
- DELETE /api/users/<id> - delete a user

Include input validation, error handling, and unit tests for all endpoints.
```

Refactoring tasks:
```
Refactor the authentication module to use JWT tokens instead of session cookies.
Update all affected endpoints and add integration tests.
```

#### 2. Run the Task

**Methods to Run:**
- Click the **"Run Task"** button
- Press `Ctrl+Enter` (Windows/Linux) or `Cmd+Enter` (macOS)

**Task Execution Starts:**
- Button changes to "Stop Task"
- Status indicator shows "Running" (orange/yellow)
- Progress messages appear in the output panel below

#### 3. Monitor Progress

The **Progress Output** panel shows real-time updates:

**Message Types:**
- **Info** (blue): General progress information
- **Success** (green): Successful completion of steps
- **Warning** (yellow): Non-critical issues or decisions
- **Error** (red): Problems encountered

**Output Features:**
- **Auto-scroll**: Automatically scrolls to show latest messages (toggle with button)
- **Timestamps**: Each message includes time
- **Syntax Highlighting**: Code snippets are highlighted for readability
- **Copy**: Click "Copy Output" to copy all messages to clipboard
- **Clear**: Click "Clear Output" to remove all messages from view

#### 4. Task Completion

When the task finishes:

**Success:**
- Status indicator shows "Completed" (green)
- Final success message appears
- Task is automatically added to History
- You can run another task

**Error:**
- Status indicator shows "Error" (red)
- Error details appear in red in output
- Task is saved to History with error status
- Review the error to understand what went wrong

**Stopped:**
- If you stopped the task manually (see below)
- Status indicator shows "Stopped" (gray)
- Partial progress is saved to History

### Stopping a Task

If you need to cancel a running task:

**Methods to Stop:**
- Click the **"Stop Task"** button
- Press `Esc` key

**What Happens:**
- Stop signal is sent to the background task
- Task attempts to stop gracefully
- May take a few seconds to fully stop
- Partial results are saved to History

**When to Stop:**
- Task is taking too long
- Task is going in wrong direction
- You need to modify settings
- You realize the task description needs changes

### Task Best Practices

**Clear Descriptions:**
- Be specific about desired outcome
- Mention programming language if applicable
- Specify frameworks or libraries to use
- Include testing requirements if needed

**Scope Management:**
- Break large tasks into smaller, focused tasks
- Test smaller changes before larger refactors
- Verify results in History before moving on

**Iteration:**
- Review task output in History
- Re-run with modifications if needed
- Use History to track what works

## Settings

The Settings view allows you to configure all aspects of the application.

### Opening Settings

**Methods:**
- Click the **Settings** tab in the navigation bar
- Press `Ctrl+,` (Windows/Linux) or `Cmd+,` (macOS)

### LLM Settings

Configure your language model connection:

**LLM Endpoint URL:**
- Format: `http://hostname:port` or `https://hostname:port`
- Example: `http://localhost:11434`
- Must be accessible from your machine
- Validated on save

**Model Name:**
- String identifier for your model
- Examples: `codellama:13b`, `llama2:7b`, `mistral:7b`
- Must exist on your LLM endpoint
- Case-sensitive

**Temperature:**
- Controls randomness in generation
- Range: `0.0` to `2.0`
- Lower values (0.0 - 0.3): More deterministic, better for code
- Higher values (0.7 - 2.0): More creative, better for brainstorming
- Recommended for code: `0.2`

**Max Tokens:**
- Maximum tokens to generate per response
- Range: `1` to `100000`
- Must be ≤ Context Length
- Recommended: `4096` for most tasks
- Higher values allow longer responses but take more time

**Context Length:**
- Total context window size in tokens
- Range: `1` to `100000`
- Must be ≥ Max Tokens
- Depends on your model's capacity
- Common values: `8192`, `16384`, `32768`

**Backend Type:**
- Select your LLM server type
- Options:
  - **ollama**: Ollama server
  - **llamacpp**: llama.cpp server
  - **openai-compatible**: Generic OpenAI API format
- Affects API call format

**Test Connection:**
- Click to verify LLM is accessible
- Shows success (green) or error (red) message
- Use before saving if you changed endpoint settings

### Project Settings

Configure project-related settings:

**Project Root:**
- Absolute path to working directory
- Click "Browse" to select directory
- Must exist and be writable
- All file operations happen within this directory

**Log Level:**
- Controls logging verbosity
- Options:
  - **error**: Only critical errors
  - **warning**: Errors and warnings
  - **info**: General information (recommended)
  - **debug**: Detailed diagnostic information (for troubleshooting)
- Logs saved to platform-specific location

**Excluded Directories:**
- Comma-separated list of directory names to exclude
- Excludes from code search and analysis
- Default: `node_modules, .git, __pycache__, venv, build, dist`
- Pattern matching (e.g., `.*` excludes all hidden directories)

### Feature Flags

Enable or disable advanced features:

**Web Research Enabled:**
- Allows AI to search web for documentation and examples
- Sends search queries to external services (e.g., DuckDuckGo)
- Your code is never sent, only search queries
- Disable for complete offline operation
- Default: `true` (enabled)

**Self-Improvement Enabled:**
- ⚠️ **WARNING**: Advanced feature, use with caution
- Allows system to modify its own code
- Enables self-improvement and adaptation
- Creates automatic backups before changes
- Includes rollback mechanism
- Default: `false` (disabled)
- Only enable if you understand implications

### GUI Settings

Configure GUI-specific options:

**Theme:**
- Select visual theme
- Options:
  - **Light**: Light color scheme
  - **Dark**: Dark color scheme
- Saved across restarts
- Applies immediately

**Enable System Tray:**
- Minimize to system tray instead of closing
- When enabled:
  - Close button minimizes to tray
  - Right-click tray icon for menu
  - Exit from tray menu to fully close
- When disabled:
  - Close button exits application
- Default: `true` (enabled)

### Saving Settings

**Save Changes:**
- Click "Save Settings" button at bottom
- All fields are validated
- Invalid values show error messages
- Configuration is saved to config.yaml
- Confirmation message appears on success

**Reset to Defaults:**
- Click "Reset to Defaults" button
- Restores all settings to default values
- Confirmation dialog prevents accidental resets
- Does not affect History or Tasks

**Validation Errors:**
- Inline error messages appear below invalid fields
- Fix errors before saving
- Hover over info icon (ⓘ) for help

### External Configuration Changes

If config.yaml is modified externally (e.g., text editor):

**Automatic Detection:**
- Application detects changes within 5 seconds
- Reload prompt appears

**Options:**
- **Reload**: Load external changes, discard unsaved GUI changes
- **Keep Current**: Ignore external changes, keep GUI state
- Choose based on which version you want to keep

## History

The History view tracks all executed tasks with search, filtering, and export capabilities.

### Opening History

**Methods:**
- Click the **History** tab in the navigation bar
- Press `Ctrl+H` (Windows/Linux) or `Cmd+H` (macOS)

### Viewing History Entries

**Entry List:**
- Shows all completed tasks (newest first)
- Each entry displays:
  - Task description (truncated if long)
  - Timestamp (when task started)
  - Status badge (Completed, Error, Stopped)
- Click any entry to view details

**Entry Details:**
- Full task description
- Complete output log
- Error messages (if failed)
- Configuration snapshot (settings at time of execution)
- Execution duration

### Searching History

**Search Box:**
- Located at top of History view
- Searches task descriptions
- Real-time filtering as you type
- Case-insensitive
- Matches partial words

**Example Searches:**
- `calculator` - finds all tasks mentioning "calculator"
- `API` - finds all API-related tasks
- `error` - finds tasks with "error" in description

### Filtering History

**Status Filter:**
- Dropdown menu next to search box
- Options:
  - **All**: Show all entries (default)
  - **Completed**: Only successful tasks
  - **Error**: Only failed tasks
  - **Stopped**: Only manually stopped tasks
- Combines with search filter

**Date Range** (if implemented):
- Filter by task execution date
- Select start and end dates
- Shows only tasks within range

### Sorting History

**Sort Order:**
- Dropdown for sort selection
- Options:
  - **Newest First**: Most recent at top (default)
  - **Oldest First**: Earliest at top
  - **Duration**: Longest/shortest tasks first

### Re-running Tasks

To execute a task again with same description:

1. Find the task in History
2. Click the entry to view details
3. Click **"Re-run Task"** button
4. Confirm in dialog (if prompted)
5. Application switches to Task view
6. Task description is pre-filled
7. Click Run to execute

**Use Cases:**
- Task failed, want to try again after fixing issues
- Task succeeded, want to apply to different project
- Refining task based on previous attempt

### Deleting History Entries

**Delete Single Entry:**
1. Click the entry to select it
2. Click **"Delete Entry"** button
3. Confirm in dialog
4. Entry is permanently removed

**Clear All History:**
1. Click **"Clear All History"** button at bottom
2. Confirm in dialog (this is permanent!)
3. All history entries are deleted
4. Cannot be undone

**When to Delete:**
- Remove test tasks
- Clean up failed attempts
- Free up database space
- Maintain privacy

### Exporting History

Export history for backup, analysis, or reporting:

**Export to JSON:**
1. Click **"Export JSON"** button
2. Choose save location in file dialog
3. All visible entries exported (respects filters)
4. File format: JSON array of entry objects
5. Includes all fields (description, output, errors, config)

**Export to CSV:**
1. Click **"Export CSV"** button
2. Choose save location in file dialog
3. All visible entries exported (respects filters)
4. Columns: ID, Description, Timestamp, Status, Duration
5. Output field truncated (first 100 chars)
6. Opens in Excel, Google Sheets, etc.

**Use Cases:**
- Backup before clearing history
- Share results with team
- Analyze task patterns
- Generate reports

## Keyboard Shortcuts

Keyboard shortcuts improve efficiency. All shortcuts work when application has focus.

### Global Shortcuts

| Action | Windows/Linux | macOS |
|--------|---------------|-------|
| Run Task | `Ctrl+Enter` | `Cmd+Enter` |
| Stop Task | `Esc` | `Esc` |
| Open Settings | `Ctrl+,` | `Cmd+,` |
| Open History | `Ctrl+H` | `Cmd+H` |

### View Navigation

| Action | Windows/Linux | macOS |
|--------|---------------|-------|
| Switch to Task View | `Ctrl+1` | `Cmd+1` |
| Switch to History View | `Ctrl+2` | `Cmd+2` |
| Switch to Settings View | `Ctrl+3` | `Cmd+3` |

### Output Actions

| Action | Windows/Linux | macOS |
|--------|---------------|-------|
| Copy Output | `Ctrl+C` | `Cmd+C` |

(Only works when not typing in text fields)

### Dialog Actions

| Action | Windows/Linux | macOS |
|--------|---------------|-------|
| Close Dialog | `Esc` | `Esc` |

### Text Editing

Standard text editing shortcuts work in input fields:

| Action | Windows/Linux | macOS |
|--------|---------------|-------|
| Select All | `Ctrl+A` | `Cmd+A` |
| Cut | `Ctrl+X` | `Cmd+X` |
| Copy | `Ctrl+C` | `Cmd+C` |
| Paste | `Ctrl+V` | `Cmd+V` |
| Undo | `Ctrl+Z` | `Cmd+Z` |
| Redo | `Ctrl+Y` | `Cmd+Shift+Z` |

### Accessibility

All shortcuts are accessible via:
- Keyboard navigation (Tab to move between elements)
- Screen readers (shortcuts are announced)
- Help menu (shortcuts are documented)

For complete shortcuts reference, see [keyboard_shortcuts.md](keyboard_shortcuts.md).

## Troubleshooting

Common issues and solutions:

### Application Won't Start

**Symptom:** Double-clicking application does nothing, or window opens then closes immediately.

**Solutions:**

1. **Check LLM server is running:**
   - Verify your LLM endpoint is accessible
   - For Ollama: `ollama list` to check if service is running
   - For llama.cpp: Check if server process is running

2. **Check logs:**
   - Windows: `%LOCALAPPDATA%\local-ai-dev\logs\`
   - macOS: `~/Library/Logs/local-ai-dev/`
   - Linux: `~/.local/share/local-ai-dev/logs/`
   - Open most recent log file for error messages

3. **Permission issues:**
   - Ensure application has write permissions to config directory
   - On macOS: Check System Preferences > Security & Privacy
   - On Linux: Ensure execute permission: `chmod +x LocalAIDev`

4. **Port conflicts:**
   - Default GUI port is 8080
   - Check if another application is using port 8080
   - Close conflicting application or configure different port

### LLM Connection Errors

**Symptom:** "Could not connect to LLM" error when running tasks or testing connection.

**Solutions:**

1. **Verify endpoint URL:**
   - Open Settings
   - Check LLM Endpoint URL is correct
   - Common formats: `http://localhost:11434` (Ollama), `http://localhost:8080` (llama.cpp)
   - Ensure `http://` or `https://` prefix is included

2. **Check LLM service:**
   - Ollama: `ollama serve` (start service) or `ollama list` (check running)
   - llama.cpp: Ensure server is running with `./server -m model.gguf`
   - Test in browser: Navigate to endpoint URL, should see response (not error)

3. **Firewall blocking:**
   - Check firewall isn't blocking localhost connections
   - Temporarily disable firewall to test
   - Add exception for LLM service port

4. **Model not found:**
   - Verify model name is correct
   - Ollama: `ollama list` to see available models
   - llama.cpp: Check model file exists

### Task Fails Immediately

**Symptom:** Task starts but fails within seconds with an error.

**Solutions:**

1. **Check error message:**
   - Read error in Progress Output panel
   - Common errors:
     - "Invalid task description": Task is too vague or empty
     - "Permission denied": Application can't write to project root
     - "Model error": LLM returned error (context too long, rate limit, etc.)

2. **Check project root:**
   - Open Settings
   - Verify Project Root exists and is writable
   - Browse to select valid directory

3. **Check LLM capacity:**
   - Task might exceed model's context length
   - Try shorter task description
   - Increase Context Length in Settings (if model supports)

4. **Review task description:**
   - Ensure task is clear and specific
   - Break complex tasks into smaller steps
   - Check for special characters or formatting issues

### Configuration Won't Save

**Symptom:** Click "Save Settings" but settings don't persist, or error appears.

**Solutions:**

1. **Fix validation errors:**
   - Red error messages appear below invalid fields
   - Fix all errors before saving
   - Common issues:
     - Temperature out of range (0.0 - 2.0)
     - Max Tokens > Context Length
     - Invalid URL format

2. **Permission issues:**
   - Application needs write access to config directory
   - Windows: Check `%APPDATA%\local-ai-dev\` permissions
   - macOS: Check `~/Library/Application Support/local-ai-dev/` permissions
   - Linux: Check `~/.config/local-ai-dev/` permissions

3. **Config file locked:**
   - Close any text editors with config.yaml open
   - Check no other instance of application is running
   - Restart application

4. **Disk space:**
   - Ensure sufficient disk space available
   - Config file is small but check anyway

### History Not Loading

**Symptom:** History view is empty despite having run tasks, or loading spinner never stops.

**Solutions:**

1. **Check database file:**
   - Windows: `%LOCALAPPDATA%\local-ai-dev\history.db`
   - macOS: `~/Library/Application Support/local-ai-dev/history.db`
   - Linux: `~/.local/share/local-ai-dev/history.db`
   - Ensure file exists and is not corrupted

2. **Database permissions:**
   - Ensure application can read database file
   - Check directory permissions

3. **Corrupted database:**
   - Backup existing database file
   - Delete database file (history will be lost)
   - Restart application (creates new database)

4. **Browser console errors:**
   - Open browser DevTools (F12)
   - Check Console tab for JavaScript errors
   - Report errors as bug if issue persists

### Slow Performance

**Symptom:** Application is sluggish, views take long to load, or input is laggy.

**Solutions:**

1. **Large history:**
   - History with 100+ entries can slow down
   - Export important history entries
   - Clear old history entries
   - Restart application

2. **LLM performance:**
   - Slow LLM responses affect task execution
   - Consider smaller/faster model
   - Check LLM server resource usage (CPU, RAM, GPU)

3. **System resources:**
   - Close other resource-intensive applications
   - Check system RAM usage
   - Ensure adequate free memory (4+ GB recommended)

4. **Task output volume:**
   - Tasks generating huge output can slow UI
   - Clear output regularly (Clear Output button)
   - Use log level "info" instead of "debug"

### System Tray Issues

**Symptom:** Application doesn't appear in system tray, or tray icon doesn't work.

**Solutions:**

1. **System tray disabled:**
   - Open Settings
   - Check "Enable System Tray" is checked
   - Save settings and restart application

2. **System tray not supported:**
   - Some Linux desktop environments don't support system tray
   - Use window close button to exit instead
   - Disable system tray in Settings

3. **Hidden tray icon:**
   - Windows: Click up arrow in taskbar to show hidden icons
   - macOS: Check right side of menu bar
   - Linux: Check system tray area (varies by desktop)

4. **Tray icon not updating:**
   - Right-click tray icon and select "Exit"
   - Restart application
   - Tray icon should show current status

### Reporting Bugs

If you encounter issues not covered here:

1. **Collect information:**
   - Application version (Help > About)
   - Operating system and version
   - LLM backend and model
   - Steps to reproduce issue
   - Error messages from logs

2. **Check logs:**
   - Platform-specific log directories (see above)
   - Include relevant log excerpts

3. **Use bug report feature:**
   - Help > Report Bug
   - Automatically collects diagnostics (excluding sensitive data)
   - Add description of issue
   - Submit report

4. **GitHub issues:**
   - Open issue on project repository
   - Include all collected information
   - Attach log files if possible

## FAQ

### General Questions

**Q: Is my code sent to the cloud?**

A: No. The application runs entirely locally. Your code never leaves your machine. The only network requests are:
- To your local LLM (e.g., localhost)
- Optional web research (only sends search queries, not your code)
- Web research can be disabled in Settings

**Q: Can I use the CLI and GUI together?**

A: Yes. Both share the same `config.yaml` file. Changes in one are reflected in the other. History is separate for each interface.

**Q: What LLM models work best?**

A: Code-focused models work best:
- **CodeLlama 13B**: Good balance of quality and speed
- **CodeLlama 34B**: Higher quality, needs more resources
- **DeepSeek Coder 33B**: Excellent for code, requires GPU
- **Mistral 7B**: Faster, good for simpler tasks

**Q: How much RAM do I need?**

A: Depends on your LLM model:
- 7B model: 8 GB RAM minimum
- 13B model: 16 GB RAM recommended
- 34B+ model: 32 GB RAM recommended
- Plus ~500 MB for the GUI application itself

**Q: Can I use cloud LLMs (OpenAI, Anthropic, etc.)?**

A: The application is designed for local LLMs. However, you can use cloud LLMs if they provide an OpenAI-compatible API endpoint. Configure endpoint and API key in Settings. Note: This sends your code to external servers.

### Configuration Questions

**Q: Where is configuration stored?**

A: Platform-specific locations:
- Windows: `%APPDATA%\local-ai-dev\config.yaml`
- macOS: `~/Library/Application Support/local-ai-dev/config.yaml`
- Linux: `~/.config/local-ai-dev/config.yaml`

**Q: Can I edit config.yaml manually?**

A: Yes. The application detects external changes within 5 seconds and prompts you to reload. Use any text editor. Follow YAML syntax.

**Q: How do I reset to defaults?**

A: Open Settings and click "Reset to Defaults" button. Confirm in dialog. This resets all settings but preserves History.

**Q: What's the difference between temperature settings?**

A: Temperature controls randomness:
- **0.0-0.3**: Deterministic, consistent (best for code)
- **0.4-0.7**: Balanced creativity
- **0.8-2.0**: Creative, varied (good for brainstorming)

For coding tasks, use 0.2 (default).

### Task Execution Questions

**Q: How long do tasks take?**

A: Varies widely based on:
- Task complexity
- Model size and speed
- System resources
- Current project size

Simple tasks: 30 seconds to 2 minutes
Complex tasks: 5 to 20 minutes
Very complex tasks: 30+ minutes

**Q: Can I run multiple tasks simultaneously?**

A: No. The application runs one task at a time. Wait for current task to finish or stop it before starting another.

**Q: What if task is taking too long?**

A: Press `Esc` or click "Stop Task" to cancel. Review the task description - it might be too complex or vague. Break into smaller tasks.

**Q: Can I modify files while task is running?**

A: Not recommended. The task may read or modify the same files, causing conflicts. Wait for task to complete before making manual changes.

**Q: What happens if I close application during task?**

A: The task is interrupted. Partial progress may be saved, but results are unpredictable. Use "Stop Task" for clean cancellation instead.

### History Questions

**Q: Is there a limit to history entries?**

A: By default, no hard limit. However, very large history (1000+ entries) may slow down the interface. Export and clear old entries periodically.

**Q: Can I recover deleted history?**

A: No. Deletion is permanent. Export important entries before deleting.

**Q: Can I share history with team members?**

A: Export history to JSON or CSV, then share the file. Others can review in their preferred tool. History cannot be imported back into the application (yet).

**Q: Why is history separate from CLI?**

A: CLI and GUI use different history storage formats for performance reasons. CLI typically logs to files, GUI uses SQLite database.

### Advanced Questions

**Q: Can I customize the UI?**

A: Theme can be changed (Light/Dark) in Settings. Further customization requires editing CSS files (for developers).

**Q: Can I use different LLMs for different tasks?**

A: Not directly. Change model in Settings before running each task. Consider using separate config files and switching between them.

**Q: How do I enable self-improvement?**

A: ⚠️ **Use with caution.** This allows the system to modify its own code.
1. Open Settings
2. Enable "Self-Improvement Enabled"
3. Save settings
4. Backups are automatic, but ensure you have version control

**Q: Can I run the GUI on a remote server?**

A: The GUI is designed for local use. For remote access, use the CLI instead via SSH, or set up secure remote desktop (VNC, RDP).

**Q: How do I update to a new version?**

A: Download and run the new installer. On Windows and macOS, it upgrades the existing installation. On Linux, rerun the install script. Configuration and History are preserved.

---

**Need more help?** 

- Check [README.md](../README.md) for system overview
- Check [keyboard_shortcuts.md](keyboard_shortcuts.md) for shortcuts reference
- Check [configuration.md](configuration.md) for detailed config options
- Report bugs via Help > Report Bug in the application
- Open an issue on the project repository

**Enjoy using the Local AI Development Environment!** 🚀

