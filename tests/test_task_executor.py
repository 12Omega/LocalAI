"""Integration tests for TaskExecutor.

These tests verify the complete agent loop functionality including:
- Task planning and execution
- Agent loop iterations
- Error recovery and retry logic
- Context window management
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import tempfile
import os

from src.core.task_executor import TaskExecutor
from src.core.models import (
    LLMConfig,
    SystemConfig,
    LLMResponse,
    ToolCall,
    ExecutionPlan,
    ExecutionStep,
    TaskResult
)
from src.core.llm_interface import LocalLLMInterface, LLMError
from src.agents.code_agent import CodeAgent
from src.context.context_manager import ContextManager


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create basic project structure
        project_root = Path(tmpdir) / "test_project"
        project_root.mkdir()
        
        # Create a simple Python file
        (project_root / "main.py").write_text("print('Hello, world!')\n")
        
        yield str(project_root)


@pytest.fixture
def mock_llm_interface():
    """Create a mock LLM interface."""
    mock = Mock(spec=LocalLLMInterface)
    
    # Default response
    mock.generate.return_value = LLMResponse(
        content="Task analysis complete",
        tool_calls=[],
        finish_reason="stop"
    )
    
    return mock


@pytest.fixture
def code_agent(temp_project_dir):
    """Create a real CodeAgent for testing."""
    return CodeAgent(project_root=temp_project_dir)


@pytest.fixture
def context_manager(temp_project_dir):
    """Create a real ContextManager for testing."""
    config = SystemConfig(
        llm=LLMConfig(
            endpoint="http://localhost:11434",
            model_name="test-model"
        ),
        project_root=temp_project_dir
    )
    return ContextManager(config)


@pytest.fixture
def task_executor(mock_llm_interface, code_agent, context_manager):
    """Create TaskExecutor with mocked LLM but real agents."""
    return TaskExecutor(
        llm_interface=mock_llm_interface,
        code_agent=code_agent,
        context_manager=context_manager
    )


class TestTaskExecutorBasics:
    """Test basic TaskExecutor functionality."""
    
    def test_initialization(self, task_executor):
        """Test TaskExecutor initializes correctly."""
        assert task_executor.llm is not None
        assert task_executor.code_agent is not None
        assert task_executor.context_manager is not None
        assert task_executor.execution_history == []
        assert task_executor.modified_files == []
        assert task_executor.test_results == {}
        assert task_executor.iteration_count == 0
    
    def test_available_tools_defined(self, task_executor):
        """Test that all required tools are defined."""
        tool_names = [tool.name for tool in TaskExecutor.AVAILABLE_TOOLS]
        
        # Check essential tools are present
        assert "create_file" in tool_names
        assert "edit_file" in tool_names
        assert "read_file" in tool_names
        assert "run_command" in tool_names
        assert "search_code" in tool_names
        assert "get_relevant_files" in tool_names
        assert "analyze_file" in tool_names
        assert "task_complete" in tool_names
        assert "report_blocker" in tool_names


class TestTaskPlanning:
    """Test task planning functionality."""
    
    def test_plan_task_with_tool_calls(self, task_executor, mock_llm_interface):
        """Test planning when LLM returns tool calls."""
        # Mock LLM to return tool calls
        mock_llm_interface.generate.return_value = LLMResponse(
            content="I'll create a test file",
            tool_calls=[
                ToolCall(
                    name="create_file",
                    arguments={
                        "file_path": "test.py",
                        "content": "# Test file\n",
                        "task_description": "Create test file"
                    }
                ),
                ToolCall(
                    name="task_complete",
                    arguments={
                        "summary": "Created test file",
                        "files_modified": ["test.py"],
                        "tests_passed": True
                    }
                )
            ],
            finish_reason="tool_calls"
        )
        
        plan = task_executor.plan_task("Create a test file")
        
        assert isinstance(plan, ExecutionPlan)
        assert len(plan.steps) == 2
        assert plan.steps[0].action == "create_file"
        assert plan.steps[1].action == "task_complete"
        assert plan.estimated_complexity in ["simple", "moderate", "complex"]
        assert "create_file" in plan.required_tools
    
    def test_plan_task_without_tool_calls(self, task_executor, mock_llm_interface):
        """Test planning when LLM doesn't use tool calls (fallback)."""
        # Mock LLM to return only text
        mock_llm_interface.generate.return_value = LLMResponse(
            content="I need to analyze the project first",
            tool_calls=[],
            finish_reason="stop"
        )
        
        plan = task_executor.plan_task("Refactor code")
        
        assert isinstance(plan, ExecutionPlan)
        assert len(plan.steps) >= 1  # Should have fallback step
        # Fallback creates get_relevant_files step
        assert plan.steps[0].action == "get_relevant_files"
    
    def test_plan_complexity_estimation(self, task_executor, mock_llm_interface):
        """Test that complexity is estimated based on number of steps."""
        # Test simple task (1-3 steps)
        mock_llm_interface.generate.return_value = LLMResponse(
            content="Simple task",
            tool_calls=[
                ToolCall(name="create_file", arguments={
                    "file_path": "test.py",
                    "content": "",
                    "task_description": "test"
                })
            ]
        )
        plan = task_executor.plan_task("Simple task")
        assert plan.estimated_complexity == "simple"
        
        # Test moderate task (4-7 steps)
        mock_llm_interface.generate.return_value = LLMResponse(
            content="Moderate task",
            tool_calls=[
                ToolCall(name="read_file", arguments={"file_path": f"file{i}.py"})
                for i in range(5)
            ]
        )
        plan = task_executor.plan_task("Moderate task")
        assert plan.estimated_complexity == "moderate"
        
        # Test complex task (8+ steps)
        mock_llm_interface.generate.return_value = LLMResponse(
            content="Complex task",
            tool_calls=[
                ToolCall(name="read_file", arguments={"file_path": f"file{i}.py"})
                for i in range(10)
            ]
        )
        plan = task_executor.plan_task("Complex task")
        assert plan.estimated_complexity == "complex"


