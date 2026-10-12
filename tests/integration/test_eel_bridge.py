"""
Integration tests for Eel Bridge Layer

Tests cover:
- Python-to-JavaScript communication (Req 11.1)
- Error handling and response formatting (Req 11.7)
- Concurrent request handling
- Progress callbacks working correctly

These tests verify that the @eel.expose decorated functions in gui_app.py
properly integrate with the backend components and handle all edge cases.
"""

import pytest
import time
import threading
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List

# Import the GUI app module and its components
import src.gui.gui_app as gui_app
from src.gui.gui_task_manager import TaskAlreadyRunningError, TaskStatus
from src.gui.gui_config_manager import GUIConfigManager
from src.gui.gui_history_manager import GUIHistoryManager, HistoryEntry
from src.core.models import TaskResult, ExecutionStep
from src.core.config import ConfigurationError


class TestEelBridgeTaskExecution:
    """Test suite for task execution through Eel bridge."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Store original values
        original_task_manager = gui_app.task_manager
        original_config_manager = gui_app.config_manager_gui
        original_history_manager = gui_app.history_manager
        
        # Create mock managers
        gui_app.task_manager = Mock()
        gui_app.config_manager_gui = Mock()
        gui_app.history_manager = Mock()
        
        yield
        
        # Restore original values
        gui_app.task_manager = original_task_manager
        gui_app.config_manager_gui = original_config_manager
        gui_app.history_manager = original_history_manager
    
    def test_run_task_returns_success_response(self):
        """run_task should return success response when task starts (Req 11.1)."""
        # Arrange
        gui_app.task_manager.run_task = Mock(return_value='task-123')
        
        # Act
        response = gui_app.run_task("Create a hello world function")
        
        # Assert
        assert isinstance(response, dict)
        assert response['success'] is True
        assert 'task_id' in response
        assert response['task_id'] == 'task-123'
        
        # Verify task_manager was called correctly
        gui_app.task_manager.run_task.assert_called_once()
        call_args = gui_app.task_manager.run_task.call_args
        assert call_args[0][0] == "Create a hello world function"
        assert callable(call_args[0][1])  # Callback function
    
    def test_run_task_validates_empty_description(self):
        """run_task should reject empty task descriptions (Req 11.7)."""
        # Act - empty string
        response1 = gui_app.run_task("")
        
        # Assert
        assert response1['success'] is False
        assert 'error' in response1
        assert 'empty' in response1['error'].lower()
        
        # Act - whitespace only
        response2 = gui_app.run_task("   \n\t  ")
        
        # Assert
        assert response2['success'] is False
        assert 'error' in response2
    
    def test_run_task_handles_task_already_running_error(self):
        """run_task should return user-friendly error for concurrent tasks (Req 11.7)."""
        # Arrange
        gui_app.task_manager.run_task = Mock(
            side_effect=TaskAlreadyRunningError("Task is running")
        )
        
        # Act
        response = gui_app.run_task("Create a test file")
        
        # Assert
        assert response['success'] is False
        assert 'error' in response
        assert 'already running' in response['error'].lower()
        # Should be user-friendly, not technical
        assert 'TaskAlreadyRunningError' not in response['error']
    
    def test_run_task_handles_unexpected_errors(self):
        """run_task should handle unexpected errors gracefully (Req 11.7)."""
        # Arrange
        gui_app.task_manager.run_task = Mock(
            side_effect=RuntimeError("Unexpected backend error")
        )
        
        # Act
        response = gui_app.run_task("Create a test file")
        
        # Assert
        assert response['success'] is False
        assert 'error' in response
        assert 'Failed to start task' in response['error']
    
    def test_run_task_when_not_initialized(self):
        """run_task should handle uninitialized state (Req 11.7)."""
        # Arrange
        gui_app.task_manager = None
        
        # Act
        response = gui_app.run_task("Create a test file")
        
        # Assert
        assert response['success'] is False
        assert 'error' in response
        assert 'not properly initialized' in response['error'].lower()
    
    def test_stop_task_returns_success_when_running(self):
        """stop_task should return success when task is stopped."""
        # Arrange
        gui_app.task_manager.stop_task = Mock(return_value=True)
        
        # Act
        response = gui_app.stop_task()
        
        # Assert
        assert isinstance(response, dict)
        assert response['success'] is True
        assert 'message' in response
        assert 'stop signal sent' in response['message'].lower()
    
    def test_stop_task_returns_failure_when_no_task_running(self):
        """stop_task should indicate when no task is running."""
        # Arrange
        gui_app.task_manager.stop_task = Mock(return_value=False)
        
        # Act
        response = gui_app.stop_task()
        
        # Assert
        assert response['success'] is False
        assert 'message' in response
        assert 'no task' in response['message'].lower()
    
    def test_stop_task_handles_errors(self):
        """stop_task should handle errors gracefully (Req 11.7)."""
        # Arrange
        gui_app.task_manager.stop_task = Mock(
            side_effect=RuntimeError("Stop failed")
        )
        
        # Act
        response = gui_app.stop_task()
        
        # Assert
        assert response['success'] is False
        assert 'message' in response
        assert 'error' in response['message'].lower()


class TestEelBridgeConfiguration:
    """Test suite for configuration management through Eel bridge."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        original_config_manager = gui_app.config_manager_gui
        gui_app.config_manager_gui = Mock()
        
        yield
        
        gui_app.config_manager_gui = original_config_manager
    
    def test_get_config_returns_config_dict(self):
        """get_config should return configuration dictionary (Req 11.1)."""
        # Arrange
        mock_config = {
            'llm': {
                'endpoint': 'http://localhost:1234',
                'model_name': 'test-model',
                'temperature': 0.7
            },
            'project_root': '/path/to/project'
        }
        gui_app.config_manager_gui.get_config_for_gui = Mock(return_value=mock_config)
        
        # Act
        response = gui_app.get_config()
        
        # Assert
        assert isinstance(response, dict)
        assert response == mock_config
        assert 'llm' in response
        assert 'project_root' in response
    
    def test_get_config_handles_errors(self):
        """get_config should handle errors and return error dict (Req 11.7)."""
        # Arrange
        gui_app.config_manager_gui.get_config_for_gui = Mock(
            side_effect=ConfigurationError("Config file corrupted")
        )
        
        # Act
        response = gui_app.get_config()
        
        # Assert
        assert isinstance(response, dict)
        assert 'error' in response
        assert 'config' in response['error'].lower()
    
    def test_get_config_when_not_initialized(self):
        """get_config should handle uninitialized state (Req 11.7)."""
        # Arrange
        gui_app.config_manager_gui = None
        
        # Act
        response = gui_app.get_config()
        
        # Assert
        assert 'error' in response
        assert 'not initialized' in response['error'].lower()
    
    def test_save_config_returns_success(self):
        """save_config should return success response."""
        # Arrange
        config_data = {
            'llm': {'endpoint': 'http://localhost:1234'},
            'project_root': '/new/path'
        }
        gui_app.config_manager_gui.save_config = Mock(
            return_value=(True, 'Configuration saved successfully')
        )
        
        # Act
        response = gui_app.save_config(config_data)
        
        # Assert
        assert response['success'] is True
        assert 'message' in response
        assert 'saved successfully' in response['message'].lower()
        gui_app.config_manager_gui.save_config.assert_called_once_with(config_data)
    
    def test_save_config_returns_validation_errors(self):
        """save_config should return validation errors (Req 11.7)."""
        # Arrange
        config_data = {'llm': {'endpoint': 'invalid-url'}}
        gui_app.config_manager_gui.save_config = Mock(
            return_value=(False, 'Invalid endpoint URL format')
        )
        
        # Act
        response = gui_app.save_config(config_data)
        
        # Assert
        assert response['success'] is False
        assert 'error' in response
        assert 'invalid endpoint' in response['error'].lower()
    
    def test_save_config_handles_unexpected_errors(self):
        """save_config should handle unexpected errors (Req 11.7)."""
        # Arrange
        config_data = {'llm': {'endpoint': 'http://localhost:1234'}}
        gui_app.config_manager_gui.save_config = Mock(
            side_effect=IOError("Disk full")
        )
        
        # Act
        response = gui_app.save_config(config_data)
        
        # Assert
        assert response['success'] is False
        assert 'error' in response
        assert 'unexpected error' in response['error'].lower()
    
    def test_validate_config_field_returns_valid(self):
        """validate_config_field should return valid status."""
        # Arrange
        gui_app.config_manager_gui.validate_field = Mock(return_value=(True, None))
        
        # Act
        response = gui_app.validate_config_field('llm.temperature', 0.7)
        
        # Assert
        assert response['valid'] is True
        assert 'error' not in response
        gui_app.config_manager_gui.validate_field.assert_called_once_with(
            'llm.temperature', 0.7
        )
    
    def test_validate_config_field_returns_invalid(self):
        """validate_config_field should return validation errors."""
        # Arrange
        gui_app.config_manager_gui.validate_field = Mock(
            return_value=(False, 'Temperature must be between 0 and 1')
        )
        
        # Act
        response = gui_app.validate_config_field('llm.temperature', 1.5)
        
        # Assert
        assert response['valid'] is False
        assert 'error' in response
        assert 'temperature' in response['error'].lower()
    
    def test_validate_config_field_handles_errors(self):
        """validate_config_field should handle errors (Req 11.7)."""
        # Arrange
        gui_app.config_manager_gui.validate_field = Mock(
            side_effect=ValueError("Invalid field name")
        )
        
        # Act
        response = gui_app.validate_config_field('invalid.field', 'value')
        
        # Assert
        assert response['valid'] is False
        assert 'error' in response


