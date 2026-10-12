"""Unit tests for TaskExecutor.

This module tests the TaskExecutor's core functionality including:
- Task planning with LLM
- Step execution and routing
- Agent loop orchestration
- State management
- Error handling
"""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.core.task_executor import TaskExecutor
from src.core.models import (
    ExecutionPlan,
    ExecutionStep,
    TaskResult,
    LLMResponse,
    ToolCall,
    LLMConfig
)
from src.core.llm_interface import (
    LocalLLMInterface,
    ModelUnavailableError,
    LLMTimeoutError
)
from src.agents.code_agent import CodeAgent
from src.agents.file_operations import OperationResult
from src.context.context_manager import ContextManager


class TestTaskExecutor:
    """Test suite for TaskExecutor class."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM interface."""
        llm = Mock(spec=LocalLLMInterface)
        return llm
    
    @pytest.fixture
    def mock_code_agent(self):
        """Create mock code agent."""
        agent = Mock(spec=CodeAgent)
        agent.file_ops = Mock()
        agent.code_search = Mock()
        agent.command_executor = Mock()
        return agent
    
    @pytest.fixture
    def mock_context_manager(self):
        """Create mock context manager."""
        manager = Mock(spec=ContextManager)
        return manager
    
    @pytest.fixture
    def task_executor(self, mock_llm, mock_code_agent, mock_context_manager):
        """Create TaskExecutor instance with mocks."""
        return TaskExecutor(
            llm_interface=mock_llm,
            code_agent=mock_code_agent,
            context_manager=mock_context_manager
        )
    
    def test_initialization(self, task_executor, mock_llm, mock_code_agent, mock_context_manager):
        """Test TaskExecutor initializes correctly."""
        assert task_executor.llm == mock_llm
        assert task_executor.code_agent == mock_code_agent
        assert task_executor.context_manager == mock_context_manager
        assert task_executor.execution_history == []
        assert task_executor.files_modified == []
        assert task_executor.test_results == {}
        assert task_executor.current_iteration == 0
    
    def test_plan_task_success(self, task_executor, mock_llm):
        """Test successful task planning."""
        # Mock LLM response with execution plan
        plan_json = {
            "steps": [
                {
                    "action": "create_file",
                    "parameters": {"file_path": "test.py", "content": "# test"},
                    "rationale": "Create test file"
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["file_ops"]
        }
        
        mock_llm.generate.return_value = LLMResponse(
            content=json.dumps(plan_json),
            tool_calls=[],
            finish_reason="stop"
        )
        
        # Call plan_task
        plan = task_executor.plan_task("Create a test file")
        
        # Verify plan
        assert plan is not None
        assert len(plan.steps) == 1
        assert plan.steps[0].action == "create_file"
        assert plan.steps[0].parameters["file_path"] == "test.py"
        assert plan.estimated_complexity == "simple"
        assert "file_ops" in plan.required_tools
        
        # Verify LLM was called
        mock_llm.generate.assert_called_once()
    
    def test_plan_task_with_markdown_code_block(self, task_executor, mock_llm):
        """Test task planning handles markdown code blocks."""
        # Mock LLM response with markdown code block
        plan_json = {
            "steps": [
                {
                    "action": "create_file",
                    "parameters": {"file_path": "test.py", "content": "pass"},
                    "rationale": "Create file"
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["file_ops"]
        }
        
        markdown_response = f"```json\n{json.dumps(plan_json)}\n```"
        
        mock_llm.generate.return_value = LLMResponse(
            content=markdown_response,
            tool_calls=[],
            finish_reason="stop"
        )
        
        # Call plan_task
        plan = task_executor.plan_task("Create a test file")
        
        # Verify plan was parsed correctly
        assert plan is not None
        assert len(plan.steps) == 1
        assert plan.steps[0].action == "create_file"
    
    def test_plan_task_llm_error(self, task_executor, mock_llm):
        """Test task planning handles LLM errors."""
        mock_llm.generate.side_effect = ModelUnavailableError("Model not found")
        
        plan = task_executor.plan_task("Create a file")
        
        assert plan is None
    
    def test_plan_task_empty_response(self, task_executor, mock_llm):
        """Test task planning handles empty LLM response."""
        mock_llm.generate.return_value = LLMResponse(
            content="",
            tool_calls=[],
            finish_reason="stop"
        )
        
        plan = task_executor.plan_task("Create a file")
        
        assert plan is None
    
    def test_plan_task_invalid_json(self, task_executor, mock_llm):
        """Test task planning handles invalid JSON."""
        mock_llm.generate.return_value = LLMResponse(
            content="This is not JSON",
            tool_calls=[],
            finish_reason="stop"
        )
        
        plan = task_executor.plan_task("Create a file")
        
        assert plan is None
    
    def test_execute_step_create_file(self, task_executor, mock_code_agent):
        """Test executing create_file step."""
        step = ExecutionStep(
            action="create_file",
            parameters={"file_path": "test.py", "content": "# test"},
            rationale="Create test file"
        )
        
        mock_code_agent.create_code.return_value = OperationResult(
            success=True,
            message="File created"
        )
        
        result = task_executor.execute_step(step)
        
        assert result.success
        assert result.message == "File created"
        mock_code_agent.create_code.assert_called_once()
        
        # Verify execution history
        assert len(task_executor.execution_history) == 1
        assert task_executor.execution_history[0]["action"] == "create_file"
        
        # Verify file tracking
        assert "test.py" in task_executor.files_modified
    
    def test_execute_step_edit_file(self, task_executor, mock_code_agent):
        """Test executing edit_file step."""
        step = ExecutionStep(
            action="edit_file",
            parameters={
                "file_path": "test.py",
                "new_content": "# updated"
            },
            rationale="Update file"
        )
        
        mock_code_agent.edit_code.return_value = OperationResult(
            success=True,
            message="File updated"
        )
        
        result = task_executor.execute_step(step)
        
        assert result.success
        mock_code_agent.edit_code.assert_called_once()
        assert "test.py" in task_executor.files_modified
    
    def test_execute_step_read_file(self, task_executor, mock_code_agent):
        """Test executing read_file step."""
        step = ExecutionStep(
            action="read_file",
            parameters={"file_path": "test.py"},
            rationale="Read file"
        )
        
        mock_code_agent.file_ops.read_file.return_value = (
            "# content",
            OperationResult(success=True, message="File read")
        )
        
        result = task_executor.execute_step(step)
        
        assert result.success
        assert result.data["content"] == "# content"
        mock_code_agent.file_ops.read_file.assert_called_once_with("test.py")
    
    def test_execute_step_search_code(self, task_executor, mock_code_agent):
        """Test executing search_code step."""
        step = ExecutionStep(
            action="search_code",
            parameters={"pattern": "def test", "file_pattern": "*.py"},
            rationale="Search for test functions"
        )
        
        mock_code_agent.code_search.search_text.return_value = [
            {"file_path": "test.py", "line_number": 1, "match_text": "def test()"}
        ]
        
        result = task_executor.execute_step(step)
        
        assert result.success
        assert result.data["count"] == 1
        mock_code_agent.code_search.search_text.assert_called_once_with("def test", "*.py")
    
    def test_execute_step_run_command(self, task_executor, mock_code_agent):
        """Test executing run_command step."""
        step = ExecutionStep(
            action="run_command",
            parameters={"command": "pytest", "cwd": "/project", "timeout": 30},
            rationale="Run tests"
        )
        
        mock_result = Mock()
        mock_result.return_code = 0
        mock_result.stdout = "All tests passed"
        mock_result.stderr = ""
        
        mock_code_agent.command_executor.execute.return_value = mock_result
        
        result = task_executor.execute_step(step)
        
        assert result.success
        assert result.data["return_code"] == 0
        mock_code_agent.command_executor.execute.assert_called_once_with("pytest", "/project", 30)
        
        # Verify test tracking
        assert "pytest" in task_executor.test_results
        assert task_executor.test_results["pytest"] is True
    
    def test_execute_step_run_command_failure(self, task_executor, mock_code_agent):
        """Test executing run_command step with command failure."""
        step = ExecutionStep(
            action="run_command",
            parameters={"command": "pytest"},
            rationale="Run tests"
        )
        
        mock_result = Mock()
        mock_result.return_code = 1
        mock_result.stdout = ""
        mock_result.stderr = "Test failed"
        
        mock_code_agent.command_executor.execute.return_value = mock_result
        
        result = task_executor.execute_step(step)
        
        assert not result.success
        assert result.data["return_code"] == 1
        assert task_executor.test_results["pytest"] is False
    
    def test_execute_step_analyze_code(self, task_executor, mock_context_manager):
        """Test executing analyze_code step."""
        step = ExecutionStep(
            action="analyze_code",
            parameters={"file_path": "test.py"},
            rationale="Analyze file"
        )
        
        mock_analysis = Mock()
        mock_analysis.language = "python"
        mock_analysis.symbols = []
        mock_analysis.imports = []
        mock_analysis.dependencies = []
        
        mock_context_manager.analyze_code.return_value = mock_analysis
        
        result = task_executor.execute_step(step)
        
        assert result.success
        assert result.data["language"] == "python"
        mock_context_manager.analyze_code.assert_called_once_with("test.py")
    
    def test_execute_step_unknown_action(self, task_executor):
        """Test executing step with unknown action."""
        step = ExecutionStep(
            action="unknown_action",
            parameters={},
            rationale="Test unknown"
        )
        
        result = task_executor.execute_step(step)
        
        assert not result.success
        assert "Unknown action" in result.message
    
    def test_execute_step_missing_parameters(self, task_executor):
        """Test executing step with missing required parameters."""
        step = ExecutionStep(
            action="create_file",
            parameters={},  # Missing file_path
            rationale="Test"
        )
        
        result = task_executor.execute_step(step)
        
        assert not result.success
        assert "Missing required parameter" in result.message
    
    def test_should_continue_no_results(self, task_executor):
        """Test should_continue with no results."""
        assert not task_executor.should_continue([])
    
    def test_should_continue_tests_passing(self, task_executor):
        """Test should_continue when tests are passing."""
        task_executor.test_results = {"test1": True, "test2": True}
        
        results = [
            {"result": {"success": True}},
            {"result": {"success": True}},
            {"result": {"success": True}}
        ]
        
        assert task_executor.should_continue(results)
    
    def test_should_continue_tests_failing(self, task_executor):
        """Test should_continue when tests are failing."""
        task_executor.test_results = {"test1": True, "test2": False}
        
        results = [
            {"result": {"success": True}},
            {"result": {"success": True}},
            {"result": {"success": True}}
        ]
        
        assert not task_executor.should_continue(results)
    
    def test_should_continue_many_successful_steps(self, task_executor):
        """Test should_continue with many successful steps."""
        results = [
            {"result": {"success": True}},
            {"result": {"success": True}},
            {"result": {"success": True}},
            {"result": {"success": True}},
            {"result": {"success": True}}
        ]
        
        assert task_executor.should_continue(results)
    
    def test_should_continue_recent_failures(self, task_executor):
        """Test should_continue with recent failures."""
        results = [
            {"result": {"success": True}},
            {"result": {"success": True}},
            {"result": {"success": False}}
        ]
        
        assert not task_executor.should_continue(results)
    
    def test_execute_task_simple_success(self, task_executor, mock_llm, mock_code_agent):
        """Test complete task execution with simple successful workflow."""
        # Mock planning
        plan_json = {
            "steps": [
                {
                    "action": "create_file",
                    "parameters": {"file_path": "test.py", "content": "pass"},
                    "rationale": "Create file"
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["file_ops"]
        }
        
        mock_llm.generate.return_value = LLMResponse(
            content=json.dumps(plan_json),
            tool_calls=[]
        )
        
        # Mock step execution
        mock_code_agent.create_code.return_value = OperationResult(
            success=True,
            message="File created"
        )
        
        # Mock should_continue to return True (complete)
        with patch.object(task_executor, 'should_continue', return_value=True):
            result = task_executor.execute_task("Create a test file")
        
        assert result.success
        assert len(result.actions_taken) == 1
        assert "test.py" in result.files_modified
        assert len(result.execution_log) == 1
    
    def test_execute_task_planning_failure(self, task_executor, mock_llm):
        """Test task execution when planning fails."""
        mock_llm.generate.return_value = LLMResponse(
            content="",  # Empty response
            tool_calls=[]
        )
        
        result = task_executor.execute_task("Create a file")
        
        assert not result.success
        assert "Failed to generate execution plan" in result.error_message
    
    def test_execute_task_llm_error(self, task_executor, mock_llm):
        """Test task execution handles LLM errors."""
        mock_llm.generate.side_effect = ModelUnavailableError("Model not found")
        
        result = task_executor.execute_task("Create a file")
        
        assert not result.success
        # The error is caught during planning, so error message is about planning failure
        assert "Failed to generate execution plan" in result.error_message
    
    def test_execute_task_max_iterations(self, task_executor, mock_llm, mock_code_agent):
        """Test task execution respects max iterations."""
        # Mock planning
        plan_json = {
            "steps": [
                {
                    "action": "create_file",
                    "parameters": {"file_path": "test.py", "content": "pass"},
                    "rationale": "Create file"
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["file_ops"]
        }
        
        # Mock reflection to return valid next action
        next_action_json = {
            "action": "create_file",
            "parameters": {"file_path": "test2.py", "content": "pass"},
            "rationale": "Continue work"
        }
        
        mock_llm.generate.side_effect = [
            # First call: planning
            LLMResponse(content=json.dumps(plan_json), tool_calls=[]),
            # Subsequent calls: reflection returning next actions
            LLMResponse(content=json.dumps(next_action_json), tool_calls=[]),
            LLMResponse(content=json.dumps(next_action_json), tool_calls=[]),
            LLMResponse(content=json.dumps(next_action_json), tool_calls=[]),
        ]
        
        # Mock step execution
        mock_code_agent.create_code.return_value = OperationResult(
            success=True,
            message="File created"
        )
        
        # Mock should_continue to always return False (never complete)
        with patch.object(task_executor, 'should_continue', return_value=False):
            with patch.object(task_executor, 'MAX_ITERATIONS', 3):
                result = task_executor.execute_task("Create a file")
        
        assert not result.success
        assert "did not complete within" in result.error_message
        assert task_executor.current_iteration == 3
    
    def test_execution_history_tracking(self, task_executor, mock_code_agent):
        """Test that execution history is properly tracked."""
        step1 = ExecutionStep(
            action="create_file",
            parameters={"file_path": "test1.py", "content": "pass"},
            rationale="Create first file"
        )
        
        step2 = ExecutionStep(
            action="create_file",
            parameters={"file_path": "test2.py", "content": "pass"},
            rationale="Create second file"
        )
        
        mock_code_agent.create_code.return_value = OperationResult(
            success=True,
            message="File created"
        )
        
        task_executor.execute_step(step1)
        task_executor.execute_step(step2)
        
        assert len(task_executor.execution_history) == 2
        assert task_executor.execution_history[0]["action"] == "create_file"
        assert task_executor.execution_history[1]["action"] == "create_file"
        assert len(task_executor.files_modified) == 2
    
    def test_state_reset_on_execute_task(self, task_executor, mock_llm, mock_code_agent):
        """Test that state is reset when starting new task."""
        # Set some initial state
        task_executor.execution_history = [{"test": "data"}]
        task_executor.files_modified = ["old_file.py"]
        task_executor.test_results = {"old_test": True}
        task_executor.current_iteration = 5
        
        # Mock planning to fail immediately (to avoid full execution)
        mock_llm.generate.return_value = LLMResponse(content="", tool_calls=[])
        
        task_executor.execute_task("New task")
        
        # Verify state was reset (even though task failed)
        assert len(task_executor.execution_history) == 0
        assert len(task_executor.files_modified) == 0
        assert len(task_executor.test_results) == 0
        assert task_executor.current_iteration == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
