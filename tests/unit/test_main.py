"""Unit tests for main entry point (src/main.py).

Tests cover:
- Logging setup with different verbosity levels
- Component initialization with valid configuration
- Graceful error handling for initialization failures
- CLI argument parsing
- Task execution modes (single task vs interactive)

Requirements tested:
- 1.3: Initialize all components using local resources only
- 15.6: Provide different log verbosity levels
"""

import pytest
import logging
import sys
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path

from src.main import (
    setup_logging,
    initialize_components,
    parse_arguments,
    execute_single_task,
    main,
    VERSION
)
from src.core.models import SystemConfig, LLMConfig, TaskResult, ExecutionStep
from src.core.config import ConfigurationError
from src.core.llm_interface import ModelUnavailableError


class TestSetupLogging:
    """Test logging setup with different verbosity levels.
    
    Requirements: 15.6 - Provide different log verbosity levels
    """
    
    def test_debug_level(self):
        """Test logging setup with debug level."""
        logger = setup_logging("debug")
        assert logger.level == logging.DEBUG
        assert logger.name == "local_ai_dev"
    
    def test_info_level(self):
        """Test logging setup with info level."""
        logger = setup_logging("info")
        assert logger.level == logging.INFO
    
    def test_warning_level(self):
        """Test logging setup with warning level."""
        logger = setup_logging("warning")
        assert logger.level == logging.WARNING
    
    def test_error_level(self):
        """Test logging setup with error level."""
        logger = setup_logging("error")
        assert logger.level == logging.ERROR
    
    def test_invalid_level_defaults_to_info(self):
        """Test that invalid log level defaults to INFO."""
        logger = setup_logging("invalid")
        assert logger.level == logging.INFO
    
    def test_case_insensitive(self):
        """Test that log level is case insensitive."""
        logger = setup_logging("DEBUG")
        assert logger.level == logging.DEBUG
        
        logger = setup_logging("WaRnInG")
        assert logger.level == logging.WARNING


class TestInitializeComponents:
    """Test component initialization.
    
    Requirements: 1.3 - Initialize all components using local resources only
    """
    
    @pytest.fixture
    def valid_config(self):
        """Create a valid system configuration."""
        return SystemConfig(
            llm=LLMConfig(
                endpoint="http://localhost:11434",
                model_name="codellama:13b",
                temperature=0.2,
                max_tokens=4096,
                context_length=16384,
                backend_type="ollama"
            ),
            project_root=".",
            log_level="info",
            web_research_enabled=True,
            self_improvement_enabled=False,
            excluded_directories=["node_modules", ".git", "__pycache__"]
        )
    
    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return logging.getLogger("test")
    
    @patch('src.main.LocalLLMInterface')
    @patch('src.main.FileOperations')
    @patch('src.main.CodeSearch')
    @patch('src.main.CommandExecutor')
    @patch('src.main.CodeAgent')
    @patch('src.main.ContextManager')
    @patch('src.main.TaskExecutor')
    def test_successful_initialization(
        self,
        mock_task_executor,
        mock_context_manager,
        mock_code_agent,
        mock_command_executor,
        mock_code_search,
        mock_file_ops,
        mock_llm_interface,
        valid_config,
        logger
    ):
        """Test successful initialization of all components."""
        # Setup mocks
        mock_llm = Mock()
        mock_llm.is_available.return_value = True
        mock_llm_interface.return_value = mock_llm
        
        mock_context = Mock()
        mock_context.languages = ["Python"]
        mock_context.frameworks = ["pytest"]
        mock_context_mgr = Mock()
        mock_context_mgr.scan_project.return_value = mock_context
        mock_context_manager.return_value = mock_context_mgr
        
        # Execute initialization
        task_executor, llm_interface, code_agent, context_manager = initialize_components(
            valid_config, logger
        )
        
        # Verify all components were initialized
        mock_llm_interface.assert_called_once()
        mock_file_ops.assert_called_once()
        mock_code_search.assert_called_once()
        mock_command_executor.assert_called_once()
        mock_code_agent.assert_called_once()
        mock_context_manager.assert_called_once()
        mock_task_executor.assert_called_once()
        
        # Verify LLM availability was checked
        mock_llm.is_available.assert_called_once()
        
        # Verify project scan was performed
        mock_context_mgr.scan_project.assert_called_once_with(valid_config.project_root)
    
    @patch('src.main.LocalLLMInterface')
    def test_llm_unavailable_error(self, mock_llm_interface, valid_config, logger):
        """Test graceful handling when LLM is unavailable."""
        # Setup mock to return unavailable LLM
        mock_llm = Mock()
        mock_llm.is_available.return_value = False
        mock_llm_interface.return_value = mock_llm
        
        # Should raise ModelUnavailableError
        with pytest.raises(ModelUnavailableError) as exc_info:
            initialize_components(valid_config, logger)
        
        assert "not responding" in str(exc_info.value)
        assert valid_config.llm.endpoint in str(exc_info.value)
    
    @patch('src.main.LocalLLMInterface')
    @patch('src.main.FileOperations')
    def test_file_operations_initialization_error(
        self,
        mock_file_ops,
        mock_llm_interface,
        valid_config,
        logger
    ):
        """Test graceful handling when file operations initialization fails."""
        # Setup LLM to succeed
        mock_llm = Mock()
        mock_llm.is_available.return_value = True
        mock_llm_interface.return_value = mock_llm
        
        # Setup file operations to fail
        mock_file_ops.side_effect = Exception("Permission denied")
        
        # Should raise ConfigurationError
        with pytest.raises(ConfigurationError) as exc_info:
            initialize_components(valid_config, logger)
        
        assert "File operations initialization failed" in str(exc_info.value)
    
    @patch('src.main.LocalLLMInterface')
    @patch('src.main.FileOperations')
    @patch('src.main.CodeSearch')
    @patch('src.main.CommandExecutor')
    @patch('src.main.CodeAgent')
    @patch('src.main.ContextManager')
    def test_context_manager_initialization_error(
        self,
        mock_context_manager,
        mock_code_agent,
        mock_command_executor,
        mock_code_search,
        mock_file_ops,
        mock_llm_interface,
        valid_config,
        logger
    ):
        """Test graceful handling when context manager initialization fails."""
        # Setup mocks to succeed until context manager
        mock_llm = Mock()
        mock_llm.is_available.return_value = True
        mock_llm_interface.return_value = mock_llm
        
        # Setup context manager to fail
        mock_context_manager.side_effect = Exception("Failed to scan project")
        
        # Should raise ConfigurationError
        with pytest.raises(ConfigurationError) as exc_info:
            initialize_components(valid_config, logger)
        
        assert "Context manager initialization failed" in str(exc_info.value)


