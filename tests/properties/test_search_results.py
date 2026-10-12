"""Property-based tests for search result structure.

This module tests Property 7: Search Result Structure
**Validates: Requirements 8.4**

The property ensures that all search results contain file path, line number,
and matching text, regardless of the search operation type.
"""

import os
import tempfile
import shutil
import uuid
from pathlib import Path
import sys

# Add src to path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest
from hypothesis import given, strategies as st, settings, assume

from agents.code_search import CodeSearch
from core.models import SearchResult, SymbolLocation


# Strategy for generating valid Python identifiers (function/class names)
@st.composite
def valid_identifier(draw):
    """Generate valid Python identifiers for function/class names."""
    # Start with a letter or underscore
    first = draw(st.sampled_from('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_'))
    # Continue with letters, digits, or underscores
    rest_length = draw(st.integers(min_value=0, max_value=20))
    rest_chars = st.sampled_from('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_')
    rest = ''.join([draw(rest_chars) for _ in range(rest_length)])
    return first + rest


# Strategy for generating Python code with functions and classes
@st.composite
def python_code_with_symbols(draw):
    """Generate Python code containing function and class definitions."""
    lines = []
    
    # Add some imports (optional)
    num_imports = draw(st.integers(min_value=0, max_value=3))
    for _ in range(num_imports):
        module = draw(valid_identifier())
        lines.append(f"import {module}")
    
    if lines:
        lines.append("")  # Blank line after imports
    
    # Add function definitions
    num_functions = draw(st.integers(min_value=1, max_value=5))
    for _ in range(num_functions):
        func_name = draw(valid_identifier())
        lines.append(f"def {func_name}():")
        lines.append("    pass")
        lines.append("")
    
    # Add class definitions
    num_classes = draw(st.integers(min_value=1, max_value=3))
    for _ in range(num_classes):
        class_name = draw(valid_identifier())
        lines.append(f"class {class_name}:")
        
        # Add some methods to the class
        num_methods = draw(st.integers(min_value=1, max_value=3))
        for _ in range(num_methods):
            method_name = draw(valid_identifier())
            lines.append(f"    def {method_name}(self):")
            lines.append("        pass")
            lines.append("")
        
        lines.append("")
    
    return '\n'.join(lines)


# Strategy for generating text content with patterns to search
@st.composite
def text_with_pattern(draw):
    """Generate text content and a pattern that appears in it."""
    # Generate a unique pattern that will definitely appear in the content
    pattern = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
        min_size=3,
        max_size=15
    ))
    assume(len(pattern) >= 3)  # Ensure pattern is meaningful
    
    # Generate lines of text
    num_lines = draw(st.integers(min_value=3, max_value=20))
    lines = []
    
    # Ensure pattern appears at least once
    pattern_line = draw(st.integers(min_value=0, max_value=num_lines - 1))
    
    for i in range(num_lines):
        if i == pattern_line:
            # This line contains the pattern
            prefix = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=0, max_size=10))
            suffix = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=0, max_size=10))
            lines.append(f"{prefix}{pattern}{suffix}")
        else:
            # Regular line without pattern
            line = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=0, max_size=50))
            lines.append(line)
    
    content = '\n'.join(lines)
    return content, pattern


