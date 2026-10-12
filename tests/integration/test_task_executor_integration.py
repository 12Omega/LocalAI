"""Integration tests for TaskExecutor.

These tests verify the complete task execution workflow including:
- Complete task execution with mock LLM responses
- Agent loop iterations with multiple reflection cycles
- Error recovery and retry logic
- Context window management with long task histories

Requirements validated:
- 7.1: Plan steps needed to complete development tasks
- 7.2: Coordinate all system components to execute the plan
- 7.3: Write tests for new functionality
- 7.4: Run tests to verify correctness
- 7.5: Debug and fix issues when tests fail
- 7.6: Refactor code when necessary
- 7.7: Provide summary of changes made when task is complete
- 7.8: Report specific blockers if task cannot be completed
- 15.1: Provide progress updates while executing tasks
- 15.5: Provide task completion summaries
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime

from src.core.task_executor import TaskExecutor
from src.core.models import (
    ExecutionPlan,
    ExecutionStep,
    TaskResult,
    LLMResponse,
    ToolCall,
    LLMConfig,
    SystemConfig
)
from src.core.llm_interface import (
    LocalLLMInterface,
    LLMError,
    ModelUnavailableError,
    LLMTimeoutError,
    InvalidResponseError
)
from src.agents.code_agent import CodeAgent
from src.agents.file_operations import FileOperations, OperationResult
from src.context.context_manager import ContextManager


class TestCompleteTaskExecution:
    """Test complete task execution workflows with mock LLM responses."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory."""
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM interface."""
        llm = Mock(spec=LocalLLMInterface)
        return llm
    
    @pytest.fixture
    def code_agent(self, temp_project_dir):
        """Create real CodeAgent for testing."""
        return CodeAgent(project_root=temp_project_dir)
    
    @pytest.fixture
    def context_manager(self, temp_project_dir):
        """Create real ContextManager for testing."""
        config = SystemConfig(
            llm=LLMConfig(endpoint="http://localhost:11434", model_name="test-model"),
            project_root=temp_project_dir
        )
        return ContextManager(config)
    
    @pytest.fixture
    def task_executor(self, mock_llm, code_agent, context_manager):
        """Create TaskExecutor with mocked LLM."""
        return TaskExecutor(
            llm_interface=mock_llm,
            code_agent=code_agent,
            context_manager=context_manager
        )
    
    def test_simple_file_creation_workflow(self, task_executor, mock_llm, temp_project_dir):
        """Test complete workflow for simple file creation task.
        
        Validates: Requirements 7.1, 7.2, 7.7
        """
        # Mock LLM to return execution plan
        plan_json = {
            "steps": [
                {
                    "action": "create_file",
                    "parameters": {
                        "file_path": "hello.py",
                        "content": "def hello():\n    print('Hello, World!')\n"
                    },
                    "rationale": "Create hello function"
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["file_ops"]
        }
        
        # Mock reflection to mark task complete
        next_action_json = {
            "action": "complete",
            "parameters": {"summary": "File created successfully"},
            "rationale": "Task is complete"
        }
        
        mock_llm.generate.side_effect = [
            # Planning call
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            # Reflection call
            LLMResponse(content=json.dumps(next_action_json), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute task
        result = task_executor.execute_task("Create a hello.py file with a hello function")
        
        # Verify result
        assert result.success
        assert len(result.files_modified) == 1
        assert "hello.py" in result.files_modified
        assert len(result.actions_taken) == 1
        assert result.actions_taken[0].action == "create_file"
        assert not result.error_message
        
        # Verify file was actually created
        file_path = Path(temp_project_dir) / "hello.py"
        assert file_path.exists()
        content = file_path.read_text()
        assert "def hello()" in content
    
    def test_multi_step_workflow_with_testing(self, task_executor, mock_llm, temp_project_dir):
        """Test workflow with multiple steps including test creation and execution.
        
        Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.7
        """
        # Mock planning
        plan_json = {
            "steps": [
                {
                    "action": "create_file",
                    "parameters": {
                        "file_path": "calculator.py",
                        "content": "def add(a, b):\n    return a + b\n"
                    },
                    "rationale": "Create calculator module"
                },
                {
                    "action": "create_file",
                    "parameters": {
                        "file_path": "test_calculator.py",
                        "content": "from calculator import add\n\ndef test_add():\n    assert add(2, 3) == 5\n"
                    },
                    "rationale": "Create tests"
                },
                {
                    "action": "run_command",
                    "parameters": {
                        "command": "python -m pytest test_calculator.py -v",
                        "cwd": temp_project_dir
                    },
                    "rationale": "Run tests"
                }
            ],
            "estimated_complexity": "moderate",
            "required_tools": ["file_ops", "command_executor"]
        }
        
        # Mock reflection to mark complete after initial steps
        next_action_json = {
            "action": "complete",
            "parameters": {"summary": "Module and tests created, tests passing"},
            "rationale": "All steps completed successfully"
        }
        
        mock_llm.generate.side_effect = [
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(next_action_json), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute task
        result = task_executor.execute_task("Create calculator module with add function and tests")
        
        # Verify result
        assert result.success
        assert len(result.files_modified) == 2
        assert "calculator.py" in result.files_modified
        assert "test_calculator.py" in result.files_modified
        assert len(result.actions_taken) == 3
        
        # Verify test results tracked
        assert len(task_executor.test_results) > 0
        
        # Verify files created
        calc_file = Path(temp_project_dir) / "calculator.py"
        test_file = Path(temp_project_dir) / "test_calculator.py"
        assert calc_file.exists()
        assert test_file.exists()
    
    def test_edit_existing_file_workflow(self, task_executor, mock_llm, temp_project_dir):
        """Test workflow that edits existing files.
        
        Validates: Requirements 7.2, 7.6, 7.7
        """
        # Create existing file
        existing_file = Path(temp_project_dir) / "app.py"
        existing_file.write_text("def old_function():\n    pass\n")
        
        # Mock planning
        plan_json = {
            "steps": [
                {
                    "action": "read_file",
                    "parameters": {"file_path": "app.py"},
                    "rationale": "Read existing code"
                },
                {
                    "action": "edit_file",
                    "parameters": {
                        "file_path": "app.py",
                        "new_content": "def old_function():\n    pass\n\ndef new_function():\n    return 'new'\n"
                    },
                    "rationale": "Add new function"
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["file_ops"]
        }
        
        next_action_json = {
            "action": "complete",
            "parameters": {"summary": "Added new function to app.py"},
            "rationale": "Task complete"
        }
        
        mock_llm.generate.side_effect = [
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(next_action_json), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute task
        result = task_executor.execute_task("Add new_function to app.py")
        
        # Verify result
        assert result.success
        assert "app.py" in result.files_modified
        
        # Verify file was edited
        content = existing_file.read_text()
        assert "def new_function()" in content
        assert "def old_function()" in content  # Original function preserved


class TestAgentLoopIterations:
    """Test agent loop iterations and reflection cycles."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory."""
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM interface."""
        return Mock(spec=LocalLLMInterface)
    
    @pytest.fixture
    def task_executor(self, mock_llm, temp_project_dir):
        """Create TaskExecutor."""
        code_agent = CodeAgent(project_root=temp_project_dir)
        config = SystemConfig(
            llm=LLMConfig(endpoint="http://localhost:11434", model_name="test-model"),
            project_root=temp_project_dir
        )
        context_manager = ContextManager(config)
        
        return TaskExecutor(
            llm_interface=mock_llm,
            code_agent=code_agent,
            context_manager=context_manager
        )
    
    def test_multi_iteration_workflow(self, task_executor, mock_llm):
        """Test workflow requiring multiple agent loop iterations.
        
        Validates: Requirements 7.1, 7.2, 7.5
        """
        # Mock planning
        plan_json = {
            "steps": [
                {
                    "action": "create_file",
                    "parameters": {
                        "file_path": "step1.py",
                        "content": "# Step 1\n"
                    },
                    "rationale": "Initial file"
                }
            ],
            "estimated_complexity": "moderate",
            "required_tools": ["file_ops"]
        }
        
        # Mock reflection - iteration 2: continue with another step
        iteration2_json = {
            "action": "create_file",
            "parameters": {
                "file_path": "step2.py",
                "content": "# Step 2\n"
            },
            "rationale": "Need another file"
        }
        
        # Mock reflection - iteration 3: continue with test
        iteration3_json = {
            "action": "run_command",
            "parameters": {
                "command": "echo 'tests pass'",
                "cwd": task_executor.code_agent.project_root
            },
            "rationale": "Run tests"
        }
        
        # Mock reflection - iteration 4: complete
        complete_json = {
            "action": "complete",
            "parameters": {"summary": "All steps completed"},
            "rationale": "Done"
        }
        
        mock_llm.generate.side_effect = [
            # Planning
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            # Iteration 2
            LLMResponse(content=json.dumps(iteration2_json), tool_calls=[], finish_reason="stop"),
            # Iteration 3
            LLMResponse(content=json.dumps(iteration3_json), tool_calls=[], finish_reason="stop"),
            # Iteration 4
            LLMResponse(content=json.dumps(complete_json), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute task
        result = task_executor.execute_task("Multi-step task")
        
        # Verify multiple iterations occurred
        assert result.success
        assert task_executor.current_iteration >= 3
        assert len(result.actions_taken) >= 3
        assert len(task_executor.execution_history) >= 3
    
    def test_reflection_uses_execution_history(self, task_executor, mock_llm):
        """Test that reflection considers execution history.
        
        Validates: Requirements 7.5, 7.7
        """
        # Mock planning
        plan_json = {
            "steps": [
                {
                    "action": "create_file",
                    "parameters": {
                        "file_path": "data.txt",
                        "content": "test data"
                    },
                    "rationale": "Create data file"
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["file_ops"]
        }
        
        # Track what prompts were sent to LLM
        prompts_received = []
        
        def capture_prompt(prompt, tools=None):
            prompts_received.append(prompt)
            if len(prompts_received) == 1:
                # Planning response
                return LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop")
            else:
                # Reflection response - complete
                complete_json = {
                    "action": "complete",
                    "parameters": {"summary": "Done"},
                    "rationale": "Task complete"
                }
                return LLMResponse(content=json.dumps(complete_json), tool_calls=[], finish_reason="stop")
        
        mock_llm.generate.side_effect = capture_prompt
        
        # Execute task
        result = task_executor.execute_task("Create data file")
        
        # Verify reflection prompt included history
        assert len(prompts_received) >= 2
        reflection_prompt = prompts_received[1]
        assert "Execution History" in reflection_prompt or "history" in reflection_prompt.lower()
        assert "create_file" in reflection_prompt.lower() or "data.txt" in reflection_prompt.lower()
    
    def test_max_iterations_limit(self, task_executor, mock_llm):
        """Test that agent loop respects maximum iterations limit.
        
        Validates: Requirements 7.8
        """
        # Mock planning with initial step
        plan_json = {
            "steps": [
                {
                    "action": "read_file",
                    "parameters": {"file_path": "nonexistent.py"},
                    "rationale": "Check file"
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["file_ops"]
        }
        
        # Mock reflection to always continue (create infinite loop)
        continue_json = {
            "action": "read_file",
            "parameters": {"file_path": "nonexistent.py"},
            "rationale": "Keep trying"
        }
        
        mock_llm.generate.return_value = LLMResponse(
            content=json.dumps(continue_json),
            tool_calls=[],
            finish_reason="stop"
        )
        
        # First call returns plan
        mock_llm.generate.side_effect = [
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop")
        ] + [LLMResponse(content=json.dumps(continue_json), tool_calls=[], finish_reason="stop")] * 30
        
        # Execute task
        result = task_executor.execute_task("Infinite loop task")
        
        # Verify max iterations reached
        assert task_executor.current_iteration == TaskExecutor.MAX_ITERATIONS
        assert not result.success
        assert "maximum iterations" in result.error_message.lower() or "did not complete" in result.error_message.lower()


class TestErrorRecoveryAndRetry:
    """Test error recovery and retry logic."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory."""
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    @pytest.fixture
    def task_executor(self, temp_project_dir):
        """Create TaskExecutor."""
        mock_llm = Mock(spec=LocalLLMInterface)
        code_agent = CodeAgent(project_root=temp_project_dir)
        config = SystemConfig(
            llm=LLMConfig(endpoint="http://localhost:11434", model_name="test-model"),
            project_root=temp_project_dir
        )
        context_manager = ContextManager(config)
        
        executor = TaskExecutor(
            llm_interface=mock_llm,
            code_agent=code_agent,
            context_manager=context_manager
        )
        executor.llm = mock_llm  # Keep reference for test setup
        return executor
    
    def test_handles_llm_timeout_during_planning(self, task_executor):
        """Test handling of LLM timeout during planning phase.
        
        Validates: Requirements 14.4, 7.8
        """
        # Mock LLM to raise timeout error
        task_executor.llm.generate.side_effect = LLMTimeoutError("Timeout waiting for LLM")
        
        # Execute task
        result = task_executor.execute_task("Test task")
        
        # Verify error handled
        assert not result.success
        assert result.error_message is not None
        assert "failed" in result.error_message.lower() or "error" in result.error_message.lower()
    
    def test_handles_invalid_llm_response(self, task_executor):
        """Test handling of invalid/malformed LLM responses.
        
        Validates: Requirements 14.1, 7.8
        """
        # Mock LLM to return invalid JSON
        task_executor.llm.generate.return_value = LLMResponse(
            content="This is not valid JSON {[}]",
            tool_calls=[],
            finish_reason="stop"
        )
        
        # Execute task
        result = task_executor.execute_task("Test task")
        
        # Verify error handled gracefully
        assert not result.success
        assert result.error_message is not None
    
    def test_continues_after_failed_step(self, task_executor, temp_project_dir):
        """Test that executor continues after a failed step.
        
        Validates: Requirements 7.5, 14.2
        """
        # Mock planning
        plan_json = {
            "steps": [
                {
                    "action": "read_file",
                    "parameters": {"file_path": "/nonexistent/file.py"},
                    "rationale": "Try to read non-existent file"
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["file_ops"]
        }
        
        # Mock reflection to try alternate approach after failure
        retry_json = {
            "action": "create_file",
            "parameters": {
                "file_path": "alternative.py",
                "content": "# Alternative approach\n"
            },
            "rationale": "Try creating file instead"
        }
        
        # Mock final reflection to complete
        complete_json = {
            "action": "complete",
            "parameters": {"summary": "Used alternative approach"},
            "rationale": "Completed with workaround"
        }
        
        task_executor.llm.generate.side_effect = [
            # Planning
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            # Reflection after failure
            LLMResponse(content=json.dumps(retry_json), tool_calls=[], finish_reason="stop"),
            # Final reflection
            LLMResponse(content=json.dumps(complete_json), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute task
        result = task_executor.execute_task("Read or create file")
        
        # Verify task completed despite initial failure
        assert result.success
        assert len(result.actions_taken) >= 2
        
        # Verify alternative file was created
        alt_file = Path(temp_project_dir) / "alternative.py"
        assert alt_file.exists()
    
    def test_handles_command_execution_failure(self, task_executor):
        """Test handling of command execution failures.
        
        Validates: Requirements 14.1, 7.5
        """
        # Mock planning with failing command
        plan_json = {
            "steps": [
                {
                    "action": "run_command",
                    "parameters": {
                        "command": "python -m pytest nonexistent_tests/",
                        "cwd": task_executor.code_agent.project_root
                    },
                    "rationale": "Run tests"
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["command_executor"]
        }
        
        # Mock reflection to recognize failure and report it
        complete_json = {
            "action": "blocked",
            "parameters": {"reason": "Tests not found"},
            "rationale": "Cannot proceed"
        }
        
        task_executor.llm.generate.side_effect = [
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(complete_json), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute task
        result = task_executor.execute_task("Run tests")
        
        # Verify execution attempted and failure recorded
        assert len(result.actions_taken) >= 1
        assert len(task_executor.test_results) > 0
        # Command failures should be tracked as failed tests
        assert False in task_executor.test_results.values()
    
    def test_recovers_from_file_permission_error(self, task_executor, temp_project_dir):
        """Test handling of file permission errors.
        
        Validates: Requirements 14.3
        """
        # Create a read-only file (simulate permission issue)
        readonly_file = Path(temp_project_dir) / "readonly.txt"
        readonly_file.write_text("original content")
        readonly_file.chmod(0o444)  # Read-only
        
        # Mock planning to edit readonly file
        plan_json = {
            "steps": [
                {
                    "action": "edit_file",
                    "parameters": {
                        "file_path": "readonly.txt",
                        "new_content": "new content"
                    },
                    "rationale": "Update file"
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["file_ops"]
        }
        
        # Mock reflection to report blocker
        blocker_json = {
            "action": "blocked",
            "parameters": {"reason": "Permission denied"},
            "rationale": "Cannot write to file"
        }
        
        task_executor.llm.generate.side_effect = [
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(blocker_json), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute task
        result = task_executor.execute_task("Edit readonly file")
        
        # Verify error was handled (not crashed)
        assert len(result.actions_taken) >= 1
        # File should not have been modified
        assert readonly_file.read_text() == "original content"
        
        # Cleanup
        readonly_file.chmod(0o644)


class TestContextWindowManagement:
    """Test context window management with long task histories."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory."""
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    @pytest.fixture
    def task_executor(self, temp_project_dir):
        """Create TaskExecutor."""
        mock_llm = Mock(spec=LocalLLMInterface)
        code_agent = CodeAgent(project_root=temp_project_dir)
        config = SystemConfig(
            llm=LLMConfig(endpoint="http://localhost:11434", model_name="test-model"),
            project_root=temp_project_dir
        )
        context_manager = ContextManager(config)
        
        executor = TaskExecutor(
            llm_interface=mock_llm,
            code_agent=code_agent,
            context_manager=context_manager
        )
        executor.llm = mock_llm
        return executor
    
    def test_summarizes_long_execution_history(self, task_executor):
        """Test that long execution histories are summarized.
        
        Validates: Requirements 7.7, 15.5
        """
        # Create a long execution history
        for i in range(15):
            task_executor.execution_history.append({
                "timestamp": datetime.now().isoformat(),
                "action": "create_file",
                "parameters": {"file_path": f"file{i}.py", "content": f"# File {i}"},
                "rationale": f"Create file {i}",
                "result": {"success": True, "message": f"Created file{i}.py"}
            })
        
        # Get summarized history
        summary = task_executor._summarize_execution_history()
        
        # Verify summary is shorter than full history
        assert len(summary) < sum(len(str(entry)) for entry in task_executor.execution_history)
        
        # Verify summary includes recent actions (should be more detailed for recent items)
        assert "file14.py" in summary or "File 14" in summary or "file14" in summary.lower()
        
        # Verify the summary shows recent history (last 10 items are shown)
        # The implementation shows the last 10 steps
        assert "file5.py" in summary.lower() or "file 5" in summary.lower()  # Should include items from position 5 onward
    
    def test_maintains_relevant_context_in_reflection(self, task_executor):
        """Test that reflection prompts include relevant context.
        
        Validates: Requirements 7.7
        """
        # Add some execution history
        task_executor.execution_history = [
            {
                "timestamp": datetime.now().isoformat(),
                "action": "create_file",
                "parameters": {"file_path": "module.py", "content": "# Module"},
                "rationale": "Create module",
                "result": {"success": True, "message": "Created"}
            },
            {
                "timestamp": datetime.now().isoformat(),
                "action": "run_command",
                "parameters": {"command": "pytest"},
                "rationale": "Run tests",
                "result": {"success": False, "message": "Tests failed"}
            }
        ]
        
        task_executor.files_modified = ["module.py"]
        task_executor.test_results = {"pytest": False}
        
        # Build reflection prompt
        prompt = task_executor._build_reflection_prompt("Create and test module")
        
        # Verify prompt includes key information
        assert "module.py" in prompt or "create_file" in prompt.lower()
        assert "test" in prompt.lower() or "pytest" in prompt.lower()
        assert "failed" in prompt.lower() or "✗" in prompt
    
    def test_tracks_files_modified_throughout_execution(self, task_executor, temp_project_dir):
        """Test that files modified are tracked across multiple steps.
        
        Validates: Requirements 7.7, 15.2
        """
        # Mock planning with multiple file operations
        plan_json = {
            "steps": [
                {
                    "action": "create_file",
                    "parameters": {"file_path": "file1.py", "content": "# File 1"},
                    "rationale": "Create first file"
                },
                {
                    "action": "create_file",
                    "parameters": {"file_path": "file2.py", "content": "# File 2"},
                    "rationale": "Create second file"
                },
                {
                    "action": "edit_file",
                    "parameters": {"file_path": "file1.py", "new_content": "# File 1 updated"},
                    "rationale": "Update first file"
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["file_ops"]
        }
        
        complete_json = {
            "action": "complete",
            "parameters": {"summary": "Created and updated files"},
            "rationale": "Done"
        }
        
        task_executor.llm.generate.side_effect = [
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(complete_json), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute task
        result = task_executor.execute_task("Create and update files")
        
        # Verify files_modified tracks unique files
        assert len(result.files_modified) == 2
        assert "file1.py" in result.files_modified
        assert "file2.py" in result.files_modified
    
    def test_provides_execution_log(self, task_executor, temp_project_dir):
        """Test that detailed execution log is provided.
        
        Validates: Requirements 15.1, 15.5
        """
        # Mock simple task
        plan_json = {
            "steps": [
                {
                    "action": "create_file",
                    "parameters": {"file_path": "log_test.py", "content": "# Test"},
                    "rationale": "Create file"
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["file_ops"]
        }
        
        complete_json = {
            "action": "complete",
            "parameters": {"summary": "File created"},
            "rationale": "Done"
        }
        
        task_executor.llm.generate.side_effect = [
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(complete_json), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute task
        result = task_executor.execute_task("Create log test file")
        
        # Verify execution log is present and informative
        assert len(result.execution_log) > 0
        
        # Log should mention the actions taken
        log_text = " ".join(result.execution_log)
        assert "create_file" in log_text.lower() or "log_test.py" in log_text.lower()


class TestStateManagement:
    """Test state management across task execution."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory."""
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    @pytest.fixture
    def task_executor(self, temp_project_dir):
        """Create TaskExecutor."""
        mock_llm = Mock(spec=LocalLLMInterface)
        code_agent = CodeAgent(project_root=temp_project_dir)
        config = SystemConfig(
            llm=LLMConfig(endpoint="http://localhost:11434", model_name="test-model"),
            project_root=temp_project_dir
        )
        context_manager = ContextManager(config)
        
        executor = TaskExecutor(
            llm_interface=mock_llm,
            code_agent=code_agent,
            context_manager=context_manager
        )
        executor.llm = mock_llm
        return executor
    
    def test_state_reset_between_tasks(self, task_executor):
        """Test that state is properly reset between task executions.
        
        Validates: Internal correctness
        """
        # Execute first task
        plan1_json = {
            "steps": [
                {
                    "action": "create_file",
                    "parameters": {"file_path": "task1.py", "content": "# Task 1"},
                    "rationale": "First task"
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["file_ops"]
        }
        
        complete_json = {
            "action": "complete",
            "parameters": {"summary": "Done"},
            "rationale": "Complete"
        }
        
        task_executor.llm.generate.side_effect = [
            LLMResponse(content=json.dumps(plan1_json), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(complete_json), tool_calls=[], finish_reason="stop")
        ]
        
        result1 = task_executor.execute_task("Task 1")
        
        # Capture state after first task
        history_count_1 = len(task_executor.execution_history)
        files_modified_1 = len(task_executor.files_modified)
        
        # Execute second task
        plan2_json = {
            "steps": [
                {
                    "action": "create_file",
                    "parameters": {"file_path": "task2.py", "content": "# Task 2"},
                    "rationale": "Second task"
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["file_ops"]
        }
        
        task_executor.llm.generate.side_effect = [
            LLMResponse(content=json.dumps(plan2_json), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(complete_json), tool_calls=[], finish_reason="stop")
        ]
        
        result2 = task_executor.execute_task("Task 2")
        
        # Verify state was reset (each task starts fresh)
        # The second task should only show its own actions, not accumulated
        assert "task1.py" not in result2.files_modified
        assert "task2.py" in result2.files_modified
    
    def test_test_results_tracking(self, task_executor):
        """Test that test results are properly tracked.
        
        Validates: Requirements 7.4
        """
        # Mock task with test execution
        plan_json = {
            "steps": [
                {
                    "action": "run_command",
                    "parameters": {
                        "command": "python -m pytest test_pass.py",
                        "cwd": task_executor.code_agent.project_root
                    },
                    "rationale": "Run passing test"
                },
                {
                    "action": "run_command",
                    "parameters": {
                        "command": "python -m pytest test_fail.py",
                        "cwd": task_executor.code_agent.project_root
                    },
                    "rationale": "Run failing test"
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["command_executor"]
        }
        
        complete_json = {
            "action": "complete",
            "parameters": {"summary": "Tests run"},
            "rationale": "Done"
        }
        
        task_executor.llm.generate.side_effect = [
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(complete_json), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute task
        result = task_executor.execute_task("Run tests")
        
        # Verify test results were tracked
        assert len(task_executor.test_results) > 0
        
        # Result should indicate test status
        # (tests_passed should be False if any test failed)
        if False in task_executor.test_results.values():
            assert not result.tests_passed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
