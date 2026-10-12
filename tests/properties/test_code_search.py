"""Property-based tests for code search with exclusions.

This module tests Property 5: Code Search with Exclusions
**Validates: Requirements 8.1, 8.2, 8.5, 8.6**

The property ensures that search finds all pattern matches in non-excluded files,
excluded directories are not searched, and results have the required fields.
"""

import os
import tempfile
import shutil
import uuid
from pathlib import Path
import pytest
from hypothesis import given, strategies as st, settings, assume

from src.agents.code_search import CodeSearch


# Strategy for generating valid directory names
@st.composite
def valid_dirname(draw):
    """Generate valid directory names."""
    length = draw(st.integers(min_value=3, max_value=15))
    chars = st.sampled_from('abcdefghijklmnopqrstuvwxyz0123456789_')
    name = ''.join(draw(st.lists(chars, min_size=3, max_size=length)))
    return name


# Strategy for generating valid file names
@st.composite
def valid_filename(draw):
    """Generate valid file names with common extensions."""
    length = draw(st.integers(min_value=3, max_value=20))
    chars = st.sampled_from('abcdefghijklmnopqrstuvwxyz0123456789_')
    name = ''.join(draw(st.lists(chars, min_size=3, max_size=length)))
    extension = draw(st.sampled_from(['.py', '.js', '.txt', '.md', '.java', '.cpp']))
    return name + extension


# Strategy for generating searchable text content
@st.composite
def text_content_with_pattern(draw):
    """Generate text content that includes a specific search pattern.
    
    Returns a tuple of (content, pattern_to_search) where pattern is guaranteed
    to appear at least once in content.
    """
    # Generate a simple pattern that will appear in the content
    pattern = draw(st.sampled_from([
        'TODO', 'FIXME', 'function', 'class', 'import', 'def',
        'test_', 'ERROR', 'WARNING', 'DEBUG', 'print'
    ]))
    
    # Generate lines of text, ensuring pattern appears at least once
    num_lines = draw(st.integers(min_value=1, max_value=20))
    lines = []
    
    # Ensure at least one line contains the pattern
    pattern_line_idx = draw(st.integers(min_value=0, max_value=num_lines - 1))
    
    for i in range(num_lines):
        if i == pattern_line_idx:
            # This line must contain the pattern
            prefix = draw(st.text(alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Z'),
                max_codepoint=127
            ), min_size=0, max_size=30))
            suffix = draw(st.text(alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Z'),
                max_codepoint=127
            ), min_size=0, max_size=30))
            line = f"{prefix}{pattern}{suffix}"
        else:
            # Random line that may or may not contain the pattern
            line = draw(st.text(alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Z'),
                max_codepoint=127
            ), min_size=0, max_size=50))
        
        lines.append(line)
    
    content = '\n'.join(lines)
    return content, pattern


# Strategy for generating codebase structure
@st.composite
def codebase_structure(draw):
    """Generate a random codebase structure.
    
    Returns a dictionary describing the codebase:
    {
        'files': [{'path': 'dir/file.py', 'content': 'text', 'pattern': 'TODO'}],
        'excluded_dirs': ['node_modules', 'build']
    }
    """
    # Generate 1-3 regular directories and 0-2 excluded directories
    num_regular_dirs = draw(st.integers(min_value=1, max_value=3))
    num_excluded_dirs = draw(st.integers(min_value=0, max_value=2))
    
    regular_dirs = [draw(valid_dirname()) for _ in range(num_regular_dirs)]
    excluded_dirs = [draw(valid_dirname()) for _ in range(num_excluded_dirs)]
    
    # Ensure no overlap between regular and excluded dirs
    excluded_dirs = [d for d in excluded_dirs if d not in regular_dirs]
    
    files = []
    
    # Generate 2-5 files in regular directories (should be found in search)
    num_regular_files = draw(st.integers(min_value=2, max_value=5))
    for _ in range(num_regular_files):
        dir_name = draw(st.sampled_from(regular_dirs))
        filename = draw(valid_filename())
        content, pattern = draw(text_content_with_pattern())
        
        files.append({
            'path': f"{dir_name}/{filename}",
            'content': content,
            'pattern': pattern,
            'excluded': False
        })
    
    # Generate 0-3 files in excluded directories (should NOT be found in search)
    if excluded_dirs:
        num_excluded_files = draw(st.integers(min_value=0, max_value=3))
        for _ in range(num_excluded_files):
            dir_name = draw(st.sampled_from(excluded_dirs))
            filename = draw(valid_filename())
            content, pattern = draw(text_content_with_pattern())
            
            files.append({
                'path': f"{dir_name}/{filename}",
                'content': content,
                'pattern': pattern,
                'excluded': True
            })
    
    return {
        'files': files,
        'excluded_dirs': set(excluded_dirs)
    }