class TestEelBridgeHistory:
    """Test suite for history management through Eel bridge."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        original_history_manager = gui_app.history_manager
        gui_app.history_manager = Mock()
        
        yield
        
        gui_app.history_manager = original_history_manager
    
    def test_get_history_returns_list(self):
        """get_history should return list of history entries (Req 11.1)."""
        # Arrange
        mock_entries = [
            HistoryEntry(
                entry_id='entry-1',
                task_description='Create test file',
                timestamp=datetime(2024, 1, 1, 12, 0, 0),
                duration_seconds=5.2,
                status='success',
                output='File created successfully'
            ),
            HistoryEntry(
                entry_id='entry-2',
                task_description='Run tests',
                timestamp=datetime(2024, 1, 1, 12, 5, 0),
                duration_seconds=10.5,
                status='failed',
                output='Test execution output',
                error_message='Test failed'
            )
        ]
        gui_app.history_manager.get_entries = Mock(return_value=mock_entries)
        
        # Act
        response = gui_app.get_history(limit=100)
        
        # Assert
        assert isinstance(response, list)
        assert len(response) == 2
        assert response[0]['entry_id'] == 'entry-1'
        assert response[0]['task_description'] == 'Create test file'
        assert response[0]['status'] == 'success'
        assert response[1]['status'] == 'failed'
        
        gui_app.history_manager.get_entries.assert_called_once_with(
            limit=100, search_query=None
        )
    
    def test_get_history_with_search_query(self):
        """get_history should pass search query to manager."""
        # Arrange
        gui_app.history_manager.get_entries = Mock(return_value=[])
        
        # Act
        response = gui_app.get_history(limit=50, search_query='test')
        
        # Assert
        gui_app.history_manager.get_entries.assert_called_once_with(
            limit=50, search_query='test'
        )
    
    def test_get_history_handles_errors(self):
        """get_history should handle errors gracefully (Req 11.7)."""
        # Arrange
        gui_app.history_manager.get_entries = Mock(
            side_effect=RuntimeError("Database error")
        )
        
        # Act
        response = gui_app.get_history()
        
        # Assert
        assert isinstance(response, list)
        assert len(response) == 0  # Returns empty list on error
    
    def test_get_history_entry_returns_full_details(self):
        """get_history_entry should return complete entry details."""
        # Arrange
        mock_entry = HistoryEntry(
            entry_id='entry-123',
            task_description='Create comprehensive test suite',
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            duration_seconds=15.7,
            status='success',
            output='Created 10 test files with 50 test cases',
            config_snapshot={'llm': {'model_name': 'test-model'}}
        )
        gui_app.history_manager.get_entry_by_id = Mock(return_value=mock_entry)
        
        # Act
        response = gui_app.get_history_entry('entry-123')
        
        # Assert
        assert isinstance(response, dict)
        assert response['entry_id'] == 'entry-123'
        assert response['task_description'] == 'Create comprehensive test suite'
        assert response['status'] == 'success'
        assert 'output' in response
        assert 'config_snapshot' in response
    
    def test_get_history_entry_returns_none_when_not_found(self):
        """get_history_entry should return None for missing entries."""
        # Arrange
        gui_app.history_manager.get_entry_by_id = Mock(return_value=None)
        
        # Act
        response = gui_app.get_history_entry('nonexistent-id')
        
        # Assert
        assert response is None
    
    def test_delete_history_entry_returns_success(self):
        """delete_history_entry should return success response."""
        # Arrange
        gui_app.history_manager.delete_entry = Mock(return_value=True)
        
        # Act
        response = gui_app.delete_history_entry('entry-123')
        
        # Assert
        assert response['success'] is True
        assert 'message' in response
        gui_app.history_manager.delete_entry.assert_called_once_with('entry-123')
    
    def test_delete_history_entry_returns_not_found(self):
        """delete_history_entry should indicate when entry not found."""
        # Arrange
        gui_app.history_manager.delete_entry = Mock(return_value=False)
        
        # Act
        response = gui_app.delete_history_entry('nonexistent-id')
        
        # Assert
        assert response['success'] is False
        assert 'not found' in response['message'].lower()
    
    def test_clear_all_history_returns_count(self):
        """clear_all_history should return count of deleted entries."""
        # Arrange
        gui_app.history_manager.clear_all = Mock(return_value=42)
        
        # Act
        response = gui_app.clear_all_history()
        
        # Assert
        assert response['success'] is True
        assert response['count'] == 42
        assert 'message' in response
    
    def test_export_history_json_returns_success(self):
        """export_history should export to JSON successfully."""
        # Arrange
        gui_app.history_manager.export_to_json = Mock(return_value=True)
        
        # Act
        response = gui_app.export_history('json', '/path/to/export.json')
        
        # Assert
        assert response['success'] is True
        assert 'message' in response
        gui_app.history_manager.export_to_json.assert_called_once_with(
            '/path/to/export.json'
        )
    
    def test_export_history_csv_returns_success(self):
        """export_history should export to CSV successfully."""
        # Arrange
        gui_app.history_manager.export_to_csv = Mock(return_value=True)
        
        # Act
        response = gui_app.export_history('csv', '/path/to/export.csv')
        
        # Assert
        assert response['success'] is True
        gui_app.history_manager.export_to_csv.assert_called_once_with(
            '/path/to/export.csv'
        )
    
    def test_export_history_invalid_format(self):
        """export_history should reject invalid format types."""
        # Act
        response = gui_app.export_history('xml', '/path/to/export.xml')
        
        # Assert
        assert response['success'] is False
        assert 'invalid format' in response['message'].lower()


class TestEelBridgeUtilities:
    """Test suite for utility functions through Eel bridge."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        original_task_manager = gui_app.task_manager
        gui_app.task_manager = Mock()
        
        yield
        
        gui_app.task_manager = original_task_manager
    
    def test_get_app_status_returns_initialized_status(self):
        """get_app_status should return application status."""
        # Arrange
        mock_status = TaskStatus(
            is_running=False,
            task_id=None,
            description=None,
            start_time=None,
            elapsed_seconds=None
        )
        gui_app.task_manager.get_status = Mock(return_value=mock_status)
        
        # Act
        response = gui_app.get_app_status()
        
        # Assert
        assert isinstance(response, dict)
        assert response['initialized'] is True
        assert 'version' in response
        assert response['task_running'] is False
    
    def test_get_app_status_with_running_task(self):
        """get_app_status should include task details when running."""
        # Arrange
        mock_status = TaskStatus(
            is_running=True,
            task_id='task-456',
            description='Running test',
            start_time=datetime.now(),
            elapsed_seconds=5.2
        )
        gui_app.task_manager.get_status = Mock(return_value=mock_status)
        
        # Act
        response = gui_app.get_app_status()
        
        # Assert
        assert response['task_running'] is True
        assert response['current_task_id'] == 'task-456'
        assert response['elapsed_seconds'] == 5.2
    
    def test_get_app_status_when_not_initialized(self):
        """get_app_status should handle uninitialized state."""
        # Arrange
        gui_app.task_manager = None
        
        # Act
        response = gui_app.get_app_status()
        
        # Assert
        assert response['initialized'] is False
        assert 'version' in response


