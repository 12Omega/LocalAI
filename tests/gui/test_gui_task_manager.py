"""
Unit tests for GUI Task Manager

Tests cover:
- Task execution in separate thread (Req 13.2)
- Stop signal handling (Req 2.9)
- Progress callback invocation (Req 11.4)
- Concurrent task prevention (Req 2.6)
- Status monitoring
"""

import pytest
import threading
import time
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.gui.gui_task_manager import (
    GUITaskManager,
    TaskAlreadyRunningError,
    TaskCancelledException,
    TaskStatus
)
from src.core.models import TaskResult, ExecutionStep


class TestGUITaskManagerInitialization:
    """Test suite for GUITaskManager initialization."""
    
    def test_initialization_success(self):
        """GUITaskManager should initialize with required components."""
        # Arrange
        mock_llm = Mock()
        mock_code_agent = Mock()
        mock_context_manager = Mock()
        
        # Act
        manager = GUITaskManager(
            llm_interface=mock_llm,
            code_agent=mock_code_agent,
            context_manager=mock_context_manager
        )
        
        # Assert
        assert manager is not None
        assert manager.task_executor is not None
        assert manager.current_thread is None
        assert not manager.stop_flag.is_set()
        assert manager.current_task_id is None
        assert manager.current_description is None
        assert manager.start_time is None
    
    def test_initialization_with_logger(self):
        """GUITaskManager should accept custom logger."""
        # Arrange
        mock_llm = Mock()
        mock_code_agent = Mock()
        mock_context_manager = Mock()
        mock_logger = Mock()
        
        # Act
        manager = GUITaskManager(
            llm_interface=mock_llm,
            code_agent=mock_code_agent,
            context_manager=mock_context_manager,
            logger=mock_logger
        )
        
        # Assert
        assert manager.logger == mock_logger


class TestTaskExecution:
    """Test suite for task execution functionality."""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        mock_llm = Mock()
        mock_code_agent = Mock()
        mock_context_manager = Mock()
        return mock_llm, mock_code_agent, mock_context_manager
    
    @pytest.fixture
    def manager(self, mock_components):
        """Create GUITaskManager with mocked components."""
        return GUITaskManager(*mock_components)
    
    @pytest.fixture
    def successful_result(self):
        """Create a successful TaskResult."""
        return TaskResult(
            success=True,
            actions_taken=[
                ExecutionStep(
                    action="create_file",
                    parameters={"path": "test.py"},
                    rationale="Create test file"
                )
            ],
            files_modified=["test.py"],
            tests_passed=True,
            error_message=None,
            execution_log=["Created test.py"]
        )
    
    def test_run_task_starts_thread(self, manager, successful_result):
        """Running a task should start a background thread (Req 13.2)."""
        # Arrange
        callback_events = []
        
        def callback(event_type, data):
            callback_events.append((event_type, data))
        
        # Mock TaskExecutor to return immediately
        with patch.object(manager.task_executor, 'execute_task', return_value=successful_result):
            # Act
            task_id = manager.run_task("Test task", callback)
            
            # Assert - thread should be created
            assert manager.is_running()
            assert task_id is not None
            assert manager.current_task_id == task_id
            assert manager.current_description == "Test task"
            assert manager.start_time is not None
            
            # Wait for thread to complete
            if manager.current_thread:
                manager.current_thread.join(timeout=2.0)
            
            # Should have received start callback
            assert any(event_type == 'start' for event_type, _ in callback_events)
    
    def test_run_task_invokes_progress_callback(self, manager, successful_result):
        """Task execution should invoke progress callbacks (Req 11.4)."""
        # Arrange
        callback_events = []
        
        def callback(event_type, data):
            callback_events.append((event_type, data))
        
        with patch.object(manager.task_executor, 'execute_task', return_value=successful_result):
            # Act
            manager.run_task("Test task", callback)
            
            # Wait for completion
            time.sleep(0.5)
            if manager.current_thread:
                manager.current_thread.join(timeout=2.0)
            
            # Assert - should have received multiple callback events
            event_types = [event_type for event_type, _ in callback_events]
            
            assert 'start' in event_types
            assert 'progress' in event_types
            assert 'complete' in event_types
            
            # Check start event data
            start_events = [(t, d) for t, d in callback_events if t == 'start']
            assert len(start_events) > 0
            assert 'task_id' in start_events[0][1]
            assert 'description' in start_events[0][1]
            assert start_events[0][1]['description'] == "Test task"
    
    def test_cannot_run_concurrent_tasks(self, manager):
        """Only one task should run at a time (Req 2.6)."""
        # Arrange
        def callback(event_type, data):
            pass
        
        # Mock execute_task to take some time
        def slow_execute(task_desc):
            time.sleep(1.0)
            return TaskResult(
                success=True,
                actions_taken=[],
                files_modified=[],
                tests_passed=True,
                error_message=None,
                execution_log=[]
            )
        
        with patch.object(manager.task_executor, 'execute_task', side_effect=slow_execute):
            # Act - start first task
            task_id_1 = manager.run_task("Task 1", callback)
            
            # Wait a bit to ensure first task is running
            time.sleep(0.1)
            
            # Assert - attempting to start second task should raise error
            with pytest.raises(TaskAlreadyRunningError) as exc_info:
                manager.run_task("Task 2", callback)
            
            assert "already running" in str(exc_info.value).lower()
            
            # Cleanup
            manager.stop_task()
            if manager.current_thread:
                manager.current_thread.join(timeout=2.0)
    
    def test_task_completion_cleans_up_state(self, manager, successful_result):
        """Task completion should clean up thread state."""
        # Arrange
        def callback(event_type, data):
            pass
        
        with patch.object(manager.task_executor, 'execute_task', return_value=successful_result):
            # Act
            task_id = manager.run_task("Test task", callback)
            
            # Wait for completion
            time.sleep(0.5)
            if manager.current_thread:
                manager.current_thread.join(timeout=2.0)
            
            # Assert - state should be cleaned up
            assert not manager.is_running()
            assert manager.current_task_id is None
            assert manager.current_description is None
            assert manager.start_time is None
            assert manager.current_thread is None


