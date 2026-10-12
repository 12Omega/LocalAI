"""
Main GUI Application Entry Point for Desktop GUI Application

This module initializes the Eel framework and exposes Python functions to JavaScript,
creating the bridge between the GUI frontend and the Python backend.

Requirements implemented:
- 1.1: Launch application by double-clicking executable
- 1.2: Load Configuration_Store and initialize Backend_Interface
- 11.1: Use existing Task_Executor without modification
- 11.4: Provide callback mechanism for real-time progress updates
- 11.7: Handle exceptions from backend modules and convert to user-friendly messages
- 12.3: Detect external configuration changes within 5 seconds
- 12.4: Prompt user to reload or keep current settings when external change detected
"""

import eel
import os
import sys
import time
import logging
import threading
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from tkinter import Tk, filedialog

# Import backend components
from src.core.config import ConfigManager, ConfigurationError
from src.core.llm_interface import LocalLLMInterface
from src.agents.code_agent import CodeAgent
from src.context.context_manager import ContextManager

# Import GUI-specific managers
from src.gui.gui_task_manager import GUITaskManager, TaskAlreadyRunningError
from src.gui.gui_config_manager import GUIConfigManager
from src.gui.gui_history_manager import GUIHistoryManager, HistoryEntry
from src.gui.crash_logger import install_crash_logger, get_crash_logger


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Global instances (initialized in start_gui())
task_manager: Optional[GUITaskManager] = None
config_manager_gui: Optional[GUIConfigManager] = None
history_manager: Optional[GUIHistoryManager] = None
config_watcher_thread: Optional[threading.Thread] = None
config_watcher_running = threading.Event()


# ============================================================================
# Eel Exposed Functions - Task Execution
# ============================================================================

@eel.expose
def run_task(task_description: str) -> Dict[str, Any]:
    """
    Start executing a task in a background thread.
    
    Implements Requirement 11.4: Provides callback mechanism for real-time
    progress updates to the GUI via eel.update_progress().
    
    Args:
        task_description: User's task description from Task Input Panel
        
    Returns:
        Dictionary with:
            - success: True if task started, False if error
            - task_id: Unique identifier for the task (if success)
            - error: Error message (if not success)
            
    Requirements: 1.2, 11.1, 11.4, 11.7
    """
    global task_manager
    
    try:
        if not task_manager:
            return {
                'success': False,
                'error': 'Application not properly initialized'
            }
        
        # Validate input
        if not task_description or not task_description.strip():
            return {
                'success': False,
                'error': 'Task description cannot be empty'
            }
        
        # Progress callback that sends updates to frontend (Req 11.4)
        def progress_callback(event_type: str, data: Dict[str, Any]) -> None:
            """Send progress updates to JavaScript frontend."""
            try:
                if event_type == 'start':
                    eel.update_progress({
                        'type': 'info',
                        'message': f'Starting task: {data["description"][:100]}...',
                        'timestamp': data['timestamp']
                    })
                    
                elif event_type == 'progress':
                    eel.update_progress({
                        'type': data.get('type', 'info'),
                        'message': data['message'],
                        'timestamp': data['timestamp']
                    })
                    
                elif event_type == 'complete':
                    # Notify completion
                    eel.task_completed({
                        'task_id': data['task_id'],
                        'status': 'success',
                        'duration': data['duration'],
                        'summary': _create_task_summary(data['result']),
                        'timestamp': data['timestamp']
                    })
                    
                    # Save to history
                    _save_task_to_history(
                        task_id=data['task_id'],
                        task_description=task_description,
                        duration=data['duration'],
                        status='success',
                        result=data['result']
                    )
                    
                elif event_type == 'error':
                    # Notify error
                    eel.task_error({
                        'task_id': data['task_id'],
                        'error_type': 'TaskExecutionError',
                        'error_message': data['error'],
                        'suggestion': _get_error_suggestion(data['error']),
                        'timestamp': data.get('timestamp', datetime.now().isoformat())
                    })
                    
                    # Save to history
                    _save_task_to_history(
                        task_id=data['task_id'],
                        task_description=task_description,
                        duration=data.get('duration', 0),
                        status='failed',
                        error_message=data['error'],
                        execution_log=data.get('execution_log', '')
                    )
                    
                elif event_type == 'cancelled':
                    # Notify cancellation
                    eel.task_completed({
                        'task_id': data['task_id'],
                        'status': 'cancelled',
                        'duration': data['duration'],
                        'summary': 'Task was cancelled by user',
                        'timestamp': data['timestamp']
                    })
                    
                    # Save to history
                    _save_task_to_history(
                        task_id=data['task_id'],
                        task_description=task_description,
                        duration=data['duration'],
                        status='cancelled',
                        output='Task cancelled by user'
                    )
                    
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
        
        # Start task execution
        task_id = task_manager.run_task(task_description, progress_callback)
        
        logger.info(f"Task started: {task_id[:8]}")
        
        return {
            'success': True,
            'task_id': task_id
        }
        
    except TaskAlreadyRunningError as e:
        # User-friendly error message (Req 11.7)
        return {
            'success': False,
            'error': 'A task is already running. Please wait for it to complete or stop it first.'
        }
        
    except Exception as e:
        # Unexpected error - log and return user-friendly message (Req 11.7)
        logger.exception("Error starting task")
        return {
            'success': False,
            'error': f'Failed to start task: {str(e)}'
        }


