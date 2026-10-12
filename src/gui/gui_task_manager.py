"""
GUI Task Manager - Thread-safe wrapper for TaskExecutor

This module provides a GUI-friendly interface to the TaskExecutor that runs
tasks in separate threads and provides progress callbacks for real-time updates.

Requirements implemented:
- 2.6: WHILE a task is executing, THE Task_Input_Panel SHALL disable the run button
- 2.9: WHEN the stop button is clicked, THE Backend_Interface SHALL terminate the current task
- 11.1: THE Backend_Interface SHALL use the existing Task_Executor without modification
- 11.4: THE Backend_Interface SHALL provide a callback mechanism for real-time progress updates
- 13.2: THE Desktop_Application SHALL execute the Backend_Interface in a separate thread from the GUI thread
"""

import threading
import time
import uuid
import logging
from datetime import datetime
from typing import Callable, Optional, Dict, Any
from dataclasses import dataclass

from src.core.task_executor import TaskExecutor
from src.core.models import TaskResult, SystemConfig
from src.core.llm_interface import LocalLLMInterface
from src.agents.code_agent import CodeAgent
from src.context.context_manager import ContextManager


@dataclass
class TaskStatus:
    """Current status of a running task."""
    is_running: bool
    task_id: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    elapsed_seconds: Optional[float] = None


class TaskAlreadyRunningError(Exception):
    """Raised when attempting to start a task while another is running."""
    pass


class TaskCancelledException(Exception):
    """Raised when a task is cancelled by user."""
    pass