@pytest.mark.property
class TestSearchResultStructure:
    """Property-based tests for search result structure.
    
    Tag: Feature: local-ai-dev-environment, Property 7: Search Result Structure
    """
    
    def setup_method(self):
        """Create a temporary directory for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.code_search = CodeSearch(project_root=self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary directory after each test method."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _create_test_file(self, filename: str, content: str) -> str:
        """Helper to create a test file and return its path."""
        filepath = os.path.join(self.temp_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    
    @given(content_and_pattern=text_with_pattern())
    @settings(max_examples=100, deadline=None)
    def test_search_text_result_structure(self, content_and_pattern):
        """Test that search_text results have required structure.
        
        **Validates: Requirements 8.4**
        
        Property: For any code search operation that returns results, each result
        SHALL contain a file path (absolute or relative), a line number (positive
        integer), and the matching text.
        
        Tag: Feature: local-ai-dev-environment, Property 7: Search Result Structure
        """
        content, pattern = content_and_pattern
        
        # Create a test file with the content
        filename = f"test_{uuid.uuid4().hex}.txt"
        filepath = self._create_test_file(filename, content)
        
        # Search for the pattern
        results = self.code_search.search_text(pattern)
        
        # If results are returned, verify structure
        if results:
            for result in results:
                # Verify result is a SearchResult instance
                assert isinstance(result, SearchResult), \
                    f"Result must be SearchResult instance, got {type(result)}"
                
                # Verify file_path exists and is a string
                assert hasattr(result, 'file_path'), "Result must have file_path attribute"
                assert isinstance(result.file_path, str), \
                    f"file_path must be string, got {type(result.file_path)}"
                assert len(result.file_path) > 0, "file_path must not be empty"
                
                # Verify line_number exists and is a positive integer
                assert hasattr(result, 'line_number'), "Result must have line_number attribute"
                assert isinstance(result.line_number, int), \
                    f"line_number must be integer, got {type(result.line_number)}"
                assert result.line_number > 0, \
                    f"line_number must be positive, got {result.line_number}"
                
                # Verify match_text exists and is a string
                assert hasattr(result, 'match_text'), "Result must have match_text attribute"
                assert isinstance(result.match_text, str), \
                    f"match_text must be string, got {type(result.match_text)}"
                
                # Verify the pattern actually appears in the match_text
                assert pattern in result.match_text, \
                    f"Pattern '{pattern}' not found in match_text '{result.match_text}'"
    
    @given(code=python_code_with_symbols())
    @settings(max_examples=100, deadline=None)
    def test_find_symbol_result_structure(self, code):
        """Test that find_symbol results have required structure.
        
        **Validates: Requirements 8.4**
        
        Property: For any symbol search operation that returns results, each result
        SHALL contain a file path (absolute or relative), a line number (positive
        integer), and the symbol name.
        
        Tag: Feature: local-ai-dev-environment, Property 7: Search Result Structure
        """
        # Create a Python file with the generated code
        filename = f"module_{uuid.uuid4().hex}.py"
        filepath = self._create_test_file(filename, code)
        
        # Extract function and class names from the code
        import re
        func_pattern = re.compile(r'def\s+(\w+)\s*\(')
        class_pattern = re.compile(r'class\s+(\w+)\s*[(:[]')
        
        func_names = func_pattern.findall(code)
        class_names = class_pattern.findall(code)
        
        all_symbols = func_names + class_names
        
        # Search for each symbol
        for symbol_name in all_symbols:
            results = self.code_search.find_symbol(symbol_name)
            
            # Verify at least one result is found
            assert len(results) > 0, \
                f"Expected to find symbol '{symbol_name}' in generated code"
            
            # Verify structure of each result
            for result in results:
                # Verify result is a SymbolLocation instance
                assert isinstance(result, SymbolLocation), \
                    f"Result must be SymbolLocation instance, got {type(result)}"
                
                # Verify file_path exists and is a string
                assert hasattr(result, 'file_path'), "Result must have file_path attribute"
                assert isinstance(result.file_path, str), \
                    f"file_path must be string, got {type(result.file_path)}"
                assert len(result.file_path) > 0, "file_path must not be empty"
                
                # Verify line_number exists and is a positive integer
                assert hasattr(result, 'line_number'), "Result must have line_number attribute"
                assert isinstance(result.line_number, int), \
                    f"line_number must be integer, got {type(result.line_number)}"
                assert result.line_number > 0, \
                    f"line_number must be positive, got {result.line_number}"
                
                # Verify symbol_name exists and matches what we searched for
                assert hasattr(result, 'symbol_name'), "Result must have symbol_name attribute"
                assert isinstance(result.symbol_name, str), \
                    f"symbol_name must be string, got {type(result.symbol_name)}"
                assert result.symbol_name == symbol_name, \
                    f"symbol_name must match search query: expected '{symbol_name}', got '{result.symbol_name}'"
                
                # Verify symbol_type exists and is valid
                assert hasattr(result, 'symbol_type'), "Result must have symbol_type attribute"
                assert isinstance(result.symbol_type, str), \
                    f"symbol_type must be string, got {type(result.symbol_type)}"
                assert result.symbol_type in ['function', 'class', 'method'], \
                    f"symbol_type must be function/class/method, got '{result.symbol_type}'"
    
    @given(
        pattern=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
            min_size=3,
            max_size=15
        ),
        num_files=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_search_across_multiple_files(self, pattern, num_files):
        """Test search result structure when searching across multiple files.
        
        **Validates: Requirements 8.4**
        
        Property: When searching across multiple files, all results must maintain
        the required structure with file paths, line numbers, and matching text.
        
        Tag: Feature: local-ai-dev-environment, Property 7: Search Result Structure
        """
        assume(len(pattern) >= 3)
        
        # Create multiple files with the pattern in each
        created_files = []
        for i in range(num_files):
            content = f"Line 1 with some text\nLine 2 contains {pattern} here\nLine 3 more text\n"
            filename = f"file_{i}_{uuid.uuid4().hex}.txt"
            filepath = self._create_test_file(filename, content)
            created_files.append(filepath)
        
        # Search for the pattern
        results = self.code_search.search_text(pattern)
        
        # Should find at least one match per file
        assert len(results) >= num_files, \
            f"Expected at least {num_files} results, got {len(results)}"
        
        # Verify structure of all results
        for result in results:
            # Verify all required fields exist and have correct types
            assert isinstance(result, SearchResult)
            assert isinstance(result.file_path, str)
            assert len(result.file_path) > 0
            assert isinstance(result.line_number, int)
            assert result.line_number > 0
            assert isinstance(result.match_text, str)
            assert pattern in result.match_text
            
            # Verify file_path refers to one of the created files
            result_path = Path(result.file_path)
            assert result_path.exists(), f"Result file path does not exist: {result.file_path}"
    
    @given(
        search_pattern=st.sampled_from([
            r'def\s+\w+',      # Function definitions
            r'class\s+\w+',    # Class definitions
            r'import\s+\w+',   # Import statements
            r'TODO|FIXME',     # Code comments
            r'\w+Error',       # Error classes
        ])
    )
    @settings(max_examples=100, deadline=None)
    def test_regex_search_result_structure(self, search_pattern):
        """Test search result structure with various regex patterns.
        
        **Validates: Requirements 8.4**
        
        Property: Search results must have the required structure regardless
        of the complexity or type of the search pattern (regex).
        
        Tag: Feature: local-ai-dev-environment, Property 7: Search Result Structure
        """
        # Create Python code that matches the patterns
        code = """