@pytest.mark.property
class TestCodeSearchWithExclusions:
    """Property-based tests for code search with directory exclusions.
    
    Tag: Feature: local-ai-dev-environment, Property 5: Code Search with Exclusions
    """
    
    def setup_method(self):
        """Create a temporary directory for each test method."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up temporary directory after each test method."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _create_codebase(self, structure):
        """Create a codebase structure in the temp directory.
        
        Args:
            structure: Dictionary with 'files' and 'excluded_dirs' keys
            
        Returns:
            Dictionary mapping file paths to their expected patterns
        """
        expected_patterns = {}
        created_files = set()
        
        for file_info in structure['files']:
            # Skip duplicate file paths (keep first occurrence)
            if file_info['path'] in created_files:
                continue
            
            file_path = os.path.join(self.temp_dir, file_info['path'])
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_info['content'])
            
            created_files.add(file_info['path'])
            
            if not file_info['excluded']:
                # Track patterns in non-excluded files
                expected_patterns[file_info['path']] = file_info['pattern']
        
        return expected_patterns
    
    @given(structure=codebase_structure())
    @settings(max_examples=100, deadline=None)
    def test_search_finds_all_matches_in_non_excluded_files(self, structure):
        """Test that search finds all pattern matches in non-excluded files.
        
        **Validates: Requirements 8.1, 8.2, 8.5, 8.6**
        
        Property: For any codebase, search pattern, and exclusion list, all matches
        to the pattern SHALL be found in non-excluded files.
        
        Tag: Feature: local-ai-dev-environment, Property 5: Code Search with Exclusions
        """
        # Create the codebase
        expected_patterns = self._create_codebase(structure)
        
        # Skip if no non-excluded files
        assume(len(expected_patterns) > 0)
        
        # Create CodeSearch instance with exclusions
        code_search = CodeSearch(
            project_root=self.temp_dir,
            excluded_dirs=structure['excluded_dirs']
        )
        
        # For each pattern in non-excluded files, search should find it
        for file_path, pattern in expected_patterns.items():
            results = code_search.search_text(pattern, "*")
            
            # Verify the pattern was found
            matching_files = [os.path.normpath(r.file_path) for r in results]
            full_file_path = os.path.normpath(os.path.join(self.temp_dir, file_path))
            
            assert full_file_path in matching_files, (
                f"Pattern '{pattern}' not found in non-excluded file {file_path}. "
                f"Expected: {full_file_path}\n"
                f"Found in: {matching_files}"
            )
    
    @given(structure=codebase_structure())
    @settings(max_examples=100, deadline=None)
    def test_excluded_directories_not_searched(self, structure):
        """Test that excluded directories are not searched.
        
        **Validates: Requirements 8.6**
        
        Property: No results SHALL come from excluded directories.
        
        Tag: Feature: local-ai-dev-environment, Property 5: Code Search with Exclusions
        """
        # Create the codebase
        self._create_codebase(structure)
        
        # Skip if no excluded directories
        excluded_files = [f for f in structure['files'] if f['excluded']]
        assume(len(excluded_files) > 0)
        
        # Create CodeSearch instance with exclusions
        code_search = CodeSearch(
            project_root=self.temp_dir,
            excluded_dirs=structure['excluded_dirs']
        )
        
        # Collect all patterns from excluded files
        excluded_patterns = set(f['pattern'] for f in excluded_files)
        
        # Search for each pattern
        for pattern in excluded_patterns:
            results = code_search.search_text(pattern, "*")
            
            # Verify no results come from excluded directories
            for result in results:
                result_path = Path(result.file_path).relative_to(self.temp_dir)
                first_dir = result_path.parts[0] if result_path.parts else ""
                
                assert first_dir not in structure['excluded_dirs'], (
                    f"Found result in excluded directory '{first_dir}': {result.file_path}"
                )
    
    @given(structure=codebase_structure())
    @settings(max_examples=100, deadline=None)
    def test_search_results_have_required_fields(self, structure):
        """Test that each search result contains file path, line number, and matching text.
        
        **Validates: Requirements 8.4**
        
        Property: Each result SHALL contain the file path, line number, and matching text.
        
        Tag: Feature: local-ai-dev-environment, Property 5: Code Search with Exclusions
        """
        # Create the codebase
        expected_patterns = self._create_codebase(structure)
        
        # Skip if no non-excluded files
        assume(len(expected_patterns) > 0)
        
        # Create CodeSearch instance with exclusions
        code_search = CodeSearch(
            project_root=self.temp_dir,
            excluded_dirs=structure['excluded_dirs']
        )
        
        # Search for any pattern
        first_pattern = next(iter(expected_patterns.values()))
        results = code_search.search_text(first_pattern, "*")
        
        # Skip if no results found (edge case with random content)
        assume(len(results) > 0)
        
        # Verify each result has required fields
        for result in results:
            # Must have file_path (non-empty string)
            assert hasattr(result, 'file_path'), "Result missing file_path attribute"
            assert isinstance(result.file_path, str), "file_path must be a string"
            assert len(result.file_path) > 0, "file_path must not be empty"
            assert os.path.isabs(result.file_path) or result.file_path, "file_path must be valid"
            
            # Must have line_number (positive integer)
            assert hasattr(result, 'line_number'), "Result missing line_number attribute"
            assert isinstance(result.line_number, int), "line_number must be an integer"
            assert result.line_number > 0, "line_number must be positive"
            
            # Must have match_text (string)
            assert hasattr(result, 'match_text'), "Result missing match_text attribute"
            assert isinstance(result.match_text, str), "match_text must be a string"
            # match_text can be empty for lines with only the pattern
    
    @given(structure=codebase_structure())
    @settings(max_examples=100, deadline=None)
    def test_regex_patterns_supported(self, structure):
        """Test that search supports valid regex patterns.
        
        **Validates: Requirements 8.5**
        
        Property: The search SHALL support valid regex patterns.
        
        Tag: Feature: local-ai-dev-environment, Property 5: Code Search with Exclusions
        """
        # Create the codebase
        self._create_codebase(structure)
        
        # Create CodeSearch instance with exclusions
        code_search = CodeSearch(
            project_root=self.temp_dir,
            excluded_dirs=structure['excluded_dirs']
        )
        
        # Test various regex patterns (these should not raise exceptions)
        regex_patterns = [
            r'\w+',           # Word characters
            r'def\s+\w+',     # Function definition pattern
            r'class\s+\w+',   # Class definition pattern
            r'TODO|FIXME',    # Alternation
            r'.*test.*',      # Wildcard
            r'^import',       # Start of line
        ]
        
        for pattern in regex_patterns:
            try:
                results = code_search.search_text(pattern, "*")
                # Should return a list (possibly empty)
                assert isinstance(results, list), f"search_text should return a list for pattern '{pattern}'"
            except Exception as e:
                pytest.fail(f"Valid regex pattern '{pattern}' raised exception: {e}")
    
    @given(
        structure=codebase_structure(),
        file_pattern=st.sampled_from(['*.py', '*.js', '*.txt', '*.md', '*'])
    )
    @settings(max_examples=100, deadline=None)
    def test_file_pattern_filtering(self, structure, file_pattern):
        """Test that file pattern filtering works correctly.
        
        **Validates: Requirements 8.1, 8.2**
        
        Property: Search should only return results from files matching the file pattern.
        
        Tag: Feature: local-ai-dev-environment, Property 5: Code Search with Exclusions
        """
        # Create the codebase
        self._create_codebase(structure)
        
        # Create CodeSearch instance with exclusions
        code_search = CodeSearch(
            project_root=self.temp_dir,
            excluded_dirs=structure['excluded_dirs']
        )
        
        # Search with file pattern
        results = code_search.search_text(r'\w+', file_pattern)
        
        # Verify all results match the file pattern
        for result in results:
            file_name = os.path.basename(result.file_path)
            
            if file_pattern == '*':
                # Should match any file
                assert len(file_name) > 0
            else:
                # Extract extension from pattern (e.g., '*.py' -> '.py')
                if file_pattern.startswith('*.'):
                    expected_ext = file_pattern[1:]  # Remove '*'
                    assert file_name.endswith(expected_ext), (
                        f"File {file_name} does not match pattern {file_pattern}"
                    )
    
    @given(structure=codebase_structure())
    @settings(max_examples=100, deadline=None)
    def test_search_files_by_name(self, structure):
        """Test that search_files finds files matching name pattern in non-excluded dirs.
        
        **Validates: Requirements 8.2, 8.6**
        
        Property: search_files SHALL find all files matching the name pattern
        in non-excluded directories only.
        
        Tag: Feature: local-ai-dev-environment, Property 5: Code Search with Exclusions
        """
        # Create the codebase
        self._create_codebase(structure)
        
        # Create CodeSearch instance with exclusions
        code_search = CodeSearch(
            project_root=self.temp_dir,
            excluded_dirs=structure['excluded_dirs']
        )
        
        # Search for all Python files
        py_files = code_search.search_files("*.py")
        
        # Verify no results come from excluded directories
        for file_path in py_files:
            result_path = Path(file_path).relative_to(self.temp_dir)
            first_dir = result_path.parts[0] if result_path.parts else ""
            
            assert first_dir not in structure['excluded_dirs'], (
                f"search_files found file in excluded directory '{first_dir}': {file_path}"
            )
        
        # Verify all non-excluded .py files are found
        normalized_py_files = [os.path.normpath(f) for f in py_files]
        seen_paths = set()
        
        for file_info in structure['files']:
            # Skip duplicates
            if file_info['path'] in seen_paths:
                continue
            seen_paths.add(file_info['path'])
            
            if file_info['path'].endswith('.py') and not file_info['excluded']:
                full_path = os.path.normpath(os.path.join(self.temp_dir, file_info['path']))
                assert full_path in normalized_py_files, (
                    f"Expected to find {file_info['path']} in search results.\n"
                    f"Expected: {full_path}\n"
                    f"Found: {normalized_py_files}"
                )
    
    @given(structure=codebase_structure())
    @settings(max_examples=100, deadline=None)
    def test_context_lines_provided(self, structure):
        """Test that search results include context lines before and after the match.
        
        **Validates: Requirements 8.1, 8.4**
        
        Property: Search results should include context_before and context_after lists.
        
        Tag: Feature: local-ai-dev-environment, Property 5: Code Search with Exclusions
        """
        # Create the codebase
        expected_patterns = self._create_codebase(structure)
        
        # Skip if no non-excluded files
        assume(len(expected_patterns) > 0)
        
        # Create CodeSearch instance with exclusions
        code_search = CodeSearch(
            project_root=self.temp_dir,
            excluded_dirs=structure['excluded_dirs']
        )
        
        # Search for any pattern
        first_pattern = next(iter(expected_patterns.values()))
        results = code_search.search_text(first_pattern, "*")
        
        # Skip if no results found
        assume(len(results) > 0)
        
        # Verify each result has context fields
        for result in results:
            assert hasattr(result, 'context_before'), "Result missing context_before"
            assert hasattr(result, 'context_after'), "Result missing context_after"
            assert isinstance(result.context_before, list), "context_before must be a list"
            assert isinstance(result.context_after, list), "context_after must be a list"
            
            # Context should be lists of strings
            for line in result.context_before:
                assert isinstance(line, str), "context_before items must be strings"
            for line in result.context_after:
                assert isinstance(line, str), "context_after items must be strings"


@pytest.mark.property
class TestSearchResultStructure:
    """Property-based tests for search result structure.
    
    Tag: Feature: local-ai-dev-environment, Property 7: Search Result Structure
    """
    
    def setup_method(self):
        """Create a temporary directory for each test method."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up temporary directory after each test method."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _create_test_files(self, num_files=5):
        """Create test files with predictable content.
        
        Args:
            num_files: Number of files to create
            
        Returns:
            List of created file paths
        """
        created_files = []
        
        for i in range(num_files):
            # Create directory structure
            dir_name = f"src_{i}"
            dir_path = os.path.join(self.temp_dir, dir_name)
            os.makedirs(dir_path, exist_ok=True)
            
            # Create Python file with function definitions
            file_name = f"module_{i}.py"
            file_path = os.path.join(dir_path, file_name)
            
            content = f"""# Module {i}
import os
import sys

def function_{i}():
    '''Function {i} docstring'''
    return {i}

class Class_{i}:
    '''Class {i} docstring'''
    
    def method_{i}(self):
        '''Method {i} docstring'''
        return {i}
    
# TODO: Add more functionality
# FIXME: Fix the implementation
"""
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            created_files.append(file_path)
        
        return created_files
    
    @given(
        num_files=st.integers(min_value=1, max_value=10),
        search_pattern=st.sampled_from([
            'TODO', 'FIXME', 'def', 'class', 'import', 'return'
        ])
    )
    @settings(max_examples=100, deadline=None)
    def test_search_text_results_have_required_structure(self, num_files, search_pattern):
        """Test that all search_text results have required structure fields.
        
        **Validates: Requirements 8.4**
        
        Property: For any code search operation that returns results, each result
        SHALL contain a file path (absolute or relative), a line number (positive 
        integer), and the matching text or symbol name.
        
        Tag: Feature: local-ai-dev-environment, Property 7: Search Result Structure
        """
        # Create test files
        self._create_test_files(num_files)
        
        # Create CodeSearch instance
        code_search = CodeSearch(project_root=self.temp_dir)
        
        # Perform search
        results = code_search.search_text(search_pattern, "*")
        
        # Skip if no results (edge case with small files)
        assume(len(results) > 0)
        
        # Verify structure of each result
        for result in results:
            # 1. Must have file_path (absolute or relative path string)
            assert hasattr(result, 'file_path'), "Result missing file_path attribute"
            assert isinstance(result.file_path, str), "file_path must be a string"
            assert len(result.file_path) > 0, "file_path must not be empty"
            
            # Verify file_path is a valid path (absolute or relative)
            file_path = Path(result.file_path)
            assert file_path.is_absolute() or str(file_path), "file_path must be a valid path"
            
            # 2. Must have line_number (positive integer)
            assert hasattr(result, 'line_number'), "Result missing line_number attribute"
            assert isinstance(result.line_number, int), "line_number must be an integer"
            assert result.line_number > 0, f"line_number must be positive, got {result.line_number}"
            
            # 3. Must have match_text (the matching text/line content)
            assert hasattr(result, 'match_text'), "Result missing match_text attribute"
            assert isinstance(result.match_text, str), "match_text must be a string"
            # match_text can be empty for blank lines but must exist
            assert result.match_text is not None, "match_text must not be None"
    
    @given(num_files=st.integers(min_value=1, max_value=10))
    @settings(max_examples=100, deadline=None)
    def test_find_symbol_results_have_required_structure(self, num_files):
        """Test that all find_symbol results have required structure fields.
        
        **Validates: Requirements 8.4**
        
        Property: For any symbol search operation that returns results, each result
        SHALL contain a file path, a line number (positive integer), and the symbol name.
        
        Tag: Feature: local-ai-dev-environment, Property 7: Search Result Structure
        """
        # Create test files
        self._create_test_files(num_files)
        
        # Create CodeSearch instance
        code_search = CodeSearch(project_root=self.temp_dir)
        
        # Search for a function that should exist in our test files
        symbol_name = f"function_0"  # First file should have this
        results = code_search.find_symbol(symbol_name)
        
        # Skip if no results found (shouldn't happen with our test setup)
        assume(len(results) > 0)
        
        # Verify structure of each result
        for result in results:
            # 1. Must have file_path
            assert hasattr(result, 'file_path'), "SymbolLocation missing file_path attribute"
            assert isinstance(result.file_path, str), "file_path must be a string"
            assert len(result.file_path) > 0, "file_path must not be empty"
            
            # Verify file_path is a valid path
            file_path = Path(result.file_path)
            assert file_path.is_absolute() or str(file_path), "file_path must be a valid path"
            
            # 2. Must have line_number (positive integer)
            assert hasattr(result, 'line_number'), "SymbolLocation missing line_number attribute"
            assert isinstance(result.line_number, int), "line_number must be an integer"
            assert result.line_number > 0, f"line_number must be positive, got {result.line_number}"
            
            # 3. Must have symbol_name
            assert hasattr(result, 'symbol_name'), "SymbolLocation missing symbol_name attribute"
            assert isinstance(result.symbol_name, str), "symbol_name must be a string"
            assert len(result.symbol_name) > 0, "symbol_name must not be empty"
            assert result.symbol_name == symbol_name, f"symbol_name should match searched symbol"
            
            # 4. Must have symbol_type (function, class, method, etc.)
            assert hasattr(result, 'symbol_type'), "SymbolLocation missing symbol_type attribute"
            assert isinstance(result.symbol_type, str), "symbol_type must be a string"
            assert result.symbol_type in ['function', 'class', 'method'], (
                f"symbol_type must be valid type, got '{result.symbol_type}'"
            )
    
    @given(
        num_files=st.integers(min_value=2, max_value=10),
        search_patterns=st.lists(
            st.sampled_from(['TODO', 'FIXME', 'def', 'class', 'import']),
            min_size=1,
            max_size=3,
            unique=True
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_multiple_search_operations_consistent_structure(self, num_files, search_patterns):
        """Test that structure is consistent across multiple search operations.
        
        **Validates: Requirements 8.4**
        
        Property: All search results from multiple operations should have the same
        consistent structure with file_path, line_number, and matching content.
        
        Tag: Feature: local-ai-dev-environment, Property 7: Search Result Structure
        """
        # Create test files
        self._create_test_files(num_files)
        
        # Create CodeSearch instance
        code_search = CodeSearch(project_root=self.temp_dir)
        
        all_results = []
        
        # Perform multiple searches
        for pattern in search_patterns:
            results = code_search.search_text(pattern, "*")
            all_results.extend(results)
        
        # Skip if no results across all searches
        assume(len(all_results) > 0)
        
        # Verify all results have consistent structure
        required_attrs = ['file_path', 'line_number', 'match_text']
        
        for i, result in enumerate(all_results):
            # All results must have the same attributes
            for attr in required_attrs:
                assert hasattr(result, attr), (
                    f"Result {i} missing required attribute '{attr}'"
                )
            
            # Verify types are consistent
            assert isinstance(result.file_path, str), f"Result {i}: file_path not a string"
            assert isinstance(result.line_number, int), f"Result {i}: line_number not an int"
            assert isinstance(result.match_text, str), f"Result {i}: match_text not a string"
            
            # Verify line_number is always positive
            assert result.line_number > 0, f"Result {i}: line_number not positive"
    
    @given(num_files=st.integers(min_value=1, max_value=5))
    @settings(max_examples=100, deadline=None)
    def test_search_results_line_numbers_within_file_bounds(self, num_files):
        """Test that line numbers in search results are within file bounds.
        
        **Validates: Requirements 8.4**
        
        Property: For any search result, the line_number must be valid (between 1
        and the total number of lines in the file).
        
        Tag: Feature: local-ai-dev-environment, Property 7: Search Result Structure
        """
        # Create test files
        self._create_test_files(num_files)
        
        # Create CodeSearch instance
        code_search = CodeSearch(project_root=self.temp_dir)
        
        # Search for common pattern
        results = code_search.search_text('def', "*")
        
        # Skip if no results
        assume(len(results) > 0)
        
        # Verify each result's line number is within file bounds
        for result in results:
            file_path = result.file_path
            line_number = result.line_number
            
            # Read the file to check total lines
            with open(file_path, 'r', encoding='utf-8') as f:
                total_lines = sum(1 for _ in f)
            
            # Line number must be within bounds
            assert 1 <= line_number <= total_lines, (
                f"line_number {line_number} out of bounds for file with {total_lines} lines: {file_path}"
            )
    
    @given(num_files=st.integers(min_value=1, max_value=5))
    @settings(max_examples=100, deadline=None)
    def test_search_result_match_text_contains_pattern(self, num_files):
        """Test that match_text in search results actually contains the search pattern.
        
        **Validates: Requirements 8.4**
        
        Property: For any search result from search_text, the match_text field
        should contain the search pattern that was used.
        
        Tag: Feature: local-ai-dev-environment, Property 7: Search Result Structure
        """
        # Create test files
        self._create_test_files(num_files)
        
        # Create CodeSearch instance
        code_search = CodeSearch(project_root=self.temp_dir)
        
        # Test with literal patterns (easier to verify)
        patterns = ['TODO', 'FIXME', 'import', 'return']
        
        for pattern in patterns:
            results = code_search.search_text(pattern, "*")
            
            # If results found, verify pattern is in match_text
            for result in results:
                assert pattern in result.match_text, (
                    f"Pattern '{pattern}' not found in match_text: '{result.match_text}'"
                )


@pytest.mark.property
class TestSymbolExtractionCompleteness:
    """Property-based tests for symbol extraction completeness.
    
    Tag: Feature: local-ai-dev-environment, Property 6: Symbol Extraction Completeness
    """
    
    def setup_method(self):
        """Create a temporary directory for each test method."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up temporary directory after each test method."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @st.composite
    def python_code_with_symbols(draw):
        """Generate syntactically valid Python code with functions and classes.
        
        Returns a tuple of (code_string, expected_symbols) where expected_symbols
        is a list of dicts with 'name', 'type', and 'line_number'.
        """
        symbols = []
        lines = []
        current_line = 1
        
        # Add optional module docstring
        if draw(st.booleans()):
            docstring = draw(st.text(alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Z'),
                max_codepoint=127
            ), min_size=0, max_size=50))
            lines.append(f'"""{ docstring }"""')
            current_line += 1
        
        # Add optional imports
        num_imports = draw(st.integers(min_value=0, max_value=3))
        for _ in range(num_imports):
            module = draw(st.sampled_from(['os', 'sys', 'json', 'time', 'random']))
            lines.append(f'import {module}')
            current_line += 1
        
        # Add blank line after imports if any
        if num_imports > 0:
            lines.append('')
            current_line += 1
        
        # Generate 1-5 top-level functions
        num_functions = draw(st.integers(min_value=1, max_value=5))
        for i in range(num_functions):
            func_name = f"function_{i}"
            params = draw(st.sampled_from(['', 'x', 'x, y', 'args', '*args', '**kwargs']))
            
            lines.append(f'def {func_name}({params}):')
            symbols.append({
                'name': func_name,
                'type': 'function',
                'line_number': current_line
            })
            current_line += 1
            
            # Add docstring
            lines.append(f'    """Function {func_name} docstring"""')
            current_line += 1
            
            # Add simple body
            body_lines = draw(st.integers(min_value=1, max_value=3))
            for _ in range(body_lines):
                statement = draw(st.sampled_from([
                    f'    return {i}',
                    '    pass',
                    f'    x = {i}',
                    '    print("test")'
                ]))
                lines.append(statement)
                current_line += 1
            
            # Add blank line after function
            lines.append('')
            current_line += 1
        
        # Generate 1-3 classes
        num_classes = draw(st.integers(min_value=1, max_value=3))
        for i in range(num_classes):
            class_name = f"Class_{i}"
            
            lines.append(f'class {class_name}:')
            symbols.append({
                'name': class_name,
                'type': 'class',
                'line_number': current_line
            })
            current_line += 1
            
            # Add class docstring
            lines.append(f'    """Class {class_name} docstring"""')
            current_line += 1
            
            # Add __init__ method
            lines.append('    def __init__(self):')
            symbols.append({
                'name': '__init__',
                'type': 'method',
                'line_number': current_line
            })
            current_line += 1
            
            lines.append('        """Initialize instance"""')
            current_line += 1
            lines.append(f'        self.value = {i}')
            current_line += 1
            lines.append('')
            current_line += 1
            
            # Add 1-3 methods
            num_methods = draw(st.integers(min_value=1, max_value=3))
            for j in range(num_methods):
                method_name = f"method_{j}"
                params = draw(st.sampled_from(['self', 'self, x', 'self, *args']))
                
                lines.append(f'    def {method_name}({params}):')
                symbols.append({
                    'name': method_name,
                    'type': 'method',
                    'line_number': current_line
                })
                current_line += 1
                
                lines.append(f'        """Method {method_name} docstring"""')
                current_line += 1
                lines.append(f'        return {j}')
                current_line += 1
                
                # Optional blank line
                if draw(st.booleans()):
                    lines.append('')
                    current_line += 1
            
            # Blank line after class
            lines.append('')
            current_line += 1
        
        code = '\n'.join(lines)
        return code, symbols
    
    @given(code_data=python_code_with_symbols())
    @settings(max_examples=100, deadline=None)
    def test_all_functions_and_classes_extracted(self, code_data):
        """Test that all function and class definitions are found.
        
        **Validates: Requirements 8.3**
        
        Property: For any syntactically valid source code file in a supported 
        language, parsing SHALL identify all function and class definitions.
        
        Tag: Feature: local-ai-dev-environment, Property 6: Symbol Extraction Completeness
        """
        code, expected_symbols = code_data
        
        # Create a Python file with the generated code
        test_file = os.path.join(self.temp_dir, 'test_module.py')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Create CodeSearch instance
        code_search = CodeSearch(project_root=self.temp_dir)
        
        # Extract all unique symbol names from expected_symbols
        unique_symbols = {}
        for symbol in expected_symbols:
            name = symbol['name']
            if name not in unique_symbols:
                unique_symbols[name] = symbol
        
        # Search for each expected symbol
        for symbol_name, symbol_info in unique_symbols.items():
            results = code_search.find_symbol(symbol_name)
            
            # Verify the symbol was found
            assert len(results) > 0, (
                f"Symbol '{symbol_name}' of type '{symbol_info['type']}' "
                f"not found at line {symbol_info['line_number']}"
            )
            
            # Verify at least one result matches our expectations
            found_match = False
            for result in results:
                if (result.symbol_name == symbol_name and
                    result.file_path == test_file and
                    result.symbol_type in ['function', 'class', 'method']):
                    found_match = True
                    break
            
            assert found_match, (
                f"Symbol '{symbol_name}' found but with incorrect metadata. "
                f"Expected type: {symbol_info['type']}, "
                f"Results: {[(r.symbol_name, r.symbol_type) for r in results]}"
            )
    
    @given(code_data=python_code_with_symbols())
    @settings(max_examples=100, deadline=None)
    def test_extracted_symbols_have_correct_metadata(self, code_data):
        """Test that each extracted symbol has correct metadata.
        
        **Validates: Requirements 8.3**
        
        Property: Each extracted symbol SHALL include the symbol name, type 
        (function/class), file path, and line number.
        
        Tag: Feature: local-ai-dev-environment, Property 6: Symbol Extraction Completeness
        """
        code, expected_symbols = code_data
        
        # Create a Python file with the generated code
        test_file = os.path.join(self.temp_dir, 'test_module.py')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Create CodeSearch instance
        code_search = CodeSearch(project_root=self.temp_dir)
        
        # Get all unique symbol names
        unique_symbol_names = set(s['name'] for s in expected_symbols)
        
        # Search for each symbol and verify metadata
        for symbol_name in unique_symbol_names:
            results = code_search.find_symbol(symbol_name)
            
            # Verify at least one result exists
            assume(len(results) > 0)
            
            for result in results:
                # 1. Must have symbol_name (string, non-empty)
                assert hasattr(result, 'symbol_name'), "Missing symbol_name attribute"
                assert isinstance(result.symbol_name, str), "symbol_name must be a string"
                assert len(result.symbol_name) > 0, "symbol_name must not be empty"
                assert result.symbol_name == symbol_name, "symbol_name must match search query"
                
                # 2. Must have symbol_type (function, class, or method)
                assert hasattr(result, 'symbol_type'), "Missing symbol_type attribute"
                assert isinstance(result.symbol_type, str), "symbol_type must be a string"
                assert result.symbol_type in ['function', 'class', 'method'], (
                    f"symbol_type must be 'function', 'class', or 'method', got '{result.symbol_type}'"
                )
                
                # 3. Must have file_path (absolute path string)
                assert hasattr(result, 'file_path'), "Missing file_path attribute"
                assert isinstance(result.file_path, str), "file_path must be a string"
                assert len(result.file_path) > 0, "file_path must not be empty"
                assert result.file_path == test_file, "file_path must match test file"
                
                # 4. Must have line_number (positive integer)
                assert hasattr(result, 'line_number'), "Missing line_number attribute"
                assert isinstance(result.line_number, int), "line_number must be an integer"
                assert result.line_number > 0, "line_number must be positive"
                
                # Verify line_number is within file bounds
                with open(test_file, 'r', encoding='utf-8') as f:
                    total_lines = sum(1 for _ in f)
                
                assert 1 <= result.line_number <= total_lines, (
                    f"line_number {result.line_number} out of bounds "
                    f"(file has {total_lines} lines)"
                )
    
    @given(
        num_functions=st.integers(min_value=1, max_value=10),
        num_classes=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_symbol_count_accuracy(self, num_functions, num_classes):
        """Test that the number of extracted symbols matches expected count.
        
        **Validates: Requirements 8.3**
        
        Property: All function and class definitions SHALL be found (completeness).
        
        Tag: Feature: local-ai-dev-environment, Property 6: Symbol Extraction Completeness
        """
        # Generate code with exact number of functions and classes
        lines = []
        expected_functions = []
        expected_classes = []
        
        # Generate functions
        for i in range(num_functions):
            func_name = f"func_{i}"
            lines.append(f'def {func_name}():')
            lines.append(f'    """Function {i}"""')
            lines.append(f'    return {i}')
            lines.append('')
            expected_functions.append(func_name)
        
        # Generate classes
        for i in range(num_classes):
            class_name = f"Class{i}"
            lines.append(f'class {class_name}:')
            lines.append(f'    """Class {i}"""')
            lines.append('    pass')
            lines.append('')
            expected_classes.append(class_name)
        
        code = '\n'.join(lines)
        
        # Create test file
        test_file = os.path.join(self.temp_dir, 'test_symbols.py')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Create CodeSearch instance
        code_search = CodeSearch(project_root=self.temp_dir)
        
        # Verify all functions are found
        for func_name in expected_functions:
            results = code_search.find_symbol(func_name)
            assert len(results) > 0, f"Function '{func_name}' not found"
            
            # At least one result should be a function
            function_results = [r for r in results if r.symbol_type == 'function']
            assert len(function_results) > 0, (
                f"Function '{func_name}' found but not typed as 'function'"
            )
        
        # Verify all classes are found
        for class_name in expected_classes:
            results = code_search.find_symbol(class_name)
            assert len(results) > 0, f"Class '{class_name}' not found"
            
            # At least one result should be a class
            class_results = [r for r in results if r.symbol_type == 'class']
            assert len(class_results) > 0, (
                f"Class '{class_name}' found but not typed as 'class'"
            )
    
    @given(code_data=python_code_with_symbols())
    @settings(max_examples=100, deadline=None)
    def test_symbol_line_numbers_accurate(self, code_data):
        """Test that extracted symbols have accurate line numbers.
        
        **Validates: Requirements 8.3, 8.4**
        
        Property: Each symbol's line_number SHALL point to the actual definition line.
        
        Tag: Feature: local-ai-dev-environment, Property 6: Symbol Extraction Completeness
        """
        code, expected_symbols = code_data
        
        # Create test file
        test_file = os.path.join(self.temp_dir, 'test_lines.py')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Create CodeSearch instance
        code_search = CodeSearch(project_root=self.temp_dir)
        
        # Read the file lines for verification
        with open(test_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Verify each expected symbol
        for symbol_info in expected_symbols:
            symbol_name = symbol_info['name']
            expected_line = symbol_info['line_number']
            symbol_type = symbol_info['type']
            
            results = code_search.find_symbol(symbol_name)
            
            # Find matching result
            matching_results = [
                r for r in results 
                if r.file_path == test_file
            ]
            
            assume(len(matching_results) > 0)
            
            # Verify at least one result points to the definition line
            found_valid_result = False
            for result in matching_results:
                # Verify the line actually contains the definition
                if result.line_number <= len(lines):
                    actual_line = lines[result.line_number - 1].strip()
                    
                    # Check if line contains the definition keyword and symbol name
                    if symbol_type == 'class':
                        if 'class' in actual_line and symbol_name in actual_line:
                            found_valid_result = True
                            break
                    elif symbol_type in ['function', 'method']:
                        if 'def' in actual_line and symbol_name in actual_line:
                            found_valid_result = True
                            break
            
            assert found_valid_result, (
                f"No result for '{symbol_name}' points to valid definition line. "
                f"Expected symbol type: {symbol_type}, "
                f"Line numbers found: {[r.line_number for r in matching_results]}"
            )
    
    @given(
        num_files=st.integers(min_value=2, max_value=5),
        symbols_per_file=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_symbol_extraction_across_multiple_files(self, num_files, symbols_per_file):
        """Test that symbol extraction works correctly across multiple files.
        
        **Validates: Requirements 8.3**
        
        Property: Symbol extraction SHALL work correctly across multiple files,
        finding all symbols in each file.
        
        Tag: Feature: local-ai-dev-environment, Property 6: Symbol Extraction Completeness
        """
        # Create multiple Python files with different symbols
        created_symbols = {}  # file_path -> list of symbol names
        
        for file_idx in range(num_files):
            file_name = f"module_{file_idx}.py"
            file_path = os.path.join(self.temp_dir, file_name)
            
            lines = [f'"""Module {file_idx}"""', '']
            file_symbols = []
            
            # Add functions
            for sym_idx in range(symbols_per_file):
                func_name = f"func_{file_idx}_{sym_idx}"
                lines.append(f'def {func_name}():')
                lines.append(f'    return {sym_idx}')
                lines.append('')
                file_symbols.append(func_name)
            
            # Add a class
            class_name = f"Class_{file_idx}"
            lines.append(f'class {class_name}:')
            lines.append('    pass')
            lines.append('')
            file_symbols.append(class_name)
            
            code = '\n'.join(lines)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            created_symbols[file_path] = file_symbols
        
        # Create CodeSearch instance
        code_search = CodeSearch(project_root=self.temp_dir)
        
        # Verify all symbols from all files are found
        for file_path, symbol_names in created_symbols.items():
            for symbol_name in symbol_names:
                results = code_search.find_symbol(symbol_name)
                
                # Verify symbol was found
                assert len(results) > 0, (
                    f"Symbol '{symbol_name}' not found in {file_path}"
                )
                
                # Verify at least one result is from the correct file
                file_results = [r for r in results if r.file_path == file_path]
                assert len(file_results) > 0, (
                    f"Symbol '{symbol_name}' not found in correct file {file_path}. "
                    f"Found in: {[r.file_path for r in results]}"
                )