@eel.expose
def stop_task() -> Dict[str, Any]:
    """
    Cancel the currently running task.
    
    Returns:
        Dictionary with:
            - success: True if stop signal sent, False if no task running
            - message: Status message
            
    Requirements: 2.9
    """
    global task_manager
    
    try:
        if not task_manager:
            return {
                'success': False,
                'message': 'Application not properly initialized'
            }
        
        if task_manager.stop_task():
            logger.info("Stop signal sent to running task")
            return {
                'success': True,
                'message': 'Stop signal sent. Task will stop at the next checkpoint.'
            }
        else:
            return {
                'success': False,
                'message': 'No task is currently running'
            }
            
    except Exception as e:
        logger.exception("Error stopping task")
        return {
            'success': False,
            'message': f'Error stopping task: {str(e)}'
        }


# ============================================================================
# Eel Exposed Functions - Configuration Management
# ============================================================================

@eel.expose
def get_config() -> Dict[str, Any]:
    """
    Get current configuration for display in Settings Manager.
    
    Returns configuration with sensitive values masked.
    
    Returns:
        Configuration dictionary or error dictionary
        
    Requirements: 4.2, 4.11, 12.1
    """
    global config_manager_gui
    
    try:
        if not config_manager_gui:
            return {'error': 'Configuration manager not initialized'}
        
        config_dict = config_manager_gui.get_config_for_gui()
        return config_dict
        
    except Exception as e:
        logger.exception("Error getting configuration")
        return {'error': f'Failed to load configuration: {str(e)}'}