class TestStepExecution:
    """Test individual step execution."""
    
    def test_execute_create_file_step(self, task_executor, temp_project_dir):
        """Test executing create_file step."""
        step = ExecutionStep(
            action="create_file",
            parameters={
                "file_path": "new_file.py",
                "content": "# New file\ndef hello():\n    print('Hello')\n",
                "task_description": "Create new file"
            },
            rationale="Creating a new file for testing"
        )
        
        result = task_executor.execute_step(step)
        
        assert result['success'] is True
        assert result['file_path'] == "new_file.py"
        assert "new_file.py" in task_executor.modified_files
        
        # Verify file was actually created
        file_path = Path(temp_project_dir) / "new_file.py"
        assert file_path.exists()
    
    def test_execute_read_file_step(self, task_executor, temp_project_dir):
        """Test executing read_file step."""
        step = ExecutionStep(
            action="read_file",
            parameters={"file_path": "main.py"},
            rationale="Reading existing file"
        )
        
        result = task_executor.execute_step(step)
        
        assert result['success'] is True
        assert result['content'] is not None
        assert "Hello, world!" in result['content']
    
    def test_execute_edit_file_step(self, task_executor, temp_project_dir):
        """Test executing edit_file step."""
        step = ExecutionStep(
            action="edit_file",
            parameters={
                "file_path": "main.py",
                "new_content": "print('Modified!')\n",
                "modification_request": "Update print statement"
            },
            rationale="Editing file"
        )
        
        result = task_executor.execute_step(step)
        
        assert result['success'] is True
        assert "main.py" in task_executor.modified_files
        
        # Verify file was actually modified
        file_path = Path(temp_project_dir) / "main.py"
        assert file_path.read_text() == "print('Modified!')\n"
    
    def test_execute_run_command_step(self, task_executor):
        """Test executing run_command step."""
        step = ExecutionStep(
            action="run_command",
            parameters={
                "command": "echo 'test output'",
                "working_directory": task_executor.code_agent.project_root
            },
            rationale="Running test command"
        )
        
        result = task_executor.execute_step(step)
        
        assert result['success'] is True
        assert result['exit_code'] == 0
        assert 'test output' in result['stdout']
    
    def test_execute_run_command_tracks_tests(self, task_executor):
        """Test that test commands are tracked in test_results."""
        step = ExecutionStep(
            action="run_command",
            parameters={
                "command": "pytest tests/",
                "working_directory": task_executor.code_agent.project_root
            },
            rationale="Running tests"
        )
        
        # Execute step (will fail since pytest might not find tests, but that's ok)
        result = task_executor.execute_step(step)
        
        # Check that test result was tracked
        assert len(task_executor.test_results) > 0
    
    def test_execute_search_code_step(self, task_executor):
        """Test executing search_code step."""
        step = ExecutionStep(
            action="search_code",
            parameters={
                "query": "print",
                "file_pattern": "*.py"
            },
            rationale="Searching for print statements"
        )
        
        result = task_executor.execute_step(step)
        
        assert result['success'] is True
        assert 'results' in result
        assert 'count' in result
    
    def test_execute_get_relevant_files_step(self, task_executor):
        """Test executing get_relevant_files step."""
        step = ExecutionStep(
            action="get_relevant_files",
            parameters={
                "task_description": "Modify main functionality"
            },
            rationale="Finding relevant files"
        )
        
        result = task_executor.execute_step(step)
        
        assert result['success'] is True
        assert 'files' in result
        assert 'count' in result
    
    def test_execute_analyze_file_step(self, task_executor, temp_project_dir):
        """Test executing analyze_file step."""
        # Create a Python file with some content
        test_file = Path(temp_project_dir) / "test_analysis.py"
        test_file.write_text("""
def my_function():
    pass

class MyClass:
    def method(self):
        pass
""")
        
        step = ExecutionStep(
            action="analyze_file",
            parameters={
                "file_path": str(test_file)
            },
            rationale="Analyzing file structure"
        )
        
        result = task_executor.execute_step(step)
        
        assert result['success'] is True
        assert result['language'] == 'python'
        assert 'symbols' in result
    
    def test_execute_task_complete_step(self, task_executor):
        """Test executing task_complete step."""
        step = ExecutionStep(
            action="task_complete",
            parameters={
                "summary": "All tasks completed successfully",
                "files_modified": ["file1.py", "file2.py"],
                "tests_passed": True
            },
            rationale="Marking task as complete"
        )
        
        result = task_executor.execute_step(step)
        
        assert result['success'] is True
        assert result['complete'] is True
        assert result['summary'] == "All tasks completed successfully"
    
    def test_execute_report_blocker_step(self, task_executor):
        """Test executing report_blocker step."""
        step = ExecutionStep(
            action="report_blocker",
            parameters={
                "blocker_description": "Cannot access external API",
                "attempted_solutions": ["Tried different endpoint", "Checked credentials"]
            },
            rationale="Reporting blocker"
        )
        
        result = task_executor.execute_step(step)
        
        assert result['success'] is False
        assert result['blocked'] is True
        assert result['blocker_description'] == "Cannot access external API"
    
    def test_execute_unknown_action(self, task_executor):
        """Test executing unknown action returns error."""
        step = ExecutionStep(
            action="unknown_action",
            parameters={},
            rationale="Testing unknown action"
        )
        
        result = task_executor.execute_step(step)
        
        assert result['success'] is False
        assert 'error' in result