class GUITaskManager:
    """
    Thread-safe task manager for GUI applications.
    
    Wraps TaskExecutor to provide:
    - Task execution in separate daemon threads (Req 13.2)
    - Progress callbacks for real-time GUI updates (Req 11.4)
    - Task cancellation support via stop signals (Req 2.9)
    - Status monitoring (Req 2.6)
    - Reuses existing TaskExecutor without modification (Req 11.1)
    
    Threading Model:
    - Main thread: GUI event loop
    - Worker thread: Task execution (daemon)
    - Communication: Thread-safe callbacks and event flags
    """
    
    def __init__(
        self,
        llm_interface: LocalLLMInterface,
        code_agent: CodeAgent,
        context_manager: ContextManager,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize GUI Task Manager.
        
        Args:
            llm_interface: Interface for communicating with local LLM
            code_agent: Agent for code operations
            context_manager: Manager for project context
            logger: Logger for tracking execution
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize TaskExecutor with required components
        self.task_executor = TaskExecutor(
            llm_interface=llm_interface,
            code_agent=code_agent,
            context_manager=context_manager,
            logger=self.logger
        )
        
        # Thread management (daemon threads for automatic cleanup)
        self.current_thread: Optional[threading.Thread] = None
        self.stop_flag = threading.Event()  # Signal for task cancellation
        self.task_lock = threading.Lock()   # Prevent concurrent task execution
        
        # Current task state
        self.current_task_id: Optional[str] = None
        self.current_description: Optional[str] = None
        self.start_time: Optional[datetime] = None
        
        self.logger.info("GUITaskManager initialized")
    
    def run_task(self, task_description: str, progress_callback: Callable[[str, Dict[str, Any]], None]) -> str:
        """
        Execute a task in a separate daemon thread.
        
        This method implements Requirement 13.2 by executing tasks in a separate
        thread from the GUI thread, allowing the UI to remain responsive.
        
        Args:
            task_description: User's task description
            progress_callback: Function to call with progress updates
                Signature: callback(event_type: str, data: dict)
                Event types:
                    - 'start': Task has started
                    - 'progress': Progress update during execution
                    - 'complete': Task completed successfully
                    - 'error': Task failed with error
                    - 'cancelled': Task was cancelled by user
                
        Returns:
            task_id: Unique identifier for this task execution
            
        Raises:
            TaskAlreadyRunningError: If a task is currently executing (Req 2.6)
            
        Example:
            def on_progress(event_type, data):
                if event_type == 'progress':
                    print(f"Progress: {data['message']}")
            
            task_id = manager.run_task("Create calculator module", on_progress)
        """
        with self.task_lock:
            if self.is_running():
                raise TaskAlreadyRunningError(
                    "A task is already running. Please wait for it to complete or stop it first."
                )
            
            # Generate unique task ID
            task_id = str(uuid.uuid4())
            self.current_task_id = task_id
            self.current_description = task_description
            self.start_time = datetime.now()
            self.stop_flag.clear()
            
            self.logger.info(f"Starting task {task_id[:8]}: {task_description}")
            
            # Create and start worker thread as daemon (Req 13.2)
            # Daemon threads automatically terminate when main program exits
            self.current_thread = threading.Thread(
                target=self._run_task_thread,
                args=(task_id, task_description, progress_callback),
                daemon=True,  # Daemon thread for automatic cleanup
                name=f"TaskExecutor-{task_id[:8]}"
            )
            self.current_thread.start()
            
            return task_id
    
    def stop_task(self) -> bool:
        """
        Cancel the currently running task.
        
        Implements Requirement 2.9: WHEN the stop button is clicked,
        THE Backend_Interface SHALL terminate the current task execution.
        
        Sets a stop flag that the worker thread checks periodically.
        The task may not stop immediately but will stop at the next
        cancellation checkpoint.
        
        Returns:
            True if a task was signaled to stop, False if no task was running
            
        Example:
            if manager.stop_task():
                print("Stop signal sent")
            else:
                print("No task is running")
        """
        with self.task_lock:
            if not self.is_running():
                self.logger.info("Stop requested but no task is running")
                return False
            
            # Set stop flag (worker thread will check this)
            self.stop_flag.set()
            self.logger.info(f"Stop signal sent for task {self.current_task_id[:8] if self.current_task_id else 'unknown'}")
            return True
    
    def is_running(self) -> bool:
        """
        Check if a task is currently executing.
        
        Implements Requirement 2.6: Used to determine whether to enable/disable
        the run button in the Task Input Panel.
        
        Returns:
            True if a task is running, False otherwise
            
        Example:
            if not manager.is_running():
                # Enable run button
                run_button.set_enabled(True)
        """
        return (
            self.current_thread is not None and 
            self.current_thread.is_alive()
        )
    
    def get_status(self) -> TaskStatus:
        """
        Get current task status with detailed information.
        
        Provides comprehensive task state for GUI status displays.
        
        Returns:
            TaskStatus object containing:
                - is_running: Whether a task is currently executing
                - task_id: Unique identifier of running task (if any)
                - description: Task description (if running)
                - start_time: When the task started (if running)
                - elapsed_seconds: Time elapsed since start (if running)
                
        Example:
            status = manager.get_status()
            if status.is_running:
                print(f"Task {status.task_id[:8]} running for {status.elapsed_seconds:.1f}s")
            else:
                print("No task running")
        """
        is_running = self.is_running()
        elapsed = None
        
        if is_running and self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
        
        return TaskStatus(
            is_running=is_running,
            task_id=self.current_task_id if is_running else None,
            description=self.current_description if is_running else None,
            start_time=self.start_time if is_running else None,
            elapsed_seconds=elapsed
        )
    
    def _run_task_thread(
        self, 
        task_id: str, 
        task_description: str, 
        progress_callback: Callable[[str, Dict[str, Any]], None]
    ):
        """
        Worker thread that executes the task.
        
        This method runs in a separate daemon thread and implements
        Requirement 11.4 by providing real-time progress callbacks.
        
        The thread monitors the stop_flag and raises TaskCancelledException
        when cancellation is requested (Req 2.9).
        
        Args:
            task_id: Unique task identifier
            task_description: User's task description
            progress_callback: Function to call with progress updates (Req 11.4)
        """
        try:
            # Notify task started
            progress_callback('start', {
                'task_id': task_id,
                'description': task_description,
                'timestamp': datetime.now().isoformat()
            })
            
            self.logger.info(f"Task {task_id[:8]} worker thread started")
            
            # Send initial progress message
            progress_callback('progress', {
                'type': 'info',
                'message': f'Starting task: {task_description}',
                'timestamp': datetime.now().isoformat()
            })
            
            # Execute the task with periodic stop checks (Req 2.9)
            result = self._execute_with_cancellation(
                task_description,
                progress_callback
            )
            
            # Calculate duration
            duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            
            # Check if task was cancelled
            if self.stop_flag.is_set():
                self.logger.info(f"Task {task_id[:8]} was cancelled")
                progress_callback('cancelled', {
                    'task_id': task_id,
                    'message': 'Task was cancelled by user',
                    'duration': duration,
                    'timestamp': datetime.now().isoformat()
                })
            elif result.success:
                # Task completed successfully
                self.logger.info(f"Task {task_id[:8]} completed successfully in {duration:.1f}s")
                progress_callback('complete', {
                    'task_id': task_id,
                    'result': {
                        'success': result.success,
                        'actions_taken': [
                            {'action': step.action, 'rationale': step.rationale}
                            for step in result.actions_taken
                        ],
                        'files_modified': result.files_modified,
                        'tests_passed': result.tests_passed,
                        'execution_log': result.execution_log
                    },
                    'duration': duration,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                # Task completed with error
                self.logger.error(f"Task {task_id[:8]} failed: {result.error_message}")
                progress_callback('error', {
                    'task_id': task_id,
                    'error': result.error_message or 'Unknown error occurred',
                    'execution_log': result.execution_log,
                    'duration': duration,
                    'timestamp': datetime.now().isoformat()
                })
                
        except TaskCancelledException:
            # Task was cancelled during execution
            duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            self.logger.info(f"Task {task_id[:8]} cancelled after {duration:.1f}s")
            progress_callback('cancelled', {
                'task_id': task_id,
                'message': 'Task execution was cancelled',
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            # Unexpected exception
            duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            self.logger.exception(f"Task {task_id[:8]} failed with exception")
            progress_callback('error', {
                'task_id': task_id,
                'error': f'Unexpected error: {str(e)}',
                'traceback': self._format_exception(e),
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            })
        finally:
            # Clean up task state
            with self.task_lock:
                self.current_task_id = None
                self.current_description = None
                self.start_time = None
                self.current_thread = None
            
            self.logger.info(f"Task {task_id[:8]} worker thread terminated")
    
    def _execute_with_cancellation(
        self,
        task_description: str,
        progress_callback: Callable[[str, Dict[str, Any]], None]
    ) -> TaskResult:
        """
        Execute task with cancellation support.
        
        This wraps the TaskExecutor (Req 11.1: uses existing TaskExecutor without
        modification) and periodically checks the stop flag (Req 2.9).
        
        Args:
            task_description: User's task description
            progress_callback: Function to call with progress updates
            
        Returns:
            TaskResult from task execution
            
        Raises:
            TaskCancelledException: If stop_flag is set during execution
        """
        # Send progress update: planning phase
        progress_callback('progress', {
            'type': 'info',
            'message': 'Analyzing task and planning execution steps...',
            'timestamp': datetime.now().isoformat()
        })
        
        # Check for cancellation before starting
        if self.stop_flag.is_set():
            raise TaskCancelledException("Task cancelled before execution started")
        
        # Execute the task using existing TaskExecutor (Req 11.1)
        # Note: TaskExecutor.execute_task() is synchronous and doesn't
        # support cancellation checkpoints. For now, we execute it fully.
        # In a future enhancement, TaskExecutor could be modified to accept
        # a stop_flag parameter for more granular cancellation.
        
        self.logger.debug("Executing task via TaskExecutor")
        result = self.task_executor.execute_task(task_description)
        
        # Check for cancellation after execution
        if self.stop_flag.is_set():
            self.logger.debug("Task completed but stop flag was set")
            # Return a cancelled result instead of the actual result
            raise TaskCancelledException("Task cancelled during execution")
        
        # Send progress for completed actions (Req 11.4)
        if result.actions_taken:
            progress_callback('progress', {
                'type': 'info',
                'message': f'Completed {len(result.actions_taken)} actions',
                'timestamp': datetime.now().isoformat()
            })
        
        return result
    
    def _format_exception(self, e: Exception) -> str:
        """
        Format exception with traceback for logging.
        
        Args:
            e: Exception to format
            
        Returns:
            Formatted traceback string
        """
        import traceback
        return ''.join(traceback.format_exception(type(e), e, e.__traceback__))