class TestEelBridgeErrorFormatting:
    """Test suite for error response formatting (Req 11.7)."""
    
    def test_error_suggestions_for_connection_errors(self):
        """Error suggestions should provide helpful advice for connection errors."""
        # Act
        suggestion = gui_app._get_error_suggestion("Connection refused to LLM server")
        
        # Assert
        assert 'server' in suggestion.lower()
        assert 'running' in suggestion.lower() or 'endpoint' in suggestion.lower()
    
    def test_error_suggestions_for_timeout_errors(self):
        """Error suggestions should provide helpful advice for timeout errors."""
        # Act
        suggestion = gui_app._get_error_suggestion("Request timeout after 30 seconds")
        
        # Assert
        assert 'timeout' in suggestion.lower() or 'server' in suggestion.lower()
    
    def test_error_suggestions_for_api_key_errors(self):
        """Error suggestions should provide helpful advice for API key errors."""
        # Act
        suggestion = gui_app._get_error_suggestion("Invalid API key provided")
        
        # Assert
        assert 'api key' in suggestion.lower()
        assert 'settings' in suggestion.lower()
    
    def test_error_suggestions_for_permission_errors(self):
        """Error suggestions should provide helpful advice for permission errors."""
        # Act
        suggestion = gui_app._get_error_suggestion("Permission denied: /protected/file")
        
        # Assert
        assert 'permission' in suggestion.lower()
    
    def test_task_summary_formatting(self):
        """Task summaries should be formatted clearly."""
        # Arrange
        result = {
            'actions_taken': ['create_file', 'run_tests'],
            'files_modified': ['test.py', 'main.py'],
            'tests_passed': True
        }
        
        # Act
        summary = gui_app._create_task_summary(result)
        
        # Assert
        assert '2 action' in summary
        assert '2 file' in summary
        assert 'test' in summary.lower()