import os
import sys

def test_function():
    # TODO: implement this
    pass

class TestError(Exception):
    pass

class MyClass:
    def method_one(self):
        # FIXME: bug here
        pass
"""
        filename = f"test_{uuid.uuid4().hex}.py"
        filepath = self._create_test_file(filename, code)
        
        # Search with the regex pattern
        results = self.code_search.search_text(search_pattern, "*.py")
        
        # Verify structure of all results (if any found)
        for result in results:
            assert isinstance(result, SearchResult)
            assert isinstance(result.file_path, str)
            assert len(result.file_path) > 0
            assert isinstance(result.line_number, int)
            assert result.line_number > 0
            assert isinstance(result.match_text, str)
            assert len(result.match_text) > 0
    
    @given(
        func_name=valid_identifier(),
        class_name=valid_identifier()
    )
    @settings(max_examples=100, deadline=None)
    def test_empty_search_results_structure(self, func_name, class_name):
        """Test that empty search results are handled correctly.
        
        **Validates: Requirements 8.4**
        
        Property: When no matches are found, the search should return an empty
        list, not results with invalid structure.
        
        Tag: Feature: local-ai-dev-environment, Property 7: Search Result Structure
        """
        # Search for a symbol that doesn't exist
        nonexistent_symbol = f"NonExistent_{uuid.uuid4().hex}"
        results = self.code_search.find_symbol(nonexistent_symbol)
        
        # Should return empty list, not None or malformed results
        assert isinstance(results, list), "Results must be a list"
        assert len(results) == 0, "Should return empty list when no matches found"
        
        # Same for text search
        nonexistent_pattern = f"PATTERN_{uuid.uuid4().hex}_NOTFOUND"
        text_results = self.code_search.search_text(nonexistent_pattern)
        
        assert isinstance(text_results, list), "Text search results must be a list"
        assert len(text_results) == 0, "Should return empty list when no matches found"
    
    @given(code=python_code_with_symbols())
    @settings(max_examples=100, deadline=None)
    def test_line_number_accuracy(self, code):
        """Test that line numbers in results are accurate.
        
        **Validates: Requirements 8.4**
        
        Property: The line_number in each search result must correspond to the
        actual line where the match occurs in the file.
        
        Tag: Feature: local-ai-dev-environment, Property 7: Search Result Structure
        """
        # Create a Python file with unique name to avoid conflicts with other examples
        filename = f"module_{uuid.uuid4().hex}.py"
        filepath = self._create_test_file(filename, code)
        
        # Split code into lines for verification
        code_lines = code.split('\n')
        
        # Search for all function definitions - use specific filename to avoid 
        # finding results from other Hypothesis examples
        import re
        func_pattern = r'def\s+\w+'
        results = self.code_search.search_text(func_pattern, filename)
        
        # Verify each result's line number is accurate
        for result in results:
            # Line numbers are 1-indexed
            assert result.line_number >= 1
            assert result.line_number <= len(code_lines)
            
            # Get the actual line from the file
            actual_line = code_lines[result.line_number - 1]
            
            # The match_text should be present in the actual line (the regex may match 
            # a substring of the line, so we verify the line contains the pattern)
            # Instead of exact match, verify the regex pattern matches the actual line
            assert re.search(func_pattern, actual_line), \
                f"Line {result.line_number}: Pattern '{func_pattern}' not found in '{actual_line}'"