class TestAgentLoop:
    """Test complete agent loop execution."""
    
    def test_complete_task_execution_success(self, task_executor, mock_llm_interface):
        """Test successful complete task execution through agent loop."""
        # Setup mock LLM responses for the agent loop
        responses = [
            # Initial planning
            LLMResponse(
                content="Creating test file",
                tool_calls=[
                    ToolCall(
                        name="create_file",
                        arguments={
                            "file_path": "test_output.py",
                            "content": "# Test\nprint('test')\n",
                            "task_description": "Create test file"
                        }
                    )
                ],
                finish_reason="tool_calls"
            ),
            # Reflection - mark complete
            LLMResponse(
                content="Task complete",
                tool_calls=[
                    ToolCall(
                        name="task_complete",
                        arguments={
                            "summary": "Created test file successfully",
                            "files_modified": ["test_output.py"],
                            "tests_passed": True
                        }
                    )
                ],
                finish_reason="tool_calls"
            )
        ]
        
        mock_llm_interface.generate.side_effect = responses
        
        result = task_executor.execute_task("Create a test file")
        
        assert result.success is True
        assert len(result.files_modified) > 0
        assert len(result.actions_taken) > 0
        assert result.error_message is None
    
    def test_task_execution_with_iterations(self, task_executor, mock_llm_interface):
        """Test task execution that requires multiple iterations."""
        responses = [
            # Initial planning
            LLMResponse(
                content="Step 1",
                tool_calls=[
                    ToolCall(
                        name="create_file",
                        arguments={
                            "file_path": "step1.py",
                            "content": "# Step 1\n",
                            "task_description": "Step 1"
                        }
                    )
                ],
                finish_reason="tool_calls"
            ),
            # Reflection - continue
            LLMResponse(
                content="Need step 2",
                tool_calls=[
                    ToolCall(
                        name="create_file",
                        arguments={
                            "file_path": "step2.py",
                            "content": "# Step 2\n",
                            "task_description": "Step 2"
                        }
                    )
                ],
                finish_reason="tool_calls"
            ),
            # Reflection - complete
            LLMResponse(
                content="Done",
                tool_calls=[
                    ToolCall(
                        name="task_complete",
                        arguments={
                            "summary": "Completed both steps",
                            "files_modified": ["step1.py", "step2.py"],
                            "tests_passed": True
                        }
                    )
                ],
                finish_reason="tool_calls"
            )
        ]
        
        mock_llm_interface.generate.side_effect = responses
        
        result = task_executor.execute_task("Create two files")
        
        assert result.success is True
        assert task_executor.iteration_count >= 2
        assert len(result.files_modified) >= 2
    
    def test_task_execution_with_blocker(self, task_executor, mock_llm_interface):
        """Test task execution that reports a blocker."""
        # Setup mock to directly report blocker in planning phase
        mock_llm_interface.generate.return_value = LLMResponse(
            content="Cannot proceed",
            tool_calls=[
                ToolCall(
                    name="report_blocker",
                    arguments={
                        "blocker_description": "Required command not available",
                        "attempted_solutions": ["Tried to run command", "Checked PATH"]
                    }
                )
            ],
            finish_reason="tool_calls"
        )
        
        result = task_executor.execute_task("Run unavailable command")
        
        # The task completes (doesn't hang), with blocker reported
        assert len(result.actions_taken) > 0
        blocker_reported = any(
            step.action == "report_blocker" 
            for step in result.actions_taken
        )
        assert blocker_reported, "Blocker should have been reported in execution"
    
    def test_task_execution_max_iterations(self, task_executor, mock_llm_interface):
        """Test that task execution respects max iterations limit."""
        # Create infinite loop of steps
        mock_llm_interface.generate.return_value = LLMResponse(
            content="Keep going",
            tool_calls=[
                ToolCall(
                    name="read_file",
                    arguments={"file_path": "main.py"}
                )
            ],
            finish_reason="tool_calls"
        )
        
        # Set a low max for testing
        original_max = TaskExecutor.MAX_ITERATIONS
        TaskExecutor.MAX_ITERATIONS = 5
        
        try:
            result = task_executor.execute_task("Infinite task")
            
            assert result.success is False
            assert task_executor.iteration_count == TaskExecutor.MAX_ITERATIONS
            assert "maximum iterations" in result.error_message.lower()
        finally:
            TaskExecutor.MAX_ITERATIONS = original_max