class TestParseArguments:
    """Test command-line argument parsing."""
    
    def test_no_arguments(self):
        """Test parsing with no arguments (interactive mode)."""
        with patch('sys.argv', ['main.py']):
            args = parse_arguments()
            assert args.task is None
            assert args.config is None
            assert args.log_level is None
            assert args.project_root is None
    
    def test_single_task_mode(self):
        """Test parsing with --task argument."""
        with patch('sys.argv', ['main.py', '--task', 'Create a new module']):
            args = parse_arguments()
            assert args.task == 'Create a new module'
    
    def test_custom_config_file(self):
        """Test parsing with --config argument."""
        with patch('sys.argv', ['main.py', '--config', '/path/to/config.yaml']):
            args = parse_arguments()
            assert args.config == '/path/to/config.yaml'
    
    def test_log_level_argument(self):
        """Test parsing with --log-level argument."""
        with patch('sys.argv', ['main.py', '--log-level', 'debug']):
            args = parse_arguments()
            assert args.log_level == 'debug'
    
    def test_project_root_argument(self):
        """Test parsing with --project-root argument."""
        with patch('sys.argv', ['main.py', '--project-root', '/custom/root']):
            args = parse_arguments()
            assert args.project_root == '/custom/root'
    
    def test_combined_arguments(self):
        """Test parsing with multiple arguments."""
        with patch('sys.argv', [
            'main.py',
            '--task', 'Test task',
            '--config', 'config.yaml',
            '--log-level', 'error',
            '--project-root', '/project'
        ]):
            args = parse_arguments()
            assert args.task == 'Test task'
            assert args.config == 'config.yaml'
            assert args.log_level == 'error'
            assert args.project_root == '/project'
    
    def test_version_argument(self):
        """Test --version argument."""
        with patch('sys.argv', ['main.py', '--version']):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()
            assert exc_info.value.code == 0


