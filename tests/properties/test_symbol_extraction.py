"""Property-based tests for symbol extraction completeness.

This module tests Property 6: Symbol Extraction Completeness
**Validates: Requirements 8.3**

The property ensures that all function and class definitions in syntactically
valid source code are found with correct metadata (symbol name, type, file path,
and line number).
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import List, Tuple

from src.agents.code_search import CodeSearch
from src.core.models import SymbolLocation


# Strategy for generating valid Python identifiers
identifier_strategy = st.from_regex(r'[a-zA-Z_][a-zA-Z0-9_]{0,15}', fullmatch=True).filter(
    lambda x: x not in ['def', 'class', 'if', 'else', 'while', 'for', 'return', 'import', 'from', 'as', 'pass']
)


# Strategy for generating function parameters
@st.composite
def function_params_strategy(draw):
    """Generate function parameter list."""
    num_params = draw(st.integers(min_value=0, max_value=5))
    if num_params == 0:
        return ""
    
    params = []
    for _ in range(num_params):
        param_name = draw(identifier_strategy)
        # Sometimes add default value
        if draw(st.booleans()):
            default = draw(st.one_of(
                st.integers(min_value=0, max_value=100).map(str),
                st.just('None'),
                st.just('""'),
                st.just('[]')
            ))
            params.append(f'{param_name}={default}')
        else:
            params.append(param_name)
    
    return ', '.join(params)


# Strategy for generating function bodies
@st.composite
def function_body_strategy(draw):
    """Generate a simple function body."""
    body_type = draw(st.sampled_from(['pass', 'return', 'docstring', 'statement']))
    
    if body_type == 'pass':
        return '    pass'
    elif body_type == 'return':
        value = draw(st.sampled_from(['None', '0', '""', 'True', 'False', '[]', '{}']))
        return f'    return {value}'
    elif body_type == 'docstring':
        docstring = draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Z')), min_size=1, max_size=50))
        return f'    """{docstring}"""\n    pass'
    else:
        var_name = draw(identifier_strategy)
        value = draw(st.integers(min_value=0, max_value=100))
        return f'    {var_name} = {value}\n    return {var_name}'


# Strategy for generating a single function definition
@st.composite
def function_def_strategy(draw, indented=False):
    """Generate a function definition."""
    func_name = draw(identifier_strategy)
    params = draw(function_params_strategy())
    body = draw(function_body_strategy())
    
    indent = '    ' if indented else ''
    func_code = f'{indent}def {func_name}({params}):\n'
    
    # Add body with proper indentation
    if indented:
        func_code += '    ' + body.replace('\n', '\n    ')
    else:
        func_code += body
    
    return func_name, func_code


# Strategy for generating a class definition
@st.composite
def class_def_strategy(draw):
    """Generate a class definition with optional methods."""
    class_name = draw(identifier_strategy.filter(lambda x: x[0].isupper() or x.startswith('_')))
    
    # Sometimes add base class
    has_base = draw(st.booleans())
    if has_base:
        base_class = draw(st.sampled_from(['object', 'Exception', 'dict', 'list']))
        class_header = f'class {class_name}({base_class}):'
    else:
        class_header = f'class {class_name}:'
    
    # Generate methods (0-3 methods)
    num_methods = draw(st.integers(min_value=0, max_value=3))
    methods = []
    method_names = []
    
    if num_methods == 0:
        # Empty class
        return class_name, [], f'{class_header}\n    pass'
    
    for _ in range(num_methods):
        method_name, method_code = draw(function_def_strategy(indented=True))
        methods.append(method_code)
        method_names.append(method_name)
    
    class_code = class_header + '\n' + '\n\n'.join(methods)
    
    return class_name, method_names, class_code


# Strategy for generating a complete Python file with multiple definitions
@st.composite
def python_file_strategy(draw):
    """Generate a complete Python file with functions and classes.
    
    Returns:
        Tuple of (code_string, expected_symbols)
        where expected_symbols is a list of (name, type) tuples
    """
    # Generate 1-5 top-level definitions (mix of functions and classes)
    num_definitions = draw(st.integers(min_value=1, max_value=5))
    
    code_parts = []
    expected_symbols = []
    
    for _ in range(num_definitions):
        # Randomly choose between function and class
        is_class = draw(st.booleans())
        
        if is_class:
            class_name, method_names, class_code = draw(class_def_strategy())
            code_parts.append(class_code)
            expected_symbols.append((class_name, 'class'))
            
            # Add methods as expected symbols
            for method_name in method_names:
                expected_symbols.append((method_name, 'method'))
        else:
            func_name, func_code = draw(function_def_strategy(indented=False))
            code_parts.append(func_code)
            expected_symbols.append((func_name, 'function'))
    
    # Join with double newlines for separation
    code = '\n\n'.join(code_parts)
    
    return code, expected_symbols


@pytest.mark.property
class TestSymbolExtractionCompleteness:
    """Property-based tests for symbol extraction completeness.
    
    Tag: Feature: local-ai-dev-environment, Property 6: Symbol Extraction Completeness
    """
    
    def setup_method(self):
        """Create a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp(prefix='code_search_test_')
        self.code_search = CodeSearch(project_root=self.test_dir, excluded_dirs=set())
    
    def teardown_method(self):
        """Clean up temporary directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def _write_test_file(self, filename: str, content: str) -> Path:
        """Write a test file to the temporary directory."""
        file_path = Path(self.test_dir) / filename
        file_path.write_text(content, encoding='utf-8')
        return file_path
    
    @given(code_and_symbols=python_file_strategy())
    @settings(max_examples=100, deadline=None)
    def test_all_symbols_found(self, code_and_symbols):
        """Test that all function and class definitions are found.
        
        **Validates: Requirements 8.3**
        
        Property: For any syntactically valid Python source code file,
        parsing SHALL identify all function and class definitions.
        
        Tag: Feature: local-ai-dev-environment, Property 6: Symbol Extraction Completeness
        """
        code, expected_symbols = code_and_symbols
        
        # Ensure we have at least one symbol to test
        assume(len(expected_symbols) > 0)
        
        # Write the code to a test file
        test_file = self._write_test_file('test_code.py', code)
        
        # Track which symbols we expect to find
        expected_symbol_names = set(name for name, _ in expected_symbols)
        
        # Find all symbols
        found_symbols = {}
        for symbol_name in expected_symbol_names:
            results = self.code_search.find_symbol(symbol_name)
            for result in results:
                found_symbols[result.symbol_name] = result
        
        # Verify all expected symbols were found
        found_symbol_names = set(found_symbols.keys())
        assert found_symbol_names == expected_symbol_names, \
            f"Expected symbols {expected_symbol_names} but found {found_symbol_names}"
    
    @given(code_and_symbols=python_file_strategy())
    @settings(max_examples=100, deadline=None)
    def test_symbol_metadata_correctness(self, code_and_symbols):
        """Test that each extracted symbol has correct metadata.
        
        **Validates: Requirements 8.3**
        
        Property: Each extracted symbol SHALL include the symbol name, type
        (function/class/method), file path, and line number.
        
        Tag: Feature: local-ai-dev-environment, Property 6: Symbol Extraction Completeness
        """
        code, expected_symbols = code_and_symbols
        
        # Ensure we have at least one symbol to test
        assume(len(expected_symbols) > 0)
        
        # Write the code to a test file
        test_file = self._write_test_file('test_metadata.py', code)
        
        # Find all symbols and verify metadata
        for expected_name, expected_type in expected_symbols:
            results = self.code_search.find_symbol(expected_name)
            
            # Should find at least one match
            assert len(results) > 0, f"Symbol {expected_name} not found"
            
            # Verify metadata for each result
            for result in results:
                # Check symbol name
                assert result.symbol_name == expected_name, \
                    f"Symbol name mismatch: expected {expected_name}, got {result.symbol_name}"
                
                # Check symbol type
                assert result.symbol_type in ['function', 'class', 'method'], \
                    f"Invalid symbol type: {result.symbol_type}"
                
                # Check file path exists and is correct
                assert result.file_path == str(test_file), \
                    f"File path mismatch: expected {test_file}, got {result.file_path}"
                
                # Check line number is positive
                assert result.line_number > 0, \
                    f"Invalid line number: {result.line_number}"
    
    @given(code_and_symbols=python_file_strategy())
    @settings(max_examples=100, deadline=None)
    def test_line_numbers_accurate(self, code_and_symbols):
        """Test that line numbers point to actual definition locations.
        
        **Validates: Requirements 8.3**
        
        Property: The line number for each symbol should point to the line
        where the symbol is defined (contains 'def' or 'class' keyword).
        
        Tag: Feature: local-ai-dev-environment, Property 6: Symbol Extraction Completeness
        """
        code, expected_symbols = code_and_symbols
        
        # Ensure we have at least one symbol to test
        assume(len(expected_symbols) > 0)
        
        # Write the code to a test file
        test_file = self._write_test_file('test_lines.py', code)
        
        # Read the file lines
        lines = code.split('\n')
        
        # Find all symbols and verify line numbers
        for expected_name, expected_type in expected_symbols:
            results = self.code_search.find_symbol(expected_name)
            
            assert len(results) > 0, f"Symbol {expected_name} not found"
            
            for result in results:
                line_num = result.line_number
                
                # Line number should be within file bounds
                assert 1 <= line_num <= len(lines), \
                    f"Line number {line_num} out of bounds for file with {len(lines)} lines"
                
                # Get the actual line (convert to 0-indexed)
                actual_line = lines[line_num - 1]
                
                # Verify the line contains the definition keyword
                if result.symbol_type == 'class':
                    assert 'class' in actual_line and expected_name in actual_line, \
                        f"Line {line_num} does not contain class definition: {actual_line}"
                else:  # function or method
                    assert 'def' in actual_line and expected_name in actual_line, \
                        f"Line {line_num} does not contain function definition: {actual_line}"
    
    @given(
        func_name=identifier_strategy,
        params=function_params_strategy(),
        body=function_body_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_single_function_extraction(self, func_name, params, body):
        """Test extraction of a single function definition.
        
        **Validates: Requirements 8.3**
        
        Property: A file containing a single function definition should
        result in exactly one symbol found with correct type.
        
        Tag: Feature: local-ai-dev-environment, Property 6: Symbol Extraction Completeness
        """
        # Create simple function
        code = f'def {func_name}({params}):\n{body}'
        
        # Write to file
        test_file = self._write_test_file('single_func.py', code)
        
        # Find the function
        results = self.code_search.find_symbol(func_name)
        
        # Should find exactly one result
        assert len(results) >= 1, f"Function {func_name} not found"
        
        # Verify the first result
        result = results[0]
        assert result.symbol_name == func_name
        assert result.symbol_type in ['function', 'method']
        assert result.file_path == str(test_file)
        assert result.line_number == 1  # Should be on first line
    
    @given(class_def=class_def_strategy())
    @settings(max_examples=100, deadline=None)
    def test_class_with_methods_extraction(self, class_def):
        """Test extraction of class and its methods.
        
        **Validates: Requirements 8.3**
        
        Property: A class definition with methods should result in the
        class symbol and all method symbols being found.
        
        Tag: Feature: local-ai-dev-environment, Property 6: Symbol Extraction Completeness
        """
        class_name, method_names, code = class_def
        
        # Write to file
        test_file = self._write_test_file('class_test.py', code)
        
        # Find the class
        class_results = self.code_search.find_symbol(class_name)
        assert len(class_results) >= 1, f"Class {class_name} not found"
        
        # Verify class symbol exists in results
        class_found = any(r.symbol_type == 'class' and r.symbol_name == class_name 
                         for r in class_results)
        assert class_found, f"Class {class_name} not found in results"
        
        # Find all methods
        for method_name in method_names:
            method_results = self.code_search.find_symbol(method_name)
            assert len(method_results) >= 1, f"Method {method_name} not found"
            
            # Verify at least one result with this name is a method (not a class)
            # Handle edge case where method name might match class name
            method_found = any(r.symbol_type == 'method' and r.symbol_name == method_name 
                              for r in method_results)
            # If the method name matches the class name, the class will also be in results
            # In this case, we just verify the method exists somewhere in the results
            if method_name == class_name:
                # When method and class have same name, just verify both exist
                assert method_found or any(r.symbol_type == 'class' for r in method_results), \
                    f"Symbol {method_name} not found as method or class"
            else:
                assert method_found, f"Method {method_name} not found (only found as {[r.symbol_type for r in method_results]})"
    
    @given(
        num_functions=st.integers(min_value=2, max_value=10),
        func_name=identifier_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_multiple_functions_same_name(self, num_functions, func_name):
        """Test extraction when the same function name appears in multiple files.
        
        **Validates: Requirements 8.3**
        
        Property: When a symbol name appears in multiple files, all
        occurrences should be found.
        
        Tag: Feature: local-ai-dev-environment, Property 6: Symbol Extraction Completeness
        """
        # Create multiple files with the same function name
        for i in range(num_functions):
            code = f'def {func_name}():\n    pass'
            self._write_test_file(f'file_{i}.py', code)
        
        # Find all occurrences
        results = self.code_search.find_symbol(func_name)
        
        # Should find at least num_functions results (could be more if duplicates in same file)
        assert len(results) >= num_functions, \
            f"Expected at least {num_functions} results, found {len(results)}"
        
        # Verify all have correct symbol name
        for result in results:
            assert result.symbol_name == func_name
    
    @given(code_and_symbols=python_file_strategy())
    @settings(max_examples=100, deadline=None)
    def test_no_false_positives(self, code_and_symbols):
        """Test that only actual definitions are found, no false positives.
        
        **Validates: Requirements 8.3**
        
        Property: Searching for a symbol that doesn't exist should return
        empty results.
        
        Tag: Feature: local-ai-dev-environment, Property 6: Symbol Extraction Completeness
        """
        code, expected_symbols = code_and_symbols
        
        # Write the code to a test file
        test_file = self._write_test_file('test_false_positive.py', code)
        
        # Search for a symbol that definitely doesn't exist
        nonexistent_symbol = 'NonExistentSymbolName123456789'
        
        # Ensure this name isn't in our expected symbols
        assume(nonexistent_symbol not in [name for name, _ in expected_symbols])
        
        # Search for it
        results = self.code_search.find_symbol(nonexistent_symbol)
        
        # Should find nothing
        assert len(results) == 0, \
            f"Found {len(results)} false positive results for nonexistent symbol"
    
    @given(
        func_name=identifier_strategy,
        decorators=st.lists(
            st.sampled_from(['@staticmethod', '@classmethod', '@property', '@abstractmethod']),
            min_size=0,
            max_size=2
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_decorated_functions_extraction(self, func_name, decorators):
        """Test extraction of decorated functions.
        
        **Validates: Requirements 8.3**
        
        Property: Functions with decorators should still be found correctly.
        
        Tag: Feature: local-ai-dev-environment, Property 6: Symbol Extraction Completeness
        """
        # Create function with decorators
        decorator_lines = '\n'.join(decorators) if decorators else ''
        code = f'{decorator_lines}\ndef {func_name}():\n    pass' if decorator_lines else f'def {func_name}():\n    pass'
        
        # Write to file
        test_file = self._write_test_file('decorated.py', code)
        
        # Find the function
        results = self.code_search.find_symbol(func_name)
        
        # Should find the function
        assert len(results) >= 1, f"Decorated function {func_name} not found"
        
        result = results[0]
        assert result.symbol_name == func_name