class TestTaskCancellation:
    """Test suite for task cancellation functionality."""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        mock_llm = Mock()
        mock_code_agent = Mock()
        mock_context_manager = Mock()
        return mock_llm, mock_code_agent, mock_context_manager
    
    @pytest.fixture
    def manager(self, mock_components):
        """Create GUITaskManager with mocked components."""
        return GUITaskManager(*mock_components)
    
    def test_stop_task_sets_flag(self, manager):
        """Stopping a task should set the stop flag (Req 2.9)."""
        # Arrange
        def callback(event_type, data):
            pass
        
        def slow_execute(task_desc):
            time.sleep(1.0)
            return TaskResult(
                success=True,
                actions_taken=[],
                files_modified=[],
                tests_passed=True,
                error_message=None,
                execution_log=[]
            )
        
        with patch.object(manager.task_executor, 'execute_task', side_effect=slow_execute):
            # Act
            manager.run_task("Test task", callback)
            time.sleep(0.1)  # Let thread start
            
            result = manager.stop_task()
            
            # Assert
            assert result is True
            assert manager.stop_flag.is_set()
            
            # Cleanup
            if manager.current_thread:
                manager.current_thread.join(timeout=2.0)
    
    def test_stop_task_when_not_running(self, manager):
        """Stopping when no task is running should return False."""
        # Act
        result = manager.stop_task()
        
        # Assert
        assert result is False
        assert not manager.stop_flag.is_set()
    
    def test_stop_task_triggers_cancelled_callback(self, manager):
        """Cancelled task should trigger 'cancelled' callback event."""
        # Arrange
        callback_events = []
        
        def callback(event_type, data):
            callback_events.append((event_type, data))
        
        def slow_execute(task_desc):
            time.sleep(1.0)
            return TaskResult(
                success=True,
                actions_taken=[],
                files_modified=[],
                tests_passed=True,
                error_message=None,
                execution_log=[]
            )
        
        with patch.object(manager.task_executor, 'execute_task', side_effect=slow_execute):
            # Act
            manager.run_task("Test task", callback)
            time.sleep(0.1)  # Let thread start
            manager.stop_task()
            
            # Wait for completion
            if manager.current_thread:
                manager.current_thread.join(timeout=2.0)
            
            # Assert
            event_types = [event_type for event_type, _ in callback_events]
            assert 'cancelled' in event_types
            
            # Check cancelled event data
            cancelled_events = [(t, d) for t, d in callback_events if t == 'cancelled']
            assert len(cancelled_events) > 0
            assert 'message' in cancelled_events[0][1]
            assert 'duration' in cancelled_events[0][1]