class TestEelBridgeConcurrentRequests:
    """Test suite for concurrent request handling."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        original_task_manager = gui_app.task_manager
        original_config_manager = gui_app.config_manager_gui
        original_history_manager = gui_app.history_manager
        
        gui_app.task_manager = Mock()
        gui_app.config_manager_gui = Mock()
        gui_app.history_manager = Mock()
        
        yield
        
        gui_app.task_manager = original_task_manager
        gui_app.config_manager_gui = original_config_manager
        gui_app.history_manager = original_history_manager
    
    def test_multiple_config_reads_concurrent(self):
        """Multiple get_config calls should work concurrently."""
        # Arrange
        mock_config = {'llm': {'endpoint': 'http://localhost:1234'}}
        gui_app.config_manager_gui.get_config_for_gui = Mock(return_value=mock_config)
        
        results = []
        
        def call_get_config():
            result = gui_app.get_config()
            results.append(result)
        
        # Act - spawn multiple threads calling get_config
        threads = [threading.Thread(target=call_get_config) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=2.0)
        
        # Assert - all calls should succeed
        assert len(results) == 5
        for result in results:
            assert result == mock_config
    
    def test_multiple_history_reads_concurrent(self):
        """Multiple get_history calls should work concurrently."""
        # Arrange
        gui_app.history_manager.get_entries = Mock(return_value=[])
        
        results = []
        
        def call_get_history():
            result = gui_app.get_history(limit=10)
            results.append(result)
        
        # Act - spawn multiple threads
        threads = [threading.Thread(target=call_get_history) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=2.0)
        
        # Assert - all calls should succeed
        assert len(results) == 5
        for result in results:
            assert isinstance(result, list)
    
    def test_config_save_while_reading(self):
        """Config save and read operations should work concurrently."""
        # Arrange
        mock_config = {'llm': {'endpoint': 'http://localhost:1234'}}
        gui_app.config_manager_gui.get_config_for_gui = Mock(return_value=mock_config)
        gui_app.config_manager_gui.save_config = Mock(
            return_value=(True, 'Saved')
        )
        
        results = {'reads': [], 'writes': []}
        
        def read_config():
            result = gui_app.get_config()
            results['reads'].append(result)
        
        def write_config():
            result = gui_app.save_config(mock_config)
            results['writes'].append(result)
        
        # Act - spawn mixed read/write threads
        threads = []
        for i in range(10):
            if i % 2 == 0:
                threads.append(threading.Thread(target=read_config))
            else:
                threads.append(threading.Thread(target=write_config))
        
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=2.0)
        
        # Assert - all operations should succeed
        assert len(results['reads']) == 5
        assert len(results['writes']) == 5
        
        for read_result in results['reads']:
            assert read_result == mock_config
        
        for write_result in results['writes']:
            assert write_result['success'] is True
    
    def test_status_checks_while_task_running(self):
        """Status checks should work while task is running."""
        # Arrange
        gui_app.task_manager.run_task = Mock(return_value='task-789')
        
        # Mock status that changes over time
        call_count = {'count': 0}
        
        def mock_get_status():
            call_count['count'] += 1
            if call_count['count'] < 3:
                return TaskStatus(
                    is_running=True,
                    task_id='task-789',
                    description='Test',
                    start_time=datetime.now(),
                    elapsed_seconds=call_count['count'] * 0.5
                )
            else:
                return TaskStatus(
                    is_running=False,
                    task_id=None,
                    description=None,
                    start_time=None,
                    elapsed_seconds=None
                )
        
        gui_app.task_manager.get_status = mock_get_status
        
        # Act - start task
        start_response = gui_app.run_task("Test task")
        assert start_response['success'] is True
        
        # Act - check status multiple times
        status_results = []
        for _ in range(5):
            status = gui_app.get_app_status()
            status_results.append(status)
            time.sleep(0.1)
        
        # Assert - all status checks should succeed
        assert len(status_results) == 5
        assert all(isinstance(s, dict) for s in status_results)


class TestEelBridgeProgressCallbacks:
    """Test suite for progress callback functionality (Req 11.4)."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        original_task_manager = gui_app.task_manager
        original_history_manager = gui_app.history_manager
        
        gui_app.task_manager = Mock()
        gui_app.history_manager = Mock()
        
        yield
        
        gui_app.task_manager = original_task_manager
        gui_app.history_manager = original_history_manager
    
    @patch('src.gui.gui_app.eel')
    def test_progress_callback_calls_eel_update(self, mock_eel):
        """Progress callbacks should call eel.update_progress (Req 11.4)."""
        # Arrange
        captured_callback = None
        
        def capture_callback(description, callback):
            nonlocal captured_callback
            captured_callback = callback
            return 'task-001'
        
        gui_app.task_manager.run_task = capture_callback
        
        # Act - call run_task to capture the callback
        response = gui_app.run_task("Test task")
        
        # Assert - callback should be captured
        assert captured_callback is not None
        
        # Act - invoke the callback with progress event
        captured_callback('progress', {
            'type': 'info',
            'message': 'Processing file test.py',
            'timestamp': datetime.now().isoformat()
        })
        
        # Assert - eel.update_progress should have been called
        mock_eel.update_progress.assert_called()
        call_args = mock_eel.update_progress.call_args[0][0]
        assert call_args['type'] == 'info'
        assert 'Processing file' in call_args['message']
    
    @patch('src.gui.gui_app.eel')
    def test_task_complete_callback_calls_eel(self, mock_eel):
        """Task completion should trigger eel.task_completed (Req 11.4)."""
        # Arrange
        captured_callback = None
        
        def capture_callback(description, callback):
            nonlocal captured_callback
            captured_callback = callback
            return 'task-002'
        
        gui_app.task_manager.run_task = capture_callback
        gui_app.history_manager.add_entry = Mock()
        
        # Act - capture callback
        gui_app.run_task("Test task")
        
        # Act - invoke complete event
        captured_callback('complete', {
            'task_id': 'task-002',
            'duration': 10.5,
            'result': {'actions_taken': ['test']},
            'timestamp': datetime.now().isoformat()
        })
        
        # Assert - eel.task_completed should be called
        mock_eel.task_completed.assert_called()
        call_args = mock_eel.task_completed.call_args[0][0]
        assert call_args['task_id'] == 'task-002'
        assert call_args['status'] == 'success'
        assert call_args['duration'] == 10.5
    
    @patch('src.gui.gui_app.eel')
    def test_task_error_callback_calls_eel(self, mock_eel):
        """Task errors should trigger eel.task_error (Req 11.4, 11.7)."""
        # Arrange
        captured_callback = None
        
        def capture_callback(description, callback):
            nonlocal captured_callback
            captured_callback = callback
            return 'task-003'
        
        gui_app.task_manager.run_task = capture_callback
        gui_app.history_manager.add_entry = Mock()
        
        # Act - capture callback
        gui_app.run_task("Test task")
        
        # Act - invoke error event
        captured_callback('error', {
            'task_id': 'task-003',
            'error': 'Connection timeout',
            'timestamp': datetime.now().isoformat()
        })
        
        # Assert - eel.task_error should be called
        mock_eel.task_error.assert_called()
        call_args = mock_eel.task_error.call_args[0][0]
        assert call_args['task_id'] == 'task-003'
        assert 'connection' in call_args['error_message'].lower()
        assert 'suggestion' in call_args  # Should provide user-friendly suggestion
    
    @patch('src.gui.gui_app.eel')
    def test_callback_error_handling(self, mock_eel):
        """Callback errors should not crash the application (Req 11.7)."""
        # Arrange
        mock_eel.update_progress.side_effect = RuntimeError("Eel communication error")
        
        captured_callback = None
        
        def capture_callback(description, callback):
            nonlocal captured_callback
            captured_callback = callback
            return 'task-004'
        
        gui_app.task_manager.run_task = capture_callback
        
        # Act - capture callback
        gui_app.run_task("Test task")
        
        # Act - invoke callback (should not raise exception)
        try:
            captured_callback('progress', {
                'type': 'info',
                'message': 'Test message',
                'timestamp': datetime.now().isoformat()
            })
            success = True
        except Exception:
            success = False
        
        # Assert - should handle error gracefully
        assert success is True