class TestExecuteSingleTask:
    """Test single task execution."""
    
    @pytest.fixture
    def mock_task_executor(self):
        """Create a mock task executor."""
        return Mock()
    
    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return logging.getLogger("test")
    
    def test_successful_task_execution(self, mock_task_executor, logger):
        """Test successful execution of a single task."""
        # Setup mock to return success
        success_result = TaskResult(
            success=True,
            actions_taken=[
                ExecutionStep(
                    action="create_file",
                    parameters={"path": "test.py", "content": "# Test"},
                    rationale="Create test file"
                )
            ],
            files_modified=["test.py"],
            tests_passed=True,
            error_message=None,
            execution_log=["Created test.py"]
        )
        mock_task_executor.execute_task.return_value = success_result
        
        # Execute task
        exit_code = execute_single_task(
            mock_task_executor,
            "Create a test file",
            logger
        )
        
        # Verify
        assert exit_code == 0
        mock_task_executor.execute_task.assert_called_once_with("Create a test file")
    
    def test_failed_task_execution(self, mock_task_executor, logger):
        """Test failed task execution."""
        # Setup mock to return failure
        failure_result = TaskResult(
            success=False,
            actions_taken=[],
            files_modified=[],
            tests_passed=False,
            error_message="Task failed",
            execution_log=["Error occurred"]
        )
        mock_task_executor.execute_task.return_value = failure_result
        
        # Execute task
        exit_code = execute_single_task(
            mock_task_executor,
            "Invalid task",
            logger
        )
        
        # Verify
        assert exit_code == 1
    
    def test_task_execution_with_exception(self, mock_task_executor, logger):
        """Test task execution when exception is raised."""
        # Setup mock to raise exception
        mock_task_executor.execute_task.side_effect = Exception("Unexpected error")
        
        # Execute task
        exit_code = execute_single_task(
            mock_task_executor,
            "Test task",
            logger
        )
        
        # Verify
        assert exit_code == 1


class TestMainFunction:
    """Test main function integration."""
    
    @patch('src.main.initialize_components')
    @patch('src.main.ConfigManager')
    @patch('src.main.execute_single_task')
    def test_main_single_task_success(
        self,
        mock_execute_single,
        mock_config_manager,
        mock_initialize
    ):
        """Test main function with successful single task execution."""
        # Setup mocks
        mock_config = Mock()
        mock_config.log_level = "info"
        mock_config.llm.endpoint = "http://localhost:11434"
        mock_config.llm.model_name = "test-model"
        
        mock_cm = Mock()
        mock_cm.load_config.return_value = mock_config
        mock_config_manager.return_value = mock_cm
        
        mock_task_executor = Mock()
        mock_initialize.return_value = (mock_task_executor, Mock(), Mock(), Mock())
        
        mock_execute_single.return_value = 0
        
        # Execute main with task argument
        with patch('sys.argv', ['main.py', '--task', 'Test task']):
            exit_code = main()
        
        # Verify
        assert exit_code == 0
        mock_execute_single.assert_called_once()
    
    @patch('src.main.ConfigManager')
    def test_main_configuration_error(self, mock_config_manager):
        """Test main function with configuration error."""
        # Setup mock to raise configuration error
        mock_cm = Mock()
        mock_cm.load_config.side_effect = ConfigurationError("Invalid config")
        mock_config_manager.return_value = mock_cm
        
        # Execute main
        with patch('sys.argv', ['main.py']):
            exit_code = main()
        
        # Verify
        assert exit_code == 1
    
    @patch('src.main.initialize_components')
    @patch('src.main.ConfigManager')
    def test_main_model_unavailable_error(
        self,
        mock_config_manager,
        mock_initialize
    ):
        """Test main function with model unavailable error."""
        # Setup mocks
        mock_config = Mock()
        mock_config.log_level = "info"
        mock_config.llm.endpoint = "http://localhost:11434"
        mock_config.llm.model_name = "test-model"
        
        mock_cm = Mock()
        mock_cm.load_config.return_value = mock_config
        mock_config_manager.return_value = mock_cm
        
        mock_initialize.side_effect = ModelUnavailableError("LLM not available")
        
        # Execute main
        with patch('sys.argv', ['main.py']):
            exit_code = main()
        
        # Verify
        assert exit_code == 1
    
    @patch('src.main.ConfigManager')
    def test_main_keyboard_interrupt(self, mock_config_manager):
        """Test main function with keyboard interrupt."""
        # Setup mock to raise KeyboardInterrupt
        mock_cm = Mock()
        mock_cm.load_config.side_effect = KeyboardInterrupt()
        mock_config_manager.return_value = mock_cm
        
        # Execute main
        with patch('sys.argv', ['main.py']):
            exit_code = main()
        
        # Verify
        assert exit_code == 130  # Standard exit code for SIGINT
    
    @patch('src.main.initialize_components')
    @patch('src.main.ConfigManager')
    def test_main_log_level_override(
        self,
        mock_config_manager,
        mock_initialize
    ):
        """Test that command-line log level overrides config file."""
        # Setup mocks
        mock_config = Mock()
        mock_config.log_level = "info"  # Config file says info
        
        mock_cm = Mock()
        mock_cm.load_config.return_value = mock_config
        mock_config_manager.return_value = mock_cm
        
        mock_task_executor = Mock()
        mock_initialize.return_value = (mock_task_executor, Mock(), Mock(), Mock())
        
        # Execute main with log-level argument
        with patch('sys.argv', ['main.py', '--log-level', 'debug', '--task', 'Test']):
            with patch('src.main.execute_single_task', return_value=0):
                main()
        
        # Verify config was updated
        assert mock_config.log_level == 'debug'