class TestStatusMonitoring:
    """Test suite for task status monitoring."""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        mock_llm = Mock()
        mock_code_agent = Mock()
        mock_context_manager = Mock()
        return mock_llm, mock_code_agent, mock_context_manager
    
    @pytest.fixture
    def manager(self, mock_components):
        """Create GUITaskManager with mocked components."""
        return GUITaskManager(*mock_components)
    
    def test_is_running_when_no_task(self, manager):
        """is_running should return False when no task is active."""
        # Act
        result = manager.is_running()
        
        # Assert
        assert result is False
    
    def test_is_running_when_task_active(self, manager):
        """is_running should return True when task is executing."""
        # Arrange
        def callback(event_type, data):
            pass
        
        def slow_execute(task_desc):
            time.sleep(1.0)
            return TaskResult(
                success=True,
                actions_taken=[],
                files_modified=[],
                tests_passed=True,
                error_message=None,
                execution_log=[]
            )
        
        with patch.object(manager.task_executor, 'execute_task', side_effect=slow_execute):
            # Act
            manager.run_task("Test task", callback)
            time.sleep(0.1)  # Let thread start
            
            result = manager.is_running()
            
            # Assert
            assert result is True
            
            # Cleanup
            manager.stop_task()
            if manager.current_thread:
                manager.current_thread.join(timeout=2.0)
    
    def test_get_status_when_idle(self, manager):
        """get_status should return idle status when no task is running."""
        # Act
        status = manager.get_status()
        
        # Assert
        assert isinstance(status, TaskStatus)
        assert status.is_running is False
        assert status.task_id is None
        assert status.description is None
        assert status.start_time is None
        assert status.elapsed_seconds is None
    
    def test_get_status_when_running(self, manager):
        """get_status should return active status with task details."""
        # Arrange
        def callback(event_type, data):
            pass
        
        def slow_execute(task_desc):
            time.sleep(1.0)
            return TaskResult(
                success=True,
                actions_taken=[],
                files_modified=[],
                tests_passed=True,
                error_message=None,
                execution_log=[]
            )
        
        with patch.object(manager.task_executor, 'execute_task', side_effect=slow_execute):
            # Act
            task_id = manager.run_task("Test task", callback)
            time.sleep(0.1)  # Let thread start
            
            status = manager.get_status()
            
            # Assert
            assert status.is_running is True
            assert status.task_id == task_id
            assert status.description == "Test task"
            assert status.start_time is not None
            assert status.elapsed_seconds is not None
            assert status.elapsed_seconds > 0
            
            # Cleanup
            manager.stop_task()
            if manager.current_thread:
                manager.current_thread.join(timeout=2.0)
    
    def test_get_status_calculates_elapsed_time(self, manager):
        """get_status should calculate elapsed time accurately."""
        # Arrange
        def callback(event_type, data):
            pass
        
        def slow_execute(task_desc):
            time.sleep(1.0)
            return TaskResult(
                success=True,
                actions_taken=[],
                files_modified=[],
                tests_passed=True,
                error_message=None,
                execution_log=[]
            )
        
        with patch.object(manager.task_executor, 'execute_task', side_effect=slow_execute):
            # Act
            manager.run_task("Test task", callback)
            time.sleep(0.3)  # Let thread run for a bit
            
            status1 = manager.get_status()
            time.sleep(0.2)  # Wait more
            status2 = manager.get_status()
            
            # Assert
            assert status1.elapsed_seconds is not None
            assert status2.elapsed_seconds is not None
            assert status2.elapsed_seconds > status1.elapsed_seconds
            
            # Cleanup
            manager.stop_task()
            if manager.current_thread:
                manager.current_thread.join(timeout=2.0)


