"""End-to-end system test for Python project creation.

This test validates the complete workflow for creating a new Python module with tests,
verifying that:
- Files are created with correct structure
- Tests pass when executed
- Code follows Python conventions
- The system successfully orchestrates all components

Requirements validated:
- 2.1: Generate complete, functional code that satisfies task requirements
- 2.2: Create new files in appropriate project directories
- 2.3: Follow existing code style and conventions
- 2.4: Include appropriate comments and documentation
- 2.5: Generate code without syntax errors
- 2.6: Create all necessary files to complete the task
- 7.1: Plan steps needed to complete development tasks
- 7.2: Coordinate all system components to execute the plan
- 7.3: Write tests for new functionality
- 7.4: Run tests to verify correctness
- 11.1: Generate syntactically correct code in Python
"""

import pytest
import tempfile
import shutil
import subprocess
import ast
from pathlib import Path
from unittest.mock import Mock
import json

from src.core.task_executor import TaskExecutor
from src.core.models import LLMResponse, LLMConfig, SystemConfig
from src.core.llm_interface import LocalLLMInterface
from src.agents.code_agent import CodeAgent
from src.context.context_manager import ContextManager


class TestPythonProjectEndToEnd:
    """End-to-end tests for Python project creation workflow."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory for testing."""
        tmpdir = tempfile.mkdtemp(prefix="e2e_python_test_")
        yield tmpdir
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    @pytest.fixture
    def task_executor(self, temp_project_dir):
        """Create TaskExecutor with mocked LLM for controlled testing."""
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
    
    def test_create_python_module_with_tests(self, task_executor, temp_project_dir):
        """Test complete workflow: create Python module with tests and verify execution.
        
        This test validates the entire system's ability to:
        1. Plan a multi-step task (module creation + test creation)
        2. Generate syntactically correct Python code
        3. Follow Python conventions (naming, structure, documentation)
        4. Create tests that verify functionality
        5. Execute tests successfully
        
        Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 7.1, 7.2, 7.3, 7.4, 11.1
        """
        # Define the expected module content with proper Python conventions
        module_content = '''"""String utility module.

This module provides utility functions for string manipulation.
"""


def capitalize_words(text: str) -> str:
    """Capitalize the first letter of each word in the text.
    
    Args:
        text: The input text to capitalize
        
    Returns:
        Text with each word capitalized
        
    Examples:
        >>> capitalize_words("hello world")
        'Hello World'
    """
    if not text:
        return text
    return ' '.join(word.capitalize() for word in text.split())


def reverse_string(text: str) -> str:
    """Reverse the characters in a string.
    
    Args:
        text: The input text to reverse
        
    Returns:
        The reversed text
        
    Examples:
        >>> reverse_string("hello")
        'olleh'
    """
    return text[::-1]
'''
        
        # Define the expected test content
        test_content = '''"""Tests for string_utils module.

This module contains unit tests for the string utility functions.
"""

import pytest
from string_utils import capitalize_words, reverse_string


def test_capitalize_words():
    """Test capitalize_words function with various inputs."""
    # Test normal case
    assert capitalize_words("hello world") == "Hello World"
    
    # Test single word
    assert capitalize_words("python") == "Python"
    
    # Test empty string
    assert capitalize_words("") == ""
    
    # Test already capitalized
    assert capitalize_words("Hello World") == "Hello World"


def test_reverse_string():
    """Test reverse_string function with various inputs."""
    # Test normal case
    assert reverse_string("hello") == "olleh"
    
    # Test single character
    assert reverse_string("a") == "a"
    
    # Test empty string
    assert reverse_string("") == ""
    
    # Test palindrome
    assert reverse_string("racecar") == "racecar"


def test_capitalize_words_with_special_input():
    """Test capitalize_words with different input types."""
    # Test with numbers
    assert capitalize_words("hello 123") == "Hello 123"


def test_reverse_string_with_special_characters():
    """Test reverse_string preserves special characters."""
    assert reverse_string("hello!") == "!olleh"
'''
        
        # Mock LLM to return a well-structured execution plan
        plan_json = {
            "steps": [
                {
                    "action": "create_file",
                    "parameters": {
                        "file_path": "string_utils.py",
                        "content": module_content
                    },
                    "rationale": "Create the main module with string utility functions following Python conventions"
                },
                {
                    "action": "create_file",
                    "parameters": {
                        "file_path": "test_string_utils.py",
                        "content": test_content
                    },
                    "rationale": "Create comprehensive tests for the string utility functions"
                },
                {
                    "action": "run_command",
                    "parameters": {
                        "command": "python -m pytest test_string_utils.py -v",
                        "cwd": temp_project_dir
                    },
                    "rationale": "Execute tests to verify functionality"
                }
            ],
            "estimated_complexity": "moderate",
            "required_tools": ["file_ops", "command_executor"]
        }
        
        # Mock reflection to mark task as complete after execution
        complete_json = {
            "action": "complete",
            "parameters": {
                "summary": "Created string_utils module with capitalize_words and reverse_string functions. Created comprehensive test suite with 6 test cases covering normal cases, edge cases, and special scenarios. All tests passed successfully."
            },
            "rationale": "Module and tests created successfully, all tests passing"
        }
        
        task_executor.llm.generate.side_effect = [
            # Planning phase
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            # Reflection phase
            LLMResponse(content=json.dumps(complete_json), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute the task
        result = task_executor.execute_task(
            "Create a Python module called string_utils with functions to capitalize words and reverse strings. Include comprehensive tests."
        )
        
        # Verify task completed successfully
        assert result.success, f"Task failed: {result.error_message}"
        assert not result.error_message
        
        # Verify files were created (Requirement 2.2, 2.6)
        module_file = Path(temp_project_dir) / "string_utils.py"
        test_file = Path(temp_project_dir) / "test_string_utils.py"
        
        assert module_file.exists(), "Module file was not created"
        assert test_file.exists(), "Test file was not created"
        
        # Verify correct files tracked in result
        assert len(result.files_modified) == 2
        assert "string_utils.py" in result.files_modified
        assert "test_string_utils.py" in result.files_modified
        
        # Verify execution plan was followed (Requirement 7.1, 7.2)
        assert len(result.actions_taken) == 3
        assert result.actions_taken[0].action == "create_file"
        assert result.actions_taken[1].action == "create_file"
        assert result.actions_taken[2].action == "run_command"
        
        # Verify code is syntactically correct Python (Requirement 2.5, 11.1)
        module_code = module_file.read_text()
        test_code = test_file.read_text()
        
        try:
            ast.parse(module_code)
        except SyntaxError as e:
            pytest.fail(f"Module has syntax errors: {e}")
        
        try:
            ast.parse(test_code)
        except SyntaxError as e:
            pytest.fail(f"Test file has syntax errors: {e}")
        
        # Verify code follows Python conventions (Requirement 2.3, 2.4)
        # Check for docstrings
        assert '"""' in module_code, "Module missing docstrings"
        assert '"""' in test_code, "Tests missing docstrings"
        
        # Check for function definitions
        assert "def capitalize_words" in module_code
        assert "def reverse_string" in module_code
        assert "def test_capitalize_words" in test_code
        assert "def test_reverse_string" in test_code
        
        # Check for type hints (Python convention)
        assert "str) -> str:" in module_code, "Missing type hints"
        
        # Check for proper imports in test file
        assert "import pytest" in test_code
        assert "from string_utils import" in test_code
        
        # Verify tests were written (Requirement 7.3)
        assert "def test_" in test_code
        assert "assert" in test_code
        
        # Verify tests can be executed (Requirement 7.4)
        # Run the actual tests to ensure they pass
        result_pytest = subprocess.run(
            ["python", "-m", "pytest", "test_string_utils.py", "-v"],
            cwd=temp_project_dir,
            capture_output=True,
            text=True
        )
        
        assert result_pytest.returncode == 0, f"Tests failed:\n{result_pytest.stdout}\n{result_pytest.stderr}"
        assert "passed" in result_pytest.stdout.lower(), "Tests did not pass"
        
        # Verify the actual functionality works
        # Import and test the module directly
        import sys
        sys.path.insert(0, temp_project_dir)
        try:
            from string_utils import capitalize_words, reverse_string
            
            # Test the actual functions (Requirement 2.1)
            assert capitalize_words("hello world") == "Hello World"
            assert reverse_string("hello") == "olleh"
            
        finally:
            sys.path.remove(temp_project_dir)
            # Clean up imported module
            if 'string_utils' in sys.modules:
                del sys.modules['string_utils']
    
    def test_create_python_class_with_tests(self, task_executor, temp_project_dir):
        """Test creating a Python class with object-oriented design and tests.
        
        This verifies the system can handle more complex Python structures including:
        - Class definitions with multiple methods
        - __init__ constructors
        - Instance variables and methods
        - Proper class documentation
        
        Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 7.1, 7.2, 7.3, 7.4, 11.1
        """
        # Define a class-based module
        class_module_content = '''"""Calculator class module.

This module provides a Calculator class for basic arithmetic operations.
"""


class Calculator:
    """A simple calculator for basic arithmetic operations.
    
    Attributes:
        result: The current result of calculations
    """
    
    def __init__(self):
        """Initialize calculator with result set to 0."""
        self.result = 0
    
    def add(self, value: float) -> float:
        """Add a value to the current result.
        
        Args:
            value: The value to add
            
        Returns:
            The new result after addition
        """
        self.result += value
        return self.result
    
    def subtract(self, value: float) -> float:
        """Subtract a value from the current result.
        
        Args:
            value: The value to subtract
            
        Returns:
            The new result after subtraction
        """
        self.result -= value
        return self.result
    
    def reset(self) -> None:
        """Reset the calculator result to 0."""
        self.result = 0
    
    def get_result(self) -> float:
        """Get the current result.
        
        Returns:
            The current result
        """
        return self.result
'''
        
        class_test_content = '''"""Tests for Calculator class.

This module contains unit tests for the Calculator class.
"""

import pytest
from calculator import Calculator


def test_calculator_initialization():
    """Test that calculator initializes with result 0."""
    calc = Calculator()
    assert calc.get_result() == 0


def test_add():
    """Test addition functionality."""
    calc = Calculator()
    assert calc.add(5) == 5
    assert calc.add(3) == 8


def test_subtract():
    """Test subtraction functionality."""
    calc = Calculator()
    calc.add(10)
    assert calc.subtract(3) == 7
    assert calc.subtract(2) == 5


def test_reset():
    """Test reset functionality."""
    calc = Calculator()
    calc.add(10)
    calc.reset()
    assert calc.get_result() == 0


def test_chained_operations():
    """Test multiple operations in sequence."""
    calc = Calculator()
    calc.add(10)
    calc.add(5)
    calc.subtract(3)
    assert calc.get_result() == 12
'''
        
        # Mock LLM plan
        plan_json = {
            "steps": [
                {
                    "action": "create_file",
                    "parameters": {
                        "file_path": "calculator.py",
                        "content": class_module_content
                    },
                    "rationale": "Create Calculator class with proper OOP design"
                },
                {
                    "action": "create_file",
                    "parameters": {
                        "file_path": "test_calculator.py",
                        "content": class_test_content
                    },
                    "rationale": "Create comprehensive tests for Calculator class"
                },
                {
                    "action": "run_command",
                    "parameters": {
                        "command": "python -m pytest test_calculator.py -v",
                        "cwd": temp_project_dir
                    },
                    "rationale": "Run tests to verify Calculator implementation"
                }
            ],
            "estimated_complexity": "moderate",
            "required_tools": ["file_ops", "command_executor"]
        }
        
        complete_json = {
            "action": "complete",
            "parameters": {
                "summary": "Created Calculator class with add, subtract, reset methods. Implemented 5 test cases. All tests passed."
            },
            "rationale": "Class and tests completed successfully"
        }
        
        task_executor.llm.generate.side_effect = [
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(complete_json), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute task
        result = task_executor.execute_task(
            "Create a Calculator class with add and subtract methods. Include tests."
        )
        
        # Verify success
        assert result.success
        
        # Verify files created (Requirement 2.2, 2.6)
        calc_file = Path(temp_project_dir) / "calculator.py"
        test_file = Path(temp_project_dir) / "test_calculator.py"
        assert calc_file.exists()
        assert test_file.exists()
        
        # Verify syntax (Requirement 2.5, 11.1)
        calc_code = calc_file.read_text()
        test_code = test_file.read_text()
        
        try:
            ast.parse(calc_code)
            ast.parse(test_code)
        except SyntaxError as e:
            pytest.fail(f"Syntax error: {e}")
        
        # Verify OOP structure (Requirement 2.3, 2.4)
        assert "class Calculator" in calc_code
        assert "def __init__" in calc_code
        assert "self." in calc_code
        assert '"""' in calc_code  # Docstrings
        
        # Verify tests exist (Requirement 7.3)
        assert "def test_" in test_code
        assert "Calculator()" in test_code
        
        # Run actual tests (Requirement 7.4)
        result_pytest = subprocess.run(
            ["python", "-m", "pytest", "test_calculator.py", "-v"],
            cwd=temp_project_dir,
            capture_output=True,
            text=True
        )
        
        assert result_pytest.returncode == 0, f"Tests failed:\n{result_pytest.stdout}\n{result_pytest.stderr}"
        
        # Verify functionality (Requirement 2.1)
        import sys
        sys.path.insert(0, temp_project_dir)
        try:
            from calculator import Calculator
            
            calc = Calculator()
            assert calc.add(10) == 10
            assert calc.subtract(3) == 7
            calc.reset()
            assert calc.get_result() == 0
            
        finally:
            sys.path.remove(temp_project_dir)
            if 'calculator' in sys.modules:
                del sys.modules['calculator']
    
    def test_python_conventions_validation(self, task_executor, temp_project_dir):
        """Test that generated code follows Python conventions.
        
        Verifies:
        - PEP 8 naming conventions (snake_case for functions/variables)
        - Docstrings for modules, classes, and functions
        - Type hints
        - Proper imports
        - Comments for complex logic
        
        Validates: Requirements 2.3, 2.4, 11.1, 11.2
        """
        # Define code that demonstrates Python conventions
        conventions_module = '''"""Math utilities module.

Provides mathematical utility functions following Python best practices.
"""

from typing import List


def calculate_average(numbers: List[float]) -> float:
    """Calculate the average of a list of numbers.
    
    Args:
        numbers: List of numbers to average
        
    Returns:
        The arithmetic mean of the numbers
        
    Raises:
        ValueError: If the list is empty
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    
    # Calculate sum and divide by count
    total = sum(numbers)
    count = len(numbers)
    return total / count


def find_maximum(numbers: List[float]) -> float:
    """Find the maximum value in a list of numbers.
    
    Args:
        numbers: List of numbers to search
        
    Returns:
        The maximum value
        
    Raises:
        ValueError: If the list is empty
    """
    if not numbers:
        raise ValueError("Cannot find maximum of empty list")
    
    return max(numbers)
'''
        
        conventions_test = '''"""Tests for math_utils module."""

import pytest
from math_utils import calculate_average, find_maximum


def test_calculate_average():
    """Test average calculation."""
    assert calculate_average([1, 2, 3, 4, 5]) == 3.0
    assert calculate_average([10]) == 10.0


def test_calculate_average_empty_list():
    """Test that empty list raises ValueError."""
    with pytest.raises(ValueError):
        calculate_average([])


def test_find_maximum():
    """Test finding maximum value."""
    assert find_maximum([1, 5, 3, 2, 4]) == 5
    assert find_maximum([10]) == 10


def test_find_maximum_empty_list():
    """Test that empty list raises ValueError."""
    with pytest.raises(ValueError):
        find_maximum([])
'''
        
        plan_json = {
            "steps": [
                {
                    "action": "create_file",
                    "parameters": {
                        "file_path": "math_utils.py",
                        "content": conventions_module
                    },
                    "rationale": "Create module following Python conventions"
                },
                {
                    "action": "create_file",
                    "parameters": {
                        "file_path": "test_math_utils.py",
                        "content": conventions_test
                    },
                    "rationale": "Create tests following pytest conventions"
                },
                {
                    "action": "run_command",
                    "parameters": {
                        "command": "python -m pytest test_math_utils.py -v",
                        "cwd": temp_project_dir
                    },
                    "rationale": "Run tests"
                }
            ],
            "estimated_complexity": "moderate",
            "required_tools": ["file_ops", "command_executor"]
        }
        
        complete_json = {
            "action": "complete",
            "parameters": {"summary": "Created math utilities with proper conventions and tests"},
            "rationale": "All conventions followed, tests passing"
        }
        
        task_executor.llm.generate.side_effect = [
            LLMResponse(content=json.dumps(plan_json), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(complete_json), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute
        result = task_executor.execute_task("Create math utilities with average and max functions")
        
        assert result.success
        
        # Read generated code
        module_file = Path(temp_project_dir) / "math_utils.py"
        module_code = module_file.read_text()
        
        # Verify Python conventions (Requirement 2.3, 2.4)
        # PEP 8 naming: snake_case function names
        assert "def calculate_average" in module_code
        assert "def find_maximum" in module_code
        
        # Module docstring
        assert module_code.strip().startswith('"""')
        
        # Function docstrings
        assert module_code.count('"""') >= 6  # Module + 2 functions with docstrings
        
        # Type hints
        assert "List[float]" in module_code
        assert "-> float:" in module_code
        
        # Proper imports
        assert "from typing import" in module_code
        
        # Comments for logic (Requirement 2.4)
        assert "#" in module_code
        
        # Run tests to verify functionality
        result_pytest = subprocess.run(
            ["python", "-m", "pytest", "test_math_utils.py", "-v"],
            cwd=temp_project_dir,
            capture_output=True,
            text=True
        )
        
        assert result_pytest.returncode == 0, f"Tests failed:\n{result_pytest.stdout}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
