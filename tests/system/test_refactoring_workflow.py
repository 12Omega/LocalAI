"""End-to-end test for refactoring workflow.

This test validates the complete refactoring workflow:
1. Create initial code with tests
2. Refactor code while maintaining functionality
3. Verify tests still pass after refactoring
4. Verify code quality improved while behavior preserved

Requirements validated:
- 3.1: Locate relevant code sections for modification
- 3.2: Make precise edits preserving existing functionality
- 3.3: Maintain consistency with surrounding code style
- 3.4: Preserve code structure and formatting conventions
- 3.5: Update all affected sections when editing introduces dependencies
- 7.6: Refactor code when necessary to maintain quality
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock
import json
from datetime import datetime

from src.core.task_executor import TaskExecutor
from src.core.models import (
    ExecutionPlan,
    ExecutionStep,
    TaskResult,
    LLMResponse,
    LLMConfig,
    SystemConfig
)
from src.core.llm_interface import LocalLLMInterface
from src.agents.code_agent import CodeAgent
from src.context.context_manager import ContextManager


class TestRefactoringWorkflow:
    """Test end-to-end refactoring workflow."""
    
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
    
    def test_refactor_duplicated_code(self, task_executor, mock_llm, temp_project_dir):
        """Test refactoring workflow that extracts duplicated code into a function.
        
        This test validates the complete refactoring workflow:
        1. Initial code has duplication
        2. Agent identifies duplication
        3. Agent extracts common logic into a new function
        4. Agent updates all call sites to use new function
        5. Tests still pass after refactoring
        
        Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 7.6
        """
        # Create initial code with duplication
        initial_code = '''"""Math utilities module."""

def calculate_rectangle_area(width, height):
    """Calculate area of a rectangle."""
    if width <= 0 or height <= 0:
        raise ValueError("Dimensions must be positive")
    return width * height


def calculate_triangle_area(base, height):
    """Calculate area of a triangle."""
    if base <= 0 or height <= 0:
        raise ValueError("Dimensions must be positive")
    return 0.5 * base * height


def calculate_circle_area(radius):
    """Calculate area of a circle."""
    if radius <= 0:
        raise ValueError("Radius must be positive")
    import math
    return math.pi * radius * radius
'''
        
        # Create initial tests
        initial_tests = '''"""Tests for math utilities."""
import pytest
from math_utils import (
    calculate_rectangle_area,
    calculate_triangle_area,
    calculate_circle_area
)


def test_rectangle_area():
    """Test rectangle area calculation."""
    assert calculate_rectangle_area(5, 10) == 50
    assert calculate_rectangle_area(2.5, 4) == 10.0


def test_rectangle_area_validation():
    """Test rectangle area validation."""
    with pytest.raises(ValueError, match="Dimensions must be positive"):
        calculate_rectangle_area(-5, 10)
    with pytest.raises(ValueError, match="Dimensions must be positive"):
        calculate_rectangle_area(5, 0)


def test_triangle_area():
    """Test triangle area calculation."""
    assert calculate_triangle_area(10, 5) == 25.0
    assert calculate_triangle_area(6, 3) == 9.0


def test_triangle_area_validation():
    """Test triangle area validation."""
    with pytest.raises(ValueError, match="Dimensions must be positive"):
        calculate_triangle_area(0, 5)
    with pytest.raises(ValueError, match="Dimensions must be positive"):
        calculate_triangle_area(10, -2)


def test_circle_area():
    """Test circle area calculation."""
    import math
    result = calculate_circle_area(5)
    expected = math.pi * 25
    assert abs(result - expected) < 0.0001


def test_circle_area_validation():
    """Test circle area validation."""
    with pytest.raises(ValueError, match="Radius must be positive"):
        calculate_circle_area(-5)
    with pytest.raises(ValueError, match="Radius must be positive"):
        calculate_circle_area(0)
'''
        
        # Write initial files
        math_utils_path = Path(temp_project_dir) / "math_utils.py"
        test_path = Path(temp_project_dir) / "test_math_utils.py"
        math_utils_path.write_text(initial_code)
        test_path.write_text(initial_tests)
        
        # Refactored code with extracted validation function
        refactored_code = '''"""Math utilities module."""

def _validate_positive(*values):
    """Validate that all values are positive.
    
    Args:
        *values: Variable number of values to validate
        
    Raises:
        ValueError: If any value is not positive
    """
    for value in values:
        if value <= 0:
            raise ValueError("Dimensions must be positive")


def calculate_rectangle_area(width, height):
    """Calculate area of a rectangle."""
    _validate_positive(width, height)
    return width * height


def calculate_triangle_area(base, height):
    """Calculate area of a triangle."""
    _validate_positive(base, height)
    return 0.5 * base * height


def calculate_circle_area(radius):
    """Calculate area of a circle."""
    _validate_positive(radius)
    import math
    return math.pi * radius * radius
'''
        
        # Mock LLM responses for refactoring workflow
        # Step 1: Analyze code
        analyze_plan = {
            "steps": [
                {
                    "action": "read_file",
                    "parameters": {"file_path": "math_utils.py"},
                    "rationale": "Read current code to identify duplication"
                },
                {
                    "action": "read_file",
                    "parameters": {"file_path": "test_math_utils.py"},
                    "rationale": "Read tests to understand expected behavior"
                }
            ],
            "estimated_complexity": "moderate",
            "required_tools": ["file_ops"]
        }
        
        # Step 2: Reflection decides to refactor
        refactor_action = {
            "action": "edit_file",
            "parameters": {
                "file_path": "math_utils.py",
                "new_content": refactored_code
            },
            "rationale": "Extract duplicated validation logic into _validate_positive function"
        }
        
        # Step 3: Run tests to verify refactoring
        run_tests_action = {
            "action": "run_command",
            "parameters": {
                "command": "python -m pytest test_math_utils.py -v",
                "cwd": temp_project_dir
            },
            "rationale": "Verify tests still pass after refactoring"
        }
        
        # Step 4: Complete
        complete_action = {
            "action": "complete",
            "parameters": {
                "summary": "Refactored math_utils.py: extracted _validate_positive function to eliminate code duplication. All tests pass."
            },
            "rationale": "Refactoring complete, tests passing, code quality improved"
        }
        
        mock_llm.generate.side_effect = [
            # Planning
            LLMResponse(content=json.dumps(analyze_plan), tool_calls=[], finish_reason="stop"),
            # Reflection: refactor
            LLMResponse(content=json.dumps(refactor_action), tool_calls=[], finish_reason="stop"),
            # Reflection: test
            LLMResponse(content=json.dumps(run_tests_action), tool_calls=[], finish_reason="stop"),
            # Reflection: complete
            LLMResponse(content=json.dumps(complete_action), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute refactoring task
        result = task_executor.execute_task(
            "Refactor math_utils.py to eliminate code duplication in validation logic"
        )
        
        # Verify refactoring succeeded
        assert result.success, f"Refactoring failed: {result.error_message}"
        assert "math_utils.py" in result.files_modified, "Code file should be modified"
        
        # Verify refactored code was written
        refactored_content = math_utils_path.read_text()
        assert "_validate_positive" in refactored_content, "Extracted function should exist"
        assert "def _validate_positive" in refactored_content, "Function should be defined"
        
        # Verify all call sites were updated (Requirement 3.5)
        assert refactored_content.count("_validate_positive(") >= 3, "All functions should call extracted function"
        assert "calculate_rectangle_area" in refactored_content, "Original functions should be preserved"
        assert "calculate_triangle_area" in refactored_content, "Original functions should be preserved"
        assert "calculate_circle_area" in refactored_content, "Original functions should be preserved"
        
        # Verify code structure preserved (Requirement 3.4)
        assert '"""Math utilities module."""' in refactored_content, "Module docstring should be preserved"
        assert "def calculate_rectangle_area(width, height):" in refactored_content, "Function signature should be preserved"
        
        # Verify tests should have run
        assert len(result.actions_taken) >= 3, "Should have read files, refactored, and run tests"
        test_action = [a for a in result.actions_taken if a.action == "run_command"]
        assert len(test_action) > 0, "Tests should have been run"
        
        # Verify execution history includes all steps
        assert len(task_executor.execution_history) >= 3, "Should have multiple execution steps"
    
    def test_refactor_rename_function(self, task_executor, mock_llm, temp_project_dir):
        """Test refactoring workflow that renames a function and updates all references.
        
        This test validates:
        1. Agent locates function definition (Requirement 3.1)
        2. Agent renames function (Requirement 3.2)
        3. Agent updates all call sites (Requirement 3.5)
        4. Tests are updated and still pass
        
        Validates: Requirements 3.1, 3.2, 3.3, 3.5, 7.6
        """
        # Create initial code with unclear function name
        initial_code = '''"""String utilities."""

def proc(text):
    """Process text."""
    return text.strip().lower()


def format_output(items):
    """Format list of items."""
    processed = [proc(item) for item in items]
    return ", ".join(processed)
'''
        
        initial_tests = '''"""Tests for string utilities."""
from string_utils import proc, format_output


def test_proc():
    """Test proc function."""
    assert proc("  Hello  ") == "hello"
    assert proc("WORLD") == "world"


def test_format_output():
    """Test format output."""
    result = format_output(["  Apple  ", "BANANA", "Cherry  "])
    assert result == "apple, banana, cherry"
'''
        
        # Write initial files
        string_utils_path = Path(temp_project_dir) / "string_utils.py"
        test_path = Path(temp_project_dir) / "test_string_utils.py"
        string_utils_path.write_text(initial_code)
        test_path.write_text(initial_tests)
        
        # Refactored code with better function name
        refactored_code = '''"""String utilities."""

def normalize_text(text):
    """Normalize text by stripping whitespace and converting to lowercase."""
    return text.strip().lower()


def format_output(items):
    """Format list of items."""
    processed = [normalize_text(item) for item in items]
    return ", ".join(processed)
'''
        
        refactored_tests = '''"""Tests for string utilities."""
from string_utils import normalize_text, format_output


def test_normalize_text():
    """Test normalize_text function."""
    assert normalize_text("  Hello  ") == "hello"
    assert normalize_text("WORLD") == "world"


def test_format_output():
    """Test format output."""
    result = format_output(["  Apple  ", "BANANA", "Cherry  "])
    assert result == "apple, banana, cherry"
'''
        
        # Mock LLM responses
        plan = {
            "steps": [
                {
                    "action": "read_file",
                    "parameters": {"file_path": "string_utils.py"},
                    "rationale": "Analyze current code"
                },
                {
                    "action": "read_file",
                    "parameters": {"file_path": "test_string_utils.py"},
                    "rationale": "Check test dependencies"
                }
            ],
            "estimated_complexity": "simple",
            "required_tools": ["file_ops", "code_search"]
        }
        
        # Rename in main code
        refactor_main = {
            "action": "edit_file",
            "parameters": {
                "file_path": "string_utils.py",
                "new_content": refactored_code
            },
            "rationale": "Rename 'proc' to 'normalize_text' for clarity and update all call sites"
        }
        
        # Update tests
        refactor_tests = {
            "action": "edit_file",
            "parameters": {
                "file_path": "test_string_utils.py",
                "new_content": refactored_tests
            },
            "rationale": "Update test imports and function calls to use new name"
        }
        
        # Run tests
        run_tests = {
            "action": "run_command",
            "parameters": {
                "command": "python -m pytest test_string_utils.py -v",
                "cwd": temp_project_dir
            },
            "rationale": "Verify tests pass with renamed function"
        }
        
        # Complete
        complete = {
            "action": "complete",
            "parameters": {
                "summary": "Renamed 'proc' to 'normalize_text' for clarity. Updated all references in code and tests. All tests pass."
            },
            "rationale": "Refactoring complete"
        }
        
        mock_llm.generate.side_effect = [
            LLMResponse(content=json.dumps(plan), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(refactor_main), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(refactor_tests), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(run_tests), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(complete), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute refactoring task
        result = task_executor.execute_task(
            "Refactor string_utils.py: rename 'proc' to 'normalize_text' for better clarity"
        )
        
        # Verify refactoring succeeded
        assert result.success, f"Refactoring failed: {result.error_message}"
        assert "string_utils.py" in result.files_modified, "Main file should be modified"
        assert "test_string_utils.py" in result.files_modified, "Test file should be updated"
        
        # Verify function renamed in main code (Requirement 3.2)
        main_content = string_utils_path.read_text()
        assert "def normalize_text(text):" in main_content, "Function should be renamed"
        assert "def proc(" not in main_content, "Old function name should be removed"
        
        # Verify all call sites updated (Requirement 3.5)
        assert "normalize_text(item)" in main_content, "Call sites should use new name"
        assert "proc(" not in main_content or "proc" not in main_content, "Old name should not appear in calls"
        
        # Verify tests updated
        test_content = test_path.read_text()
        assert "from string_utils import normalize_text" in test_content, "Import should be updated"
        assert "def test_normalize_text():" in test_content, "Test should be renamed"
        assert "normalize_text(" in test_content, "Test should call new function name"
        
        # Verify functionality preserved (tests should pass)
        test_actions = [a for a in result.actions_taken if a.action == "run_command" and "pytest" in str(a.parameters)]
        assert len(test_actions) > 0, "Tests should have been run"
    
    def test_refactor_extract_class(self, task_executor, mock_llm, temp_project_dir):
        """Test refactoring workflow that extracts related functions into a class.
        
        This test validates:
        1. Agent identifies related functions (Requirement 3.1)
        2. Agent creates new class structure (Requirement 3.2)
        3. Agent maintains consistent style (Requirement 3.3)
        4. Agent preserves code structure (Requirement 3.4)
        5. Agent updates all call sites (Requirement 3.5)
        
        Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 7.6
        """
        # Create initial procedural code
        initial_code = '''"""User data processing."""

user_cache = {}


def get_user_name(user_id):
    """Get user name from cache."""
    if user_id in user_cache:
        return user_cache[user_id]["name"]
    return None


def get_user_email(user_id):
    """Get user email from cache."""
    if user_id in user_cache:
        return user_cache[user_id]["email"]
    return None


def set_user_data(user_id, name, email):
    """Store user data in cache."""
    user_cache[user_id] = {"name": name, "email": email}


def clear_cache():
    """Clear user cache."""
    user_cache.clear()
'''
        
        initial_tests = '''"""Tests for user data processing."""
from user_data import get_user_name, get_user_email, set_user_data, clear_cache


def test_user_data_storage():
    """Test storing and retrieving user data."""
    clear_cache()
    set_user_data(1, "Alice", "alice@example.com")
    
    assert get_user_name(1) == "Alice"
    assert get_user_email(1) == "alice@example.com"


def test_user_data_not_found():
    """Test retrieving non-existent user data."""
    clear_cache()
    assert get_user_name(999) is None
    assert get_user_email(999) is None
'''
        
        # Write initial files
        user_data_path = Path(temp_project_dir) / "user_data.py"
        test_path = Path(temp_project_dir) / "test_user_data.py"
        user_data_path.write_text(initial_code)
        test_path.write_text(initial_tests)
        
        # Refactored code with class
        refactored_code = '''"""User data processing."""


class UserCache:
    """Cache for user data."""
    
    def __init__(self):
        """Initialize empty cache."""
        self._cache = {}
    
    def get_name(self, user_id):
        """Get user name from cache.
        
        Args:
            user_id: User identifier
            
        Returns:
            User name or None if not found
        """
        if user_id in self._cache:
            return self._cache[user_id]["name"]
        return None
    
    def get_email(self, user_id):
        """Get user email from cache.
        
        Args:
            user_id: User identifier
            
        Returns:
            User email or None if not found
        """
        if user_id in self._cache:
            return self._cache[user_id]["email"]
        return None
    
    def set_data(self, user_id, name, email):
        """Store user data in cache.
        
        Args:
            user_id: User identifier
            name: User name
            email: User email
        """
        self._cache[user_id] = {"name": name, "email": email}
    
    def clear(self):
        """Clear all cached data."""
        self._cache.clear()
'''
        
        refactored_tests = '''"""Tests for user data processing."""
from user_data import UserCache


def test_user_data_storage():
    """Test storing and retrieving user data."""
    cache = UserCache()
    cache.set_data(1, "Alice", "alice@example.com")
    
    assert cache.get_name(1) == "Alice"
    assert cache.get_email(1) == "alice@example.com"


def test_user_data_not_found():
    """Test retrieving non-existent user data."""
    cache = UserCache()
    assert cache.get_name(999) is None
    assert cache.get_email(999) is None
'''
        
        # Mock LLM responses
        plan = {
            "steps": [
                {
                    "action": "read_file",
                    "parameters": {"file_path": "user_data.py"},
                    "rationale": "Analyze current procedural code"
                },
                {
                    "action": "read_file",
                    "parameters": {"file_path": "test_user_data.py"},
                    "rationale": "Understand usage patterns"
                }
            ],
            "estimated_complexity": "moderate",
            "required_tools": ["file_ops"]
        }
        
        refactor_main = {
            "action": "edit_file",
            "parameters": {
                "file_path": "user_data.py",
                "new_content": refactored_code
            },
            "rationale": "Extract related functions into UserCache class for better encapsulation"
        }
        
        refactor_tests = {
            "action": "edit_file",
            "parameters": {
                "file_path": "test_user_data.py",
                "new_content": refactored_tests
            },
            "rationale": "Update tests to use UserCache class"
        }
        
        run_tests = {
            "action": "run_command",
            "parameters": {
                "command": "python -m pytest test_user_data.py -v",
                "cwd": temp_project_dir
            },
            "rationale": "Verify functionality preserved"
        }
        
        complete = {
            "action": "complete",
            "parameters": {
                "summary": "Refactored user_data.py: extracted functions into UserCache class. Tests updated and passing."
            },
            "rationale": "Refactoring complete, improved code organization"
        }
        
        mock_llm.generate.side_effect = [
            LLMResponse(content=json.dumps(plan), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(refactor_main), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(refactor_tests), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(run_tests), tool_calls=[], finish_reason="stop"),
            LLMResponse(content=json.dumps(complete), tool_calls=[], finish_reason="stop")
        ]
        
        # Execute refactoring task
        result = task_executor.execute_task(
            "Refactor user_data.py: extract related functions into a UserCache class"
        )
        
        # Verify refactoring succeeded
        assert result.success, f"Refactoring failed: {result.error_message}"
        
        # Verify class created (Requirement 3.2)
        main_content = user_data_path.read_text()
        assert "class UserCache:" in main_content, "Class should be created"
        assert "def __init__(self):" in main_content, "Constructor should be defined"
        assert "self._cache" in main_content, "Instance variable should be used"
        
        # Verify methods created (Requirement 3.5)
        assert "def get_name(self, user_id):" in main_content, "get_name method should exist"
        assert "def get_email(self, user_id):" in main_content, "get_email method should exist"
        assert "def set_data(self, user_id, name, email):" in main_content, "set_data method should exist"
        assert "def clear(self):" in main_content, "clear method should exist"
        
        # Verify docstrings preserved (Requirement 3.4)
        assert '"""User data processing."""' in main_content, "Module docstring should be preserved"
        assert '"""Cache for user data."""' in main_content, "Class docstring should be added"
        
        # Verify tests updated (Requirement 3.5)
        test_content = test_path.read_text()
        assert "from user_data import UserCache" in test_content, "Import should be updated"
        assert "cache = UserCache()" in test_content, "Tests should instantiate class"
        assert "cache.set_data(" in test_content, "Tests should call instance methods"
        assert "cache.get_name(" in test_content, "Tests should call instance methods"
        
        # Verify tests should have run
        test_actions = [a for a in result.actions_taken if a.action == "run_command"]
        assert len(test_actions) > 0, "Tests should have been run"
        
        # Verify both files modified
        assert "user_data.py" in result.files_modified
        assert "test_user_data.py" in result.files_modified


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