class TestReflection:
    """Test reflection and decision making."""
    
    def test_should_continue_on_task_complete(self, task_executor, mock_llm_interface):
        """Test that should_continue detects task completion."""
        # Create execution history with task_complete step
        history = [
            {
                'iteration': 1,
                'step': ExecutionStep(
                    action="task_complete",
                    parameters={
                        "summary": "Done",
                        "files_modified": [],
                        "tests_passed": True
                    },
                    rationale="Task complete"
                ),
                'result': {'success': True, 'complete': True}
            }
        ]
        
        is_complete, next_plan = task_executor.should_continue(history)
        
        assert is_complete is True
        assert next_plan is None
    
    def test_should_continue_on_blocker(self, task_executor, mock_llm_interface):
        """Test that should_continue detects blockers."""
        history = [
            {
                'iteration': 1,
                'step': ExecutionStep(
                    action="report_blocker",
                    parameters={
                        "blocker_description": "Stuck",
                        "attempted_solutions": []
                    },
                    rationale="Reporting blocker"
                ),
                'result': {'success': False, 'blocked': True}
            }
        ]
        
        is_complete, next_plan = task_executor.should_continue(history)
        
        assert is_complete is True
        assert next_plan is None
    
    def test_should_continue_generates_next_plan(self, task_executor, mock_llm_interface):
        """Test that should_continue generates next plan when not complete."""
        # Mock LLM to return next steps
        mock_llm_interface.generate.return_value = LLMResponse(
            content="Continue working",
            tool_calls=[
                ToolCall(
                    name="edit_file",
                    arguments={
                        "file_path": "main.py",
                        "new_content": "# Updated\n",
                        "modification_request": "Update"
                    }
                )
            ],
            finish_reason="tool_calls"
        )
        
        history = [
            {
                'iteration': 1,
                'step': ExecutionStep(
                    action="create_file",
                    parameters={
                        "file_path": "test.py",
                        "content": "",
                        "task_description": "Test"
                    },
                    rationale="Creating file"
                ),
                'result': {'success': True}
            }
        ]
        
        is_complete, next_plan = task_executor.should_continue(history)
        
        assert is_complete is False
        assert next_plan is not None
        assert isinstance(next_plan, ExecutionPlan)
        assert len(next_plan.steps) > 0


