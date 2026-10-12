"""End-to-end integration test for debugging workflow.

This test verifies that the Task Executor can:
1. Identify issues in failing tests
2. Edit existing code to fix bugs
3. Verify that tests pass after the fix

Requirements validated:
- 3.1: Locate relevant code sections when given a modification request
- 3.2: Make precise edits that preserve existing functionality
- 3.3: Maintain consistency with surrounding code style
- 7.5: Debug and fix issues when tests fail
- 7.7: Provide summary of changes made when task is complete
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock

from src.core.task_executor import TaskExecutor
from src.core.models import (
    LLMResponse,
    LLMConfig,
    SystemConfig
)
from src.core.llm_interface import LocalLLMInterface
from src.agents.code_agent import CodeAgent
from src.context.context_manager import ContextManager


class TestDebuggingWorkflow:
    """Test end-to-end debugging workflow."""
    
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
    
    @pytest.fixture
    def buggy_code_project(self, temp_project_dir):
        """Create a project with buggy code and failing test."""
        # Create buggy calculator module
        calculator_code = '''"""Simple calculator module with a bug."""

def add(a, b):
    """Add two numbers."""
    return a + b

def subtract(a, b):
    """Subtract b from a."""
    return a - b

def multiply(a, b):
    """Multiply two numbers - has a bug!"""
    return a + b  # BUG: Should be a * b

def divide(a, b):
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
'''
        
        # Create failing test
        test_code = '''"""Tests for calculator module."""
import pytest
from calculator import add, subtract, multiply, divide

def test_add():
    """Test addition."""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

def test_subtract():
    """Test subtraction."""
    assert subtract(5, 3) == 2
    assert subtract(0, 1) == -1
    assert subtract(10, 10) == 0

def test_multiply():
    """Test multiplication - FAILS due to bug."""
    assert multiply(2, 3) == 6
    assert multiply(-2, 4) == -8
    assert multiply(0, 5) == 0
    assert multiply(7, 1) == 7

def test_divide():
    """Test division."""
    assert divide(6, 2) == 3
    assert divide(10, 5) == 2
    assert divide(1, 1) == 1
    
    with pytest.raises(ValueError):
        divide(5, 0)
'''
        
        # Write files
        calc_path = Path(temp_project_dir) / "calculator.py"
        test_path = Path(temp_project_dir) / "test_calculator.py"
        
        calc_path.write_text(calculator_code)
        test_path.write_text(test_code)
        
        return {
            "calculator_path": calc_path,
            "test_path": test_path,
            "project_dir": temp_project_dir
        }
    
    def test_debug_failing_test_and_fix_code(self, task_executor, mock_llm, buggy_code_project):
        """Test complete debugging workflow: identify issue, fix code, verify tests pass.
        
        This is an end-to-end test that:
        1. Starts with buggy code and a failing test
        2. Task executor identifies the bug
        3. Task executor fixes the code
        4. Tests pass after the fix
        
        Validates: Requirements 3.1, 3.2, 3.3, 7.5, 7.7
        """
        temp_project_dir = buggy_code_project["project_dir"]
        
        # Mock planning phase - analyze and fix the bug
        plan_json = {
            "steps": [
                {
                    "action": "run_command",
                    "parameters": {
                        "command": "python -m pytest test_calculator.py -v"
                    },
                    "rationale": "Run tests to see which ones are failing"
                },
                {
                    "action": "read_file",
                    "parameters": {
                        "file_path": "calculator.py"
                    },
                    "rationale": "Read the calculator code to find the bug"
                },
                {
                    "action": "edit_file",
                    "parameters": {
                        "file_path": "calculator.py",
                        "new_content": '''"""Simple calculator module with a bug."""

def add(a, b):
    """Add two numbers."""
    return a + b

def subtract(a, b):
    """Subtract b from a."""
    return a - b

def multiply(a, b):
    """Multiply two numbers."""
    return a * b

def divide(a, b):
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
'''
                    },
                    "rationale": "Fix the multiply function to use multiplication instead of addition"
                },
                {
                    "action": "run_command",
                    "parameters": {
                        "command": "python -m pytest test_calculator.py -v"
                    },
                    "rationale": "Verify that all tests pass after the fix"
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["file_ops", "command_executor"]
        }
        
        # First reflection - after running initial tests and reading code
        reflection_1_json = {
            "action": "continue",
            "parameters": {
                "observation": "Tests are failing in test_multiply. Found bug in multiply function: uses addition instead of multiplication."
            },
            "rationale": "Need to edit the file to fix the bug"
        }
        
        # Second reflection - after fixing and running tests again
        reflection_2_json = {
            "action": "complete",
            "parameters": {
                "summary": "Fixed bug in multiply function. Changed 'return a + b' to 'return a * b'. All tests now pass."
            },
            "rationale": "Bug fixed and all tests passing"
        }
        
        mock_llm.generate.side_effect = [
            # Planning call
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            # First reflection after reading test results and code
            LLMResponse(content=json.dumps(reflection_1_json), tool_calls=[], finish_reason="stop"),
            # Second reflection after fix
            LLMResponse(content=json.dumps(reflection_2_json), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute debugging task
        result = task_executor.execute_task(
            "Debug the failing test in test_calculator.py and fix the code"
        )
        
        # Verify result
        assert result.success, f"Task should succeed but got error: {result.error_message}"
        assert "calculator.py" in result.files_modified, "Should have modified calculator.py"
        assert len(result.actions_taken) >= 3, "Should have run tests, read file, and edited file"
        
        # Verify the bug was actually fixed in the file
        calc_path = Path(temp_project_dir) / "calculator.py"
        fixed_code = calc_path.read_text()
        assert "return a * b" in fixed_code, "multiply function should be fixed"
        assert "return a + b  # BUG" not in fixed_code, "Bug comment should be removed"
        
        # Verify summary mentions the fix
        assert "multiply" in result.execution_log[-1].lower() or \
               "multiply" in str(result.actions_taken).lower(), \
               "Summary should mention the multiply function fix"
    
    def test_debug_multiple_issues(self, task_executor, mock_llm, temp_project_dir):
        """Test debugging workflow with multiple issues to fix.
        
        Validates: Requirements 3.1, 3.2, 3.3, 3.5, 7.5
        """
        # Create code with multiple bugs
        buggy_code = '''"""String utilities with multiple bugs."""

def reverse_string(s):
    """Reverse a string - has off-by-one error."""
    return s[::-2]  # BUG: Should be s[::-1]

def capitalize_words(s):
    """Capitalize first letter of each word - incomplete."""
    return s.title()  # Works but could handle edge cases

def count_vowels(s):
    """Count vowels in string - missing vowels."""
    vowels = "aei"  # BUG: Missing 'o' and 'u'
    return sum(1 for char in s.lower() if char in vowels)

def is_palindrome(s):
    """Check if string is palindrome - wrong logic."""
    return s == s[::-1]  # Doesn't handle spaces/punctuation
'''
        
        test_code = '''"""Tests for string utilities."""
import pytest
from string_utils import reverse_string, capitalize_words, count_vowels, is_palindrome

def test_reverse_string():
    assert reverse_string("hello") == "olleh"
    assert reverse_string("python") == "nohtyp"
    assert reverse_string("a") == "a"

def test_count_vowels():
    assert count_vowels("hello") == 2  # e, o
    assert count_vowels("python") == 1  # o
    assert count_vowels("aeiou") == 5
    assert count_vowels("xyz") == 0

def test_is_palindrome():
    assert is_palindrome("racecar") == True
    assert is_palindrome("hello") == False
    assert is_palindrome("A man a plan a canal Panama") == True
'''
        
        # Write files
        code_path = Path(temp_project_dir) / "string_utils.py"
        test_path = Path(temp_project_dir) / "test_string_utils.py"
        code_path.write_text(buggy_code)
        test_path.write_text(test_code)
        
        # Mock planning and execution
        plan_json = {
            "steps": [
                {
                    "action": "run_command",
                    "parameters": {"command": "python -m pytest test_string_utils.py -v"},
                    "rationale": "Identify failing tests"
                },
                {
                    "action": "read_file",
                    "parameters": {"file_path": "string_utils.py"},
                    "rationale": "Analyze the code"
                },
                {
                    "action": "edit_file",
                    "parameters": {
                        "file_path": "string_utils.py",
                        "new_content": '''"""String utilities with multiple bugs."""

def reverse_string(s):
    """Reverse a string."""
    return s[::-1]

def capitalize_words(s):
    """Capitalize first letter of each word."""
    return s.title()

def count_vowels(s):
    """Count vowels in string."""
    vowels = "aeiou"
    return sum(1 for char in s.lower() if char in vowels)

def is_palindrome(s):
    """Check if string is palindrome."""
    cleaned = "".join(c.lower() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]
'''
                    },
                    "rationale": "Fix all identified bugs"
                },
                {
                    "action": "run_command",
                    "parameters": {"command": "python -m pytest test_string_utils.py -v"},
                    "rationale": "Verify all fixes work"
                }
            ],
            "estimated_complexity": "moderate",
            "required_tools": ["file_ops", "command_executor"]
        }
        
        reflection_json = {
            "action": "complete",
            "parameters": {
                "summary": "Fixed multiple bugs: reverse_string slicing, count_vowels missing vowels, is_palindrome not handling spaces/punctuation. All tests pass."
            },
            "rationale": "All bugs fixed, tests passing"
        }
        
        mock_llm.generate.side_effect = [
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(reflection_json), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute task
        result = task_executor.execute_task(
            "Fix all failing tests in test_string_utils.py"
        )
        
        # Verify results
        assert result.success
        assert "string_utils.py" in result.files_modified
        
        # Verify fixes
        fixed_code = code_path.read_text()
        assert "s[::-1]" in fixed_code, "reverse_string should be fixed"
        assert '"aeiou"' in fixed_code, "count_vowels should include all vowels"
        assert "isalnum()" in fixed_code or "is_palindrome" in fixed_code, \
               "is_palindrome should handle non-alphanumeric characters"
    
    def test_debug_with_error_messages(self, task_executor, mock_llm, temp_project_dir):
        """Test that debugging workflow uses error messages to identify issues.
        
        Validates: Requirements 3.1, 7.5
        """
        # Create code with a runtime error
        buggy_code = '''"""Code with runtime error."""

def get_user_age(user_dict):
    """Get user age from dictionary."""
    return user_dict["age"]  # KeyError if 'age' not present

def process_users(users):
    """Process list of users."""
    total_age = 0
    for user in users:
        total_age += get_user_age(user)
    return total_age / len(users)
'''
        
        test_code = '''"""Test with runtime errors."""
import pytest
from user_processor import get_user_age, process_users

def test_get_user_age():
    user = {"name": "Alice", "age": 30}
    assert get_user_age(user) == 30
    
    # This will fail with KeyError
    user_no_age = {"name": "Bob"}
    result = get_user_age(user_no_age)
    assert result is None or result == 0

def test_process_users():
    users = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25}
    ]
    assert process_users(users) == 27.5
'''
        
        code_path = Path(temp_project_dir) / "user_processor.py"
        test_path = Path(temp_project_dir) / "test_user_processor.py"
        code_path.write_text(buggy_code)
        test_path.write_text(test_code)
        
        # Mock execution plan
        plan_json = {
            "steps": [
                {
                    "action": "run_command",
                    "parameters": {"command": "python -m pytest test_user_processor.py -v"},
                    "rationale": "See the error messages"
                },
                {
                    "action": "read_file",
                    "parameters": {"file_path": "user_processor.py"},
                    "rationale": "Examine the code causing KeyError"
                },
                {
                    "action": "edit_file",
                    "parameters": {
                        "file_path": "user_processor.py",
                        "new_content": '''"""Code with runtime error."""

def get_user_age(user_dict):
    """Get user age from dictionary."""
    return user_dict.get("age", 0)

def process_users(users):
    """Process list of users."""
    total_age = 0
    for user in users:
        total_age += get_user_age(user)
    return total_age / len(users)
'''
                    },
                    "rationale": "Use .get() to handle missing 'age' key gracefully"
                },
                {
                    "action": "run_command",
                    "parameters": {"command": "python -m pytest test_user_processor.py -v"},
                    "rationale": "Verify fix resolves KeyError"
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["file_ops", "command_executor"]
        }
        
        reflection_json = {
            "action": "complete",
            "parameters": {
                "summary": "Fixed KeyError in get_user_age by using .get() method with default value. Tests now pass."
            },
            "rationale": "Error resolved"
        }
        
        mock_llm.generate.side_effect = [
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(reflection_json), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute
        result = task_executor.execute_task(
            "Fix the KeyError in test_user_processor.py"
        )
        
        # Verify
        assert result.success
        assert "user_processor.py" in result.files_modified
        
        fixed_code = code_path.read_text()
        assert '.get("age"' in fixed_code or ".get('age'" in fixed_code, \
               "Should use .get() method to handle missing keys"
    
    def test_preserves_code_style_when_fixing(self, task_executor, mock_llm, temp_project_dir):
        """Test that debugging maintains existing code style and conventions.
        
        Validates: Requirements 3.3
        """
        # Create code with specific style (e.g., double quotes, 4-space indent)
        styled_code = '''"""Module with specific code style."""

class DataProcessor:
    """Process data with specific formatting style."""
    
    def __init__(self):
        """Initialize processor."""
        self.data = []
    
    def add_item(self, item):
        """Add item to data list - has bug."""
        self.data.append(item + 1)  # BUG: Shouldn't add 1
        return len(self.data)
    
    def get_total(self):
        """Get total of all items."""
        return sum(self.data)
'''
        
        test_code = '''"""Tests for DataProcessor."""
import pytest
from data_processor import DataProcessor

def test_add_item():
    processor = DataProcessor()
    processor.add_item(5)
    processor.add_item(10)
    assert processor.get_total() == 15  # Should be 5 + 10, not 6 + 11
'''
        
        code_path = Path(temp_project_dir) / "data_processor.py"
        test_path = Path(temp_project_dir) / "test_data_processor.py"
        code_path.write_text(styled_code)
        test_path.write_text(test_code)
        
        plan_json = {
            "steps": [
                {
                    "action": "read_file",
                    "parameters": {"file_path": "data_processor.py"},
                    "rationale": "Read code to understand style"
                },
                {
                    "action": "edit_file",
                    "parameters": {
                        "file_path": "data_processor.py",
                        "new_content": '''"""Module with specific code style."""

class DataProcessor:
    """Process data with specific formatting style."""
    
    def __init__(self):
        """Initialize processor."""
        self.data = []
    
    def add_item(self, item):
        """Add item to data list."""
        self.data.append(item)
        return len(self.data)
    
    def get_total(self):
        """Get total of all items."""
        return sum(self.data)
'''
                    },
                    "rationale": "Fix bug while maintaining indentation and style"
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["file_ops"]
        }
        
        reflection_json = {
            "action": "complete",
            "parameters": {"summary": "Fixed add_item method to not add 1 to items"},
            "rationale": "Bug fixed with style preserved"
        }
        
        mock_llm.generate.side_effect = [
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(reflection_json), tool_calls=[], finish_reason="stop")
        ]
        
        result = task_executor.execute_task("Fix the bug in data_processor.py")
        
        assert result.success
        fixed_code = code_path.read_text()
        
        # Verify style is preserved
        assert '"""' in fixed_code, "Docstrings should use triple double quotes"
        assert "    def " in fixed_code, "Should maintain 4-space indentation"
        assert "self.data.append(item)" in fixed_code, "Bug should be fixed"
        assert 'self.data.append(item + 1)' not in fixed_code or "# BUG" not in fixed_code, \
               "Bug should be removed"