@eel.expose
def save_config(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save configuration changes to file.
    
    Args:
        config_data: Complete configuration dictionary from Settings Manager
        
    Returns:
        Dictionary with:
            - success: True if saved successfully
            - message: Success or error message
            
    Requirements: 4.5, 4.6, 12.5, 12.6, 12.7, 12.8
    """
    global config_manager_gui
    
    try:
        if not config_manager_gui:
            return {
                'success': False,
                'error': 'Configuration manager not initialized'
            }
        
        # Save configuration (includes validation, backup, atomic write)
        success, message = config_manager_gui.save_config(config_data)
        
        if success:
            logger.info("Configuration saved successfully")
            return {
                'success': True,
                'message': message
            }
        else:
            logger.warning(f"Configuration save failed: {message}")
            return {
                'success': False,
                'error': message
            }
            
    except Exception as e:
        logger.exception("Error saving configuration")
        return {
            'success': False,
            'error': f'Unexpected error saving configuration: {str(e)}'
        }


@eel.expose
def validate_config_field(field_name: str, value: Any) -> Dict[str, Any]:
    """
    Validate a single configuration field before saving.
    
    Args:
        field_name: Dot-notation field name (e.g., 'llm.endpoint')
        value: Value to validate
        
    Returns:
        Dictionary with:
            - valid: True if valid, False otherwise
            - error: Error message if not valid
            
    Requirements: 4.3, 4.4, 12.8
    """
    global config_manager_gui
    
    try:
        if not config_manager_gui:
            return {
                'valid': False,
                'error': 'Configuration manager not initialized'
            }
        
        is_valid, error_message = config_manager_gui.validate_field(field_name, value)
        
        if is_valid:
            return {'valid': True}
        else:
            return {'valid': False, 'error': error_message}
            
    except Exception as e:
        logger.exception(f"Error validating field {field_name}")
        return {
            'valid': False,
            'error': f'Validation error: {str(e)}'
        }


# ============================================================================
# Eel Exposed Functions - Task History
# ============================================================================

@eel.expose
def get_history(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get task execution history with optional filtering and pagination.
    
    Args:
        limit: Maximum number of entries to return (default: 100)
        offset: Number of entries to skip for pagination (default: 0)
        
    Returns:
        List of history entry dictionaries, or empty list on error
        
    Requirements: 5.1, 5.2, 5.3, 5.8, 5.10, 18.1
    """
    global history_manager
    
    try:
        if not history_manager:
            logger.error("History manager not initialized")
            return []
        
        # Get entries from database with limit and offset (Req 18.1)
        entries = history_manager.get_entries(
            limit=limit,
            offset=offset
        )
        
        # Convert to dictionaries for JSON serialization
        return [
            {
                'entry_id': entry.entry_id,
                'task_description': entry.task_description,
                'timestamp': entry.timestamp.isoformat() if entry.timestamp else None,
                'duration_seconds': entry.duration_seconds,
                'status': entry.status,
                'output': entry.output[:500] if entry.output else '',  # Truncate for list view
                'error_message': entry.error_message
            }
            for entry in entries
        ]
        
    except Exception as e:
        logger.exception("Error retrieving history")
        return []


@eel.expose
def get_history_entry(entry_id: str) -> Optional[Dict[str, Any]]:
    """
    Get full details of a specific history entry.
    
    Args:
        entry_id: UUID of the history entry
        
    Returns:
        Full history entry dictionary or None if not found
        
    Requirements: 5.4
    """
    global history_manager
    
    try:
        if not history_manager:
            return None
        
        entry = history_manager.get_entry_by_id(entry_id)
        
        if entry:
            return {
                'entry_id': entry.entry_id,
                'task_description': entry.task_description,
                'timestamp': entry.timestamp.isoformat() if entry.timestamp else None,
                'duration_seconds': entry.duration_seconds,
                'status': entry.status,
                'output': entry.output,  # Full output
                'error_message': entry.error_message,
                'config_snapshot': entry.config_snapshot
            }
        
        return None
        
    except Exception as e:
        logger.exception(f"Error retrieving history entry {entry_id}")
        return None


@eel.expose
def delete_history_entry(entry_id: str) -> Dict[str, Any]:
    """
    Delete a specific history entry.
    
    Args:
        entry_id: UUID of the entry to delete
        
    Returns:
        Dictionary with:
            - success: True if deleted
            - message: Status message
            
    Requirements: 5.6
    """
    global history_manager
    
    try:
        if not history_manager:
            return {
                'success': False,
                'message': 'History manager not initialized'
            }
        
        if history_manager.delete_entry(entry_id):
            logger.info(f"Deleted history entry {entry_id[:8]}")
            return {
                'success': True,
                'message': 'Entry deleted successfully'
            }
        else:
            return {
                'success': False,
                'message': 'Entry not found'
            }
            
    except Exception as e:
        logger.exception(f"Error deleting history entry {entry_id}")
        return {
            'success': False,
            'message': f'Error deleting entry: {str(e)}'
        }


@eel.expose
def clear_all_history() -> Dict[str, Any]:
    """
    Delete all history entries.
    
    Returns:
        Dictionary with:
            - success: True if successful
            - count: Number of entries deleted
            - message: Status message
            
    Requirements: 5.7
    """
    global history_manager
    
    try:
        if not history_manager:
            return {
                'success': False,
                'message': 'History manager not initialized'
            }
        
        count = history_manager.clear_all()
        logger.info(f"Cleared {count} history entries")
        
        return {
            'success': True,
            'count': count,
            'message': f'Deleted {count} entries'
        }
        
    except Exception as e:
        logger.exception("Error clearing history")
        return {
            'success': False,
            'message': f'Error clearing history: {str(e)}'
        }


@eel.expose
def export_history(format_type: str, filepath: str) -> Dict[str, Any]:
    """
    Export history to JSON or CSV file.
    
    Args:
        format_type: 'json' or 'csv'
        filepath: Output file path
        
    Returns:
        Dictionary with:
            - success: True if exported successfully
            - message: Status message
            
    Requirements: 5.9
    """
    global history_manager
    
    try:
        if not history_manager:
            return {
                'success': False,
                'message': 'History manager not initialized'
            }
        
        if format_type == 'json':
            success = history_manager.export_to_json(filepath)
        elif format_type == 'csv':
            success = history_manager.export_to_csv(filepath)
        else:
            return {
                'success': False,
                'message': f'Invalid format type: {format_type}'
            }
        
        if success:
            logger.info(f"Exported history to {filepath}")
            return {
                'success': True,
                'message': f'History exported to {filepath}'
            }
        else:
            return {
                'success': False,
                'message': 'Export failed'
            }
            
    except Exception as e:
        logger.exception(f"Error exporting history to {filepath}")
        return {
            'success': False,
            'message': f'Error exporting history: {str(e)}'
        }


# ============================================================================
# Eel Exposed Functions - Utility
# ============================================================================

@eel.expose
def browse_directory(initial_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Open native directory browser dialog.
    
    Args:
        initial_path: Optional initial directory to show
        
    Returns:
        Dictionary with:
            - success: True if directory selected
            - path: Selected directory path (if success)
            - cancelled: True if user cancelled (if not success)
            
    Requirements: 4.8
    """
    try:
        # Create Tk root window (hidden)
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)  # Bring dialog to front
        
        # Open directory browser
        selected_path = filedialog.askdirectory(
            initialdir=initial_path,
            title='Select Directory'
        )
        
        # Destroy Tk root
        root.destroy()
        
        if selected_path:
            return {
                'success': True,
                'path': selected_path
            }
        else:
            return {
                'success': False,
                'cancelled': True
            }
            
    except Exception as e:
        logger.exception("Error opening directory browser")
        return {
            'success': False,
            'error': str(e)
        }


@eel.expose
def get_app_status() -> Dict[str, Any]:
    """
    Get current application status.
    
    Returns:
        Dictionary with application status information
    """
    global task_manager
    
    try:
        status = {
            'initialized': task_manager is not None,
            'version': '1.0.0'  # TODO: Get from package metadata
        }
        
        if task_manager:
            task_status = task_manager.get_status()
            status['task_running'] = task_status.is_running
            if task_status.is_running:
                status['current_task_id'] = task_status.task_id
                status['elapsed_seconds'] = task_status.elapsed_seconds
        
        return status
        
    except Exception as e:
        logger.exception("Error getting app status")
        return {'error': str(e)}


@eel.expose
def get_platform() -> str:
    """
    Get the current platform identifier.
    
    Returns platform string for use in JavaScript to determine platform-specific
    UI conventions (keyboard shortcuts, menu placement, etc.)
    
    Returns:
        Platform string: 'win32', 'darwin', or 'linux'
        
    Requirements: 15.5, 17.2
    """
    return sys.platform


@eel.expose
def is_first_run() -> bool:
    """
    Check if this is the first run of the application.
    
    First run is detected by checking for a sentinel file in the
    platform-specific config directory.
    
    Returns:
        True if first run (no sentinel file), False otherwise
        
    Requirements: 19.2
    """
    from src.gui.platform_paths import PlatformPaths
    
    try:
        sentinel_path = PlatformPaths.get_config_dir() / '.local-ai-dev-configured'
        return not sentinel_path.exists()
    except Exception as e:
        logger.exception("Error checking first run status")
        return False


@eel.expose
def complete_first_run_setup(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Complete first-run setup by saving initial configuration.
    
    Args:
        config: Initial configuration dictionary from setup wizard
        
    Returns:
        Dictionary with:
            - success: True if setup completed successfully
            - error: Error message if failed
            
    Requirements: 19.2
    """
    from src.gui.platform_paths import PlatformPaths
    global config_manager_gui
    
    try:
        if not config_manager_gui:
            return {
                'success': False,
                'error': 'Configuration manager not initialized'
            }
        
        # Save the configuration
        success, message = config_manager_gui.save_config(config)
        
        if not success:
            return {
                'success': False,
                'error': message
            }
        
        # Create sentinel file to mark setup as complete
        sentinel_path = PlatformPaths.get_config_dir() / '.local-ai-dev-configured'
        try:
            sentinel_path.touch()
            logger.info("First-run setup completed successfully")
        except Exception as e:
            logger.warning(f"Could not create sentinel file: {e}")
            # Not critical - config is saved
        
        return {
            'success': True
        }
        
    except Exception as e:
        logger.exception("Error completing first-run setup")
        return {
            'success': False,
            'error': f'Failed to save configuration: {str(e)}'
        }


@eel.expose
def validate_llm_endpoint(url: str) -> Dict[str, Any]:
    """
    Validate that an LLM endpoint URL is reachable.
    
    Makes a lightweight HEAD or GET request to check connectivity.
    
    Args:
        url: LLM endpoint URL to validate
        
    Returns:
        Dictionary with:
            - reachable: True if endpoint is reachable, False otherwise
            - error: Error message if not reachable
            
    Requirements: 19.2
    """
    import urllib.request
    import urllib.error
    
    try:
        # Validate URL format first
        if not url or not url.strip():
            return {
                'reachable': False,
                'error': 'URL cannot be empty'
            }
        
        # Ensure URL has a scheme
        if not url.startswith(('http://', 'https://')):
            return {
                'reachable': False,
                'error': 'URL must start with http:// or https://'
            }
        
        # Try to make a HEAD request with timeout
        try:
            request = urllib.request.Request(url, method='HEAD')
            request.add_header('User-Agent', 'LocalAIDev/1.0')
            
            with urllib.request.urlopen(request, timeout=5) as response:
                # Check if we got a valid response (any 2xx or 3xx status is OK)
                if 200 <= response.status < 400:
                    logger.info(f"LLM endpoint validated: {url}")
                    return {
                        'reachable': True
                    }
                else:
                    return {
                        'reachable': False,
                        'error': f'Server returned status {response.status}'
                    }
        except urllib.error.HTTPError as e:
            # Some servers don't support HEAD, try GET with small range
            if e.code == 405 or e.code == 501:
                logger.info(f"HEAD not supported, trying GET for {url}")
                request = urllib.request.Request(url)
                request.add_header('User-Agent', 'LocalAIDev/1.0')
                
                with urllib.request.urlopen(request, timeout=5) as response:
                    if 200 <= response.status < 400:
                        return {
                            'reachable': True
                        }
            
            # HTTP error that's not about method
            return {
                'reachable': False,
                'error': f'HTTP Error {e.code}: {e.reason}'
            }
        
    except urllib.error.URLError as e:
        # Network error or timeout
        error_msg = str(e.reason) if hasattr(e, 'reason') else str(e)
        return {
            'reachable': False,
            'error': f'Cannot reach server: {error_msg}'
        }
    except Exception as e:
        logger.exception(f"Error validating endpoint {url}")
        return {
            'reachable': False,
            'error': f'Validation error: {str(e)}'
        }


@eel.expose
def open_external(url: str) -> Dict[str, Any]:
    """
    Open an external URL or file in the system's default application.
    
    Args:
        url: URL or file path to open
        
    Returns:
        Dictionary with:
            - success: True if opened successfully
            - message: Status message
            
    Requirements: 10.5
    """
    import webbrowser
    import subprocess
    import platform
    
    try:
        logger.info(f"Opening external URL/file: {url}")
        
        # Check if it's a local file path
        if not url.startswith(('http://', 'https://', 'file://')):
            file_path = Path(url)
            
            # Make path absolute if relative
            if not file_path.is_absolute():
                # Try relative to project root or docs
                docs_path = Path(__file__).parent.parent.parent / 'docs' / url
                if docs_path.exists():
                    file_path = docs_path
                else:
                    file_path = Path(__file__).parent.parent.parent / url
            
            if file_path.exists():
                # Open local file with system default application
                if platform.system() == 'Windows':
                    os.startfile(str(file_path))
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', str(file_path)])
                else:  # Linux
                    subprocess.run(['xdg-open', str(file_path)])
                
                return {
                    'success': True,
                    'message': f'Opened {file_path.name}'
                }
            else:
                return {
                    'success': False,
                    'message': f'File not found: {file_path}'
                }
        else:
            # Open URL in browser
            webbrowser.open(url)
            return {
                'success': True,
                'message': f'Opened {url} in browser'
            }
            
    except Exception as e:
        logger.exception(f"Error opening external URL/file: {url}")
        return {
            'success': False,
            'message': f'Failed to open: {str(e)}'
        }

# ============================================================================
# Helper Functions
# ============================================================================

def _create_task_summary(result: Dict[str, Any]) -> str:
    """Create a human-readable summary of task results."""
    try:
        if not result:
            return 'Task completed'
        
        parts = []
        
        if 'actions_taken' in result:
            action_count = len(result['actions_taken'])
            parts.append(f'{action_count} action{"s" if action_count != 1 else ""}')
        
        if 'files_modified' in result:
            file_count = len(result['files_modified'])
            if file_count > 0:
                parts.append(f'{file_count} file{"s" if file_count != 1 else ""} modified')
        
        if 'tests_passed' in result and result['tests_passed']:
            parts.append('tests passed')
        
        if parts:
            return 'Completed: ' + ', '.join(parts)
        else:
            return 'Task completed successfully'
            
    except Exception:
        return 'Task completed'


def _get_error_suggestion(error_message: str) -> str:
    """Generate helpful suggestion based on error message."""
    error_lower = error_message.lower()
    
    if 'connection' in error_lower or 'connect' in error_lower:
        return 'Check that your LLM server is running and the endpoint URL is correct in Settings.'
    elif 'timeout' in error_lower:
        return 'The LLM server is taking too long to respond. Try increasing the timeout or checking server load.'
    elif 'api key' in error_lower or 'authentication' in error_lower:
        return 'Check that your API key is correct in Settings.'
    elif 'permission' in error_lower or 'access denied' in error_lower:
        return 'Check file permissions and ensure you have write access to the project directory.'
    elif 'syntax error' in error_lower:
        return 'There was a syntax error in the generated code. The AI will attempt to fix this in the next iteration.'
    else:
        return 'Review the error details below for more information.'


def _save_task_to_history(
    task_id: str,
    task_description: str,
    duration: float,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    execution_log: str = ''
) -> None:
    """Save completed task to history database."""
    global history_manager, config_manager_gui
    
    try:
        if not history_manager:
            logger.warning("History manager not initialized, cannot save task")
            return
        
        # Prepare output
        if result:
            output = result.get('execution_log', '') or execution_log
        else:
            output = execution_log
        
        # Get config snapshot
        config_snapshot = None
        if config_manager_gui:
            try:
                config_snapshot = config_manager_gui.get_config_for_gui()
            except Exception:
                pass
        
        # Create history entry
        entry = HistoryEntry(
            entry_id=task_id,
            task_description=task_description,
            timestamp=datetime.now(),
            duration_seconds=duration,
            status=status,
            output=output,
            error_message=error_message,
            config_snapshot=config_snapshot
        )
        
        # Save to database
        history_manager.add_entry(entry)
        logger.info(f"Saved task {task_id[:8]} to history")
        
    except Exception as e:
        logger.exception("Error saving task to history")


def _config_watcher_loop() -> None:
    """
    Background thread that monitors config file for external changes.
    
    Implements Requirements 12.3 and 12.4: Detect external configuration
    changes within 5 seconds and prompt user to reload or keep current settings.
    """
    global config_manager_gui, config_watcher_running
    
    logger.info("Config watcher thread started")
    
    while config_watcher_running.is_set():
        try:
            if config_manager_gui and config_manager_gui.check_external_changes():
                logger.info("External configuration change detected")
                
                # Notify frontend (Req 12.4)
                eel.config_external_change({
                    'message': 'Configuration file was modified externally',
                    'timestamp': datetime.now().isoformat()
                })
                
                # Acknowledge the change to avoid repeated notifications
                config_manager_gui.file_watcher.acknowledge_change()
            
            # Sleep for 5 seconds (Req 12.3: detect within 5 seconds)
            time.sleep(5)
            
        except Exception as e:
            logger.exception("Error in config watcher thread")
            time.sleep(5)
    
    logger.info("Config watcher thread stopped")


# ============================================================================
# Application Initialization and Startup
# ============================================================================

def initialize_backend() -> bool:
    """
    Initialize backend components.
    
    Returns:
        True if initialization successful, False otherwise
        
    Requirements: 1.2, 11.1
    """
    global task_manager, config_manager_gui, history_manager
    
    try:
        logger.info("Initializing backend components...")
        
        # Initialize configuration manager (GUI-specific)
        config_manager_gui = GUIConfigManager("config.yaml")
        logger.info("GUI Config Manager initialized")
        
        # Load system configuration
        config_mgr = ConfigManager("config.yaml")
        try:
            system_config = config_mgr.load_config()
        except ConfigurationError as e:
            logger.warning(f"Config load failed, using defaults: {e}")
            # Create default config
            system_config = config_mgr.load_config()
        
        # Initialize core components (Req 11.1)
        llm_interface = LocalLLMInterface(
            endpoint=system_config.llm.endpoint,
            model_name=system_config.llm.model_name,
            temperature=system_config.llm.temperature,
            max_tokens=system_config.llm.max_tokens
        )
        logger.info("LLM Interface initialized")
        
        code_agent = CodeAgent(
            project_root=system_config.project_root,
            logger=logger
        )
        logger.info("Code Agent initialized")
        
        context_manager = ContextManager(
            project_root=system_config.project_root,
            excluded_dirs=system_config.excluded_directories
        )
        logger.info("Context Manager initialized")
        
        # Initialize GUI Task Manager
        task_manager = GUITaskManager(
            llm_interface=llm_interface,
            code_agent=code_agent,
            context_manager=context_manager,
            logger=logger
        )
        logger.info("GUI Task Manager initialized")
        
        # Initialize history manager
        history_manager = GUIHistoryManager()
        logger.info("GUI History Manager initialized")
        
        logger.info("Backend initialization complete")
        return True
        
    except Exception as e:
        logger.exception("Failed to initialize backend")
        return False


def start_gui(port: int = 8080, debug: bool = False) -> None:
    """
    Start the GUI application.
    
    This is the main entry point that:
    1. Initializes backend components
    2. Starts config file watcher thread
    3. Launches Eel web server
    
    Args:
        port: Port for Eel web server (default: 8080)
        debug: Enable debug mode (default: False)
        
    Requirements: 1.1, 1.2, 12.3, 12.4
    """
    global config_watcher_thread, config_watcher_running
    
    try:
        logger.info("="*60)
        logger.info("Local AI Development Environment - Desktop GUI")
        logger.info("="*60)
        
        # Initialize Eel
        web_dir = Path(__file__).parent.parent / 'web'
        if not web_dir.exists():
            logger.error(f"Web directory not found: {web_dir}")
            sys.exit(1)
        
        logger.info(f"Initializing Eel with web directory: {web_dir}")
        eel.init(str(web_dir))
        
        # Initialize backend components (Req 1.2)
        if not initialize_backend():
            logger.error("Backend initialization failed")
            sys.exit(1)
        
        # Start config watcher thread (Req 12.3, 12.4)
        config_watcher_running.set()
        config_watcher_thread = threading.Thread(
            target=_config_watcher_loop,
            daemon=True,
            name="ConfigWatcher"
        )
        config_watcher_thread.start()
        logger.info("Config watcher thread started")
        
        # Start Eel application
        logger.info(f"Starting Eel on port {port}")
        logger.info("Application ready! Opening GUI window...")
        
        eel.start(
            'index.html',
            size=(1200, 800),
            port=port,
            mode='chrome',  # Use Chrome app mode if available, fallback to default browser
            close_callback=lambda page, sockets: on_close()
        )
        
    except Exception as e:
        logger.exception("Error starting GUI application")
        sys.exit(1)


def on_close() -> None:
    """
    Called when the GUI window is closed.
    
    Cleanup resources and stop background threads.
    """
    global config_watcher_running, task_manager
    
    logger.info("Application closing...")
    
    # Stop config watcher
    if config_watcher_running:
        config_watcher_running.clear()
    
    # Stop any running task
    if task_manager and task_manager.is_running():
        logger.info("Stopping running task...")
        task_manager.stop_task()
        time.sleep(1)  # Give task time to stop
    
    logger.info("Application closed")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description='Local AI Development Environment - Desktop GUI')
    parser.add_argument('--port', type=int, default=8080, help='Port for web server (default: 8080)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Start GUI
    start_gui(port=args.port, debug=args.debug)