class TestContextManagement:
    """Test context window management."""
    
    def test_execution_history_summarization_short(self, task_executor):
        """Test that short history is not summarized."""
        history = [
            {
                'iteration': i,
                'step': ExecutionStep(
                    action="read_file",
                    parameters={"file_path": f"file{i}.py"},
                    rationale=f"Reading file {i}"
                ),
                'result': {'success': True}
            }
            for i in range(5)
        ]
        
        summary = task_executor._summarize_execution_history(history)
        
        # Short history should include all details
        assert len(summary.split('\n')) >= 5
        for i in range(5):
            assert f"file{i}.py" in summary or f"Reading file {i}" in summary
    
    def test_execution_history_summarization_long(self, task_executor):
        """Test that long history is summarized."""
        history = [
            {
                'iteration': i,
                'step': ExecutionStep(
                    action="read_file",
                    parameters={"file_path": f"file{i}.py"},
                    rationale=f"Reading file {i}"
                ),
                'result': {'success': True}
            }
            for i in range(20)
        ]
        
        summary = task_executor._summarize_execution_history(history)
        
        # Long history should be summarized
        assert "Earlier actions" in summary
        assert "Recent actions" in summary


class TestErrorHandling:
    """Test error handling and recovery."""
    
    def test_llm_error_handling(self, task_executor, mock_llm_interface):
        """Test that LLM errors are handled gracefully."""
        mock_llm_interface.generate.side_effect = LLMError("Connection failed")
        
        result = task_executor.execute_task("Test task")
        
        assert result.success is False
        assert "LLM error" in result.error_message
    
    def test_step_execution_error_handling(self, task_executor, mock_llm_interface):
        """Test that step execution errors are captured."""
        # Mock LLM to return a step that will fail
        mock_llm_interface.generate.return_value = LLMResponse(
            content="Testing",
            tool_calls=[
                ToolCall(
                    name="read_file",
                    arguments={"file_path": "/nonexistent/file.py"}
                )
            ],
            finish_reason="tool_calls"
        )
        
        # Create a minimal execution to test error handling
        step = ExecutionStep(
            action="read_file",
            parameters={"file_path": "/nonexistent/file.py"},
            rationale="Test"
        )
        
        result = task_executor.execute_step(step)
        
        # Should handle error gracefully
        assert result['success'] is False
        assert 'error' in result or 'message' in result


class TestProgressTracking:
    """Test progress tracking and logging."""
    
    def test_progress_updates_during_execution(self, task_executor, mock_llm_interface, caplog):
        """Test that progress updates are logged during execution."""
        import logging
        caplog.set_level(logging.INFO)
        
        # Setup simple task
        mock_llm_interface.generate.side_effect = [
            LLMResponse(
                content="Working",
                tool_calls=[
                    ToolCall(
                        name="create_file",
                        arguments={
                            "file_path": "test.py",
                            "content": "# Test\n",
                            "task_description": "Test"
                        }
                    )
                ]
            ),
            LLMResponse(
                content="Done",
                tool_calls=[
                    ToolCall(
                        name="task_complete",
                        arguments={
                            "summary": "Done",
                            "files_modified": ["test.py"],
                            "tests_passed": True
                        }
                    )
                ]
            )
        ]
        
        task_executor.execute_task("Create test file")
        
        # Check that progress was logged
        progress_logs = [record for record in caplog.records if "PROGRESS" in record.message]
        assert len(progress_logs) > 0
    
    def test_completion_summary(self, task_executor, mock_llm_interface):
        """Test that completion summary is provided."""
        mock_llm_interface.generate.side_effect = [
            LLMResponse(
                content="Done",
                tool_calls=[
                    ToolCall(
                        name="task_complete",
                        arguments={
                            "summary": "Task completed successfully with all tests passing",
                            "files_modified": ["file1.py", "file2.py"],
                            "tests_passed": True
                        }
                    )
                ]
            )
        ]
        
        result = task_executor.execute_task("Test task")
        
        assert result.success is True
        assert len(result.execution_log) > 0
        # Check that summary includes key information
        log_text = '\n'.join(result.execution_log)
        assert "Test task" in log_text