class TestErrorHandling:
    """Test suite for error handling."""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        mock_llm = Mock()
        mock_code_agent = Mock()
        mock_context_manager = Mock()
        return mock_llm, mock_code_agent, mock_context_manager
    
    @pytest.fixture
    def manager(self, mock_components):
        """Create GUITaskManager with mocked components."""
        return GUITaskManager(*mock_components)
    
    def test_task_execution_error_triggers_error_callback(self, manager):
        """Task execution errors should trigger 'error' callback."""
        # Arrange
        callback_events = []
        
        def callback(event_type, data):
            callback_events.append((event_type, data))
        
        # Mock TaskExecutor to raise exception
        with patch.object(manager.task_executor, 'execute_task', side_effect=RuntimeError("Test error")):
            # Act
            manager.run_task("Test task", callback)
            
            # Wait for completion
            time.sleep(0.5)
            if manager.current_thread:
                manager.current_thread.join(timeout=2.0)
            
            # Assert
            event_types = [event_type for event_type, _ in callback_events]
            assert 'error' in event_types
            
            # Check error event data
            error_events = [(t, d) for t, d in callback_events if t == 'error']
            assert len(error_events) > 0
            assert 'error' in error_events[0][1]
            assert 'traceback' in error_events[0][1]
            assert "Test error" in error_events[0][1]['error']
    
    def test_task_failure_result_triggers_error_callback(self, manager):
        """Failed TaskResult should trigger 'error' callback."""
        # Arrange
        callback_events = []
        
        def callback(event_type, data):
            callback_events.append((event_type, data))
        
        failed_result = TaskResult(
            success=False,
            actions_taken=[],
            files_modified=[],
            tests_passed=False,
            error_message="Task failed due to syntax error",
            execution_log=["Attempted to create file", "Syntax error detected"]
        )
        
        with patch.object(manager.task_executor, 'execute_task', return_value=failed_result):
            # Act
            manager.run_task("Test task", callback)
            
            # Wait for completion
            time.sleep(0.5)
            if manager.current_thread:
                manager.current_thread.join(timeout=2.0)
            
            # Assert
            event_types = [event_type for event_type, _ in callback_events]
            assert 'error' in event_types
            
            # Check error event data
            error_events = [(t, d) for t, d in callback_events if t == 'error']
            assert len(error_events) > 0
            assert error_events[0][1]['error'] == "Task failed due to syntax error"


class TestThreadSafety:
    """Test suite for thread safety."""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        mock_llm = Mock()
        mock_code_agent = Mock()
        mock_context_manager = Mock()
        return mock_llm, mock_code_agent, mock_context_manager
    
    @pytest.fixture
    def manager(self, mock_components):
        """Create GUITaskManager with mocked components."""
        return GUITaskManager(*mock_components)
    
    def test_daemon_thread_creation(self, manager):
        """Worker threads should be created as daemon threads (Req 13.2)."""
        # Arrange
        def callback(event_type, data):
            pass
        
        def slow_execute(task_desc):
            time.sleep(0.5)
            return TaskResult(
                success=True,
                actions_taken=[],
                files_modified=[],
                tests_passed=True,
                error_message=None,
                execution_log=[]
            )
        
        with patch.object(manager.task_executor, 'execute_task', side_effect=slow_execute):
            # Act
            manager.run_task("Test task", callback)
            time.sleep(0.1)  # Let thread start
            
            # Assert
            assert manager.current_thread is not None
            assert manager.current_thread.daemon is True
            assert manager.current_thread.is_alive()
            
            # Cleanup
            manager.stop_task()
            if manager.current_thread:
                manager.current_thread.join(timeout=2.0)