@pytest.mark.integration
class TestEelBridgeIntegrationScenarios:
    """End-to-end integration test scenarios."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        original_task_manager = gui_app.task_manager
        original_config_manager = gui_app.config_manager_gui
        original_history_manager = gui_app.history_manager
        
        gui_app.task_manager = Mock()
        gui_app.config_manager_gui = Mock()
        gui_app.history_manager = Mock()
        
        yield
        
        gui_app.task_manager = original_task_manager
        gui_app.config_manager_gui = original_config_manager
        gui_app.history_manager = original_history_manager
    
    @patch('src.gui.gui_app.eel')
    def test_complete_task_execution_workflow(self, mock_eel):
        """Test complete workflow: start task -> progress -> complete -> history (Req 11.1)."""
        # Arrange
        gui_app.task_manager.run_task = Mock(return_value='task-flow-1')
        gui_app.history_manager.add_entry = Mock()
        gui_app.history_manager.get_entries = Mock(return_value=[
            HistoryEntry(
                entry_id='task-flow-1',
                task_description='Workflow test',
                timestamp=datetime.now(),
                duration_seconds=5.0,
                status='success',
                output='Task completed'
            )
        ])
        
        # Act 1 - Start task
        start_response = gui_app.run_task("Workflow test")
        assert start_response['success'] is True
        task_id = start_response['task_id']
        
        # Act 2 - Simulate progress via callback
        callback = gui_app.task_manager.run_task.call_args[0][1]
        callback('start', {
            'task_id': task_id,
            'description': 'Workflow test',
            'timestamp': datetime.now().isoformat()
        })
        
        callback('progress', {
            'type': 'info',
            'message': 'Step 1 complete',
            'timestamp': datetime.now().isoformat()
        })
        
        # Act 3 - Complete task
        callback('complete', {
            'task_id': task_id,
            'duration': 5.0,
            'result': {'actions_taken': ['test']},
            'timestamp': datetime.now().isoformat()
        })
        
        # Act 4 - Fetch history
        history = gui_app.get_history(limit=10)
        
        # Assert - Complete workflow succeeded
        assert len(history) == 1
        assert history[0]['entry_id'] == task_id
        assert history[0]['status'] == 'success'
        
        # Assert - All Eel calls were made
        assert mock_eel.update_progress.called
        assert mock_eel.task_completed.called
    
    def test_config_update_workflow(self):
        """Test complete config workflow: load -> validate -> save (Req 11.1)."""
        # Arrange
        initial_config = {
            'llm': {'endpoint': 'http://localhost:1234', 'temperature': 0.7}
        }
        updated_config = {
            'llm': {'endpoint': 'http://localhost:5678', 'temperature': 0.8}
        }
        
        gui_app.config_manager_gui.get_config_for_gui = Mock(return_value=initial_config)
        gui_app.config_manager_gui.validate_field = Mock(return_value=(True, None))
        gui_app.config_manager_gui.save_config = Mock(return_value=(True, 'Saved'))
        
        # Act 1 - Load config
        config = gui_app.get_config()
        assert config == initial_config
        
        # Act 2 - Validate new endpoint
        validation = gui_app.validate_config_field('llm.endpoint', 'http://localhost:5678')
        assert validation['valid'] is True
        
        # Act 3 - Validate new temperature
        validation = gui_app.validate_config_field('llm.temperature', 0.8)
        assert validation['valid'] is True
        
        # Act 4 - Save config
        save_result = gui_app.save_config(updated_config)
        assert save_result['success'] is True
        
        # Assert - Workflow completed successfully
        gui_app.config_manager_gui.save_config.assert_called_once_with(updated_config)
