"""Unit tests for CodeSearch edge cases.

Tests cover:
- Empty search results
- Malformed regex patterns
- Very large codebases (performance testing)
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
import time
import re

from src.agents.code_search import CodeSearch
from src.core.models import SearchResult, SymbolLocation


class TestCodeSearchEdgeCases:
    """Unit tests for CodeSearch edge cases."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)
    
    @pytest.fixture
    def code_search(self, temp_dir):
        """Create CodeSearch instance with temp directory."""
        return CodeSearch(project_root=temp_dir)
    
    # Empty Search Results Tests
    
    def test_search_text_empty_codebase(self, code_search, temp_dir):
        """Test searching an empty codebase returns empty results."""
        results = code_search.search_text("test_pattern", "*.py")
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_search_text_no_matches(self, code_search, temp_dir):
        """Test searching with pattern that has no matches."""
        # Create some files
        file1 = Path(temp_dir) / "file1.py"
        file1.write_text("def hello():\n    print('Hello, World!')\n")
        
        file2 = Path(temp_dir) / "file2.py"
        file2.write_text("class MyClass:\n    pass\n")
        
        # Search for pattern that doesn't exist
        results = code_search.search_text(r"nonexistent_pattern_xyz", "*.py")
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_search_files_no_matches(self, code_search, temp_dir):
        """Test searching for files that don't exist."""
        # Create some files
        file1 = Path(temp_dir) / "file1.py"
        file1.write_text("content")
        
        file2 = Path(temp_dir) / "file2.txt"
        file2.write_text("content")
        
        # Search for pattern that doesn't match any files
        results = code_search.search_files("*.js")
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_find_symbol_no_matches(self, code_search, temp_dir):
        """Test finding symbol that doesn't exist."""
        # Create Python file without the symbol
        file1 = Path(temp_dir) / "file1.py"
        file1.write_text("def other_function():\n    pass\n")
        
        # Search for non-existent symbol
        results = code_search.find_symbol("NonExistentClass")
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_search_text_empty_files(self, code_search, temp_dir):
        """Test searching empty files returns no results."""
        # Create empty files
        for i in range(5):
            file_path = Path(temp_dir) / f"empty_{i}.py"
            file_path.write_text("")
        
        results = code_search.search_text(".*", "*.py")
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_search_files_in_empty_directory(self, code_search, temp_dir):
        """Test searching for files in an empty directory."""
        results = code_search.search_files("*")
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_search_text_with_whitespace_only_files(self, code_search, temp_dir):
        """Test searching files that contain only whitespace."""
        # Create files with only whitespace
        file1 = Path(temp_dir) / "whitespace1.py"
        file1.write_text("   \n\n\t\t\n   ")
        
        file2 = Path(temp_dir) / "whitespace2.py"
        file2.write_text("\n\n\n")
        
        # Search for non-whitespace content
        results = code_search.search_text(r"\w+", "*.py")
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_find_symbol_in_comments_only(self, code_search, temp_dir):
        """Test finding symbol that only appears in comments (should not match)."""
        # Create file with symbol only in comments
        file1 = Path(temp_dir) / "comments.py"
        file1.write_text("# This mentions MyClass but doesn't define it\n# class MyClass is just a comment\n")
        
        # Should not find the symbol since it's only in comments
        results = code_search.find_symbol("MyClass")
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_search_text_excluded_directories_only(self, code_search, temp_dir):
        """Test searching when all matches are in excluded directories."""
        # Create excluded directory with files
        excluded_dir = Path(temp_dir) / "node_modules"
        excluded_dir.mkdir()
        
        file1 = excluded_dir / "file.js"
        file1.write_text("function test() { return 'test'; }")
        
        # Search for pattern that exists only in excluded directory
        results = code_search.search_text("test", "*.js")
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    # Malformed Regex Pattern Tests
    
    def test_search_text_invalid_regex_unclosed_bracket(self, code_search, temp_dir):
        """Test searching with unclosed bracket in regex."""
        # Create a file
        file1 = Path(temp_dir) / "file1.py"
        file1.write_text("def test():\n    pass\n")
        
        # Use invalid regex with unclosed bracket
        results = code_search.search_text(r"test[abc", "*.py")
        
        # Should return empty results (invalid regex is handled gracefully)
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_search_text_invalid_regex_unclosed_group(self, code_search, temp_dir):
        """Test searching with unclosed group in regex."""
        file1 = Path(temp_dir) / "file1.py"
        file1.write_text("def test():\n    pass\n")
        
        # Invalid regex with unclosed group
        results = code_search.search_text(r"test(abc", "*.py")
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_search_text_invalid_regex_bad_repetition(self, code_search, temp_dir):
        """Test searching with invalid repetition operator."""
        file1 = Path(temp_dir) / "file1.py"
        file1.write_text("def test():\n    pass\n")
        
        # Invalid regex - repetition operator without operand
        results = code_search.search_text(r"*test", "*.py")
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_search_text_invalid_regex_bad_escape(self, code_search, temp_dir):
        """Test searching with invalid escape sequence."""
        file1 = Path(temp_dir) / "file1.py"
        file1.write_text("def test():\n    pass\n")
        
        # Invalid escape sequence at end
        results = code_search.search_text(r"test\\", "*.py")
        
        # This might actually be valid (trailing backslash), but test it anyway
        assert isinstance(results, list)
    
    def test_search_text_invalid_regex_unmatched_parenthesis(self, code_search, temp_dir):
        """Test searching with unmatched parenthesis."""
        file1 = Path(temp_dir) / "file1.py"
        file1.write_text("def test():\n    pass\n")
        
        # Invalid regex with unmatched closing parenthesis
        results = code_search.search_text(r"test)", "*.py")
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_search_text_invalid_regex_bad_character_range(self, code_search, temp_dir):
        """Test searching with invalid character range."""
        file1 = Path(temp_dir) / "file1.py"
        file1.write_text("def test():\n    pass\n")
        
        # Invalid character range (z-a is backwards)
        results = code_search.search_text(r"[z-a]", "*.py")
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_search_text_invalid_regex_incomplete_escape(self, code_search, temp_dir):
        """Test searching with incomplete escape sequence."""
        file1 = Path(temp_dir) / "file1.py"
        file1.write_text("def test():\n    pass\n")
        
        # Try various problematic patterns
        invalid_patterns = [
            r"(?",  # Incomplete group
            r"(?P",  # Incomplete named group
            r"(?P<",  # Incomplete named group
            r"(?P<name",  # Incomplete named group
        ]
        
        for pattern in invalid_patterns:
            results = code_search.search_text(pattern, "*.py")
            assert isinstance(results, list)
            # Should handle gracefully and return empty or raise handled exception
    
    def test_search_text_complex_invalid_regex(self, code_search, temp_dir):
        """Test searching with complex invalid regex."""
        file1 = Path(temp_dir) / "file1.py"
        file1.write_text("def test():\n    pass\n")
        
        # Complex invalid pattern
        results = code_search.search_text(r"(((?P<name>test)[", "*.py")
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_search_text_empty_regex_pattern(self, code_search, temp_dir):
        """Test searching with empty regex pattern."""
        file1 = Path(temp_dir) / "file1.py"
        file1.write_text("def test():\n    pass\n")
        
        # Empty pattern
        results = code_search.search_text("", "*.py")
        
        assert isinstance(results, list)
        # Empty pattern should either match every line or nothing
        # Current implementation will likely match every line with content
    
    def test_search_text_null_bytes_in_regex(self, code_search, temp_dir):
        """Test searching with null bytes in regex pattern."""
        file1 = Path(temp_dir) / "file1.py"
        file1.write_text("def test():\n    pass\n")
        
        # Pattern with null byte
        try:
            results = code_search.search_text("test\x00pattern", "*.py")
            assert isinstance(results, list)
        except (ValueError, re.error):
            # Some regex engines reject null bytes
            pass
    
    # Performance Tests for Large Codebases
    
    def test_search_text_large_number_of_files(self, code_search, temp_dir):
        """Test searching across a large number of files (performance test)."""
        # Create 1000 files with content
        num_files = 1000
        for i in range(num_files):
            file_path = Path(temp_dir) / f"file_{i}.py"
            file_path.write_text(f"def function_{i}():\n    pass\n")
        
        # Measure search time
        start_time = time.time()
        results = code_search.search_text(r"def\s+function_", "*.py")
        elapsed_time = time.time() - start_time
        
        # Verify results
        assert isinstance(results, list)
        assert len(results) == num_files  # Should find all functions
        
        # Performance assertion: should complete in reasonable time
        # Adjust threshold as needed based on system performance
        assert elapsed_time < 40.0, f"Search took too long: {elapsed_time:.2f}s"
        
        print(f"Search across {num_files} files took {elapsed_time:.2f}s")
    
    def test_search_text_very_large_files(self, code_search, temp_dir):
        """Test searching in very large files (performance test)."""
        # Create a very large file (5MB)
        large_content = []
        for i in range(50000):  # 50,000 lines
            large_content.append(f"def function_{i}():\n")
            large_content.append(f"    return {i}\n")
        
        file_path = Path(temp_dir) / "large_file.py"
        file_path.write_text("".join(large_content))
        
        # Measure search time
        start_time = time.time()
        results = code_search.search_text(r"function_12345", "*.py")
        elapsed_time = time.time() - start_time
        
        # Verify results
        assert isinstance(results, list)
        assert len(results) == 1  # Should find the specific function
        assert results[0].line_number > 0
        
        # Performance assertion
        assert elapsed_time < 5.0, f"Search in large file took too long: {elapsed_time:.2f}s"
        
        print(f"Search in large file ({file_path.stat().st_size / 1024 / 1024:.2f}MB) took {elapsed_time:.2f}s")
    
    def test_search_text_deep_directory_structure(self, code_search, temp_dir):
        """Test searching in deeply nested directory structure (performance test)."""
        # Create deep directory structure (20 levels deep)
        current_dir = Path(temp_dir)
        for i in range(20):
            current_dir = current_dir / f"level_{i}"
            current_dir.mkdir()
            
            # Add a file at each level
            file_path = current_dir / f"file_{i}.py"
            file_path.write_text(f"def deep_function_{i}():\n    pass\n")
        
        # Measure search time
        start_time = time.time()
        results = code_search.search_text(r"deep_function", "*.py")
        elapsed_time = time.time() - start_time
        
        # Verify results
        assert isinstance(results, list)
        assert len(results) == 20  # Should find all functions at all levels
        
        # Performance assertion
        assert elapsed_time < 5.0, f"Search in deep structure took too long: {elapsed_time:.2f}s"
        
        print(f"Search in 20-level deep directory took {elapsed_time:.2f}s")
    
    def test_search_files_large_codebase(self, code_search, temp_dir):
        """Test file search in large codebase (performance test)."""
        # Create 2000 files with various extensions
        num_files = 2000
        for i in range(num_files):
            ext = [".py", ".js", ".txt", ".md", ".json"][i % 5]
            file_path = Path(temp_dir) / f"file_{i}{ext}"
            file_path.write_text("content")
        
        # Measure search time for specific pattern
        start_time = time.time()
        results = code_search.search_files("*.py")
        elapsed_time = time.time() - start_time
        
        # Verify results
        assert isinstance(results, list)
        assert len(results) == 400  # 2000 / 5 = 400 Python files
        
        # Performance assertion
        assert elapsed_time < 5.0, f"File search took too long: {elapsed_time:.2f}s"
        
        print(f"File search across {num_files} files took {elapsed_time:.2f}s")
    
    def test_find_symbol_large_codebase(self, code_search, temp_dir):
        """Test symbol finding in large codebase (performance test)."""
        # Create 500 Python files with various functions and classes
        num_files = 500
        for i in range(num_files):
            content = []
            # Add some classes
            for j in range(5):
                content.append(f"class Class_{i}_{j}:\n")
                content.append(f"    def method_{j}(self):\n")
                content.append(f"        pass\n\n")
            
            # Add some functions
            for j in range(5):
                content.append(f"def function_{i}_{j}():\n")
                content.append(f"    pass\n\n")
            
            file_path = Path(temp_dir) / f"module_{i}.py"
            file_path.write_text("".join(content))
        
        # Measure search time for a common symbol name
        start_time = time.time()
        results = code_search.find_symbol("method_2")
        elapsed_time = time.time() - start_time
        
        # Verify results
        assert isinstance(results, list)
        assert len(results) == num_files  # Should find method_2 in each file
        
        # Performance assertion - allow up to 15s for slower systems
        assert elapsed_time < 15.0, f"Symbol search took too long: {elapsed_time:.2f}s"
        
        print(f"Symbol search across {num_files} files took {elapsed_time:.2f}s")
    
    def test_search_text_with_many_excluded_directories(self, code_search, temp_dir):
        """Test performance when many directories are excluded."""
        # Create many directories, some excluded
        excluded_names = ["node_modules", ".git", "__pycache__", "venv", "build"]
        
        # Create 10 excluded directories each with 50 files
        for excluded_name in excluded_names:
            excluded_dir = Path(temp_dir) / excluded_name
            excluded_dir.mkdir()
            for i in range(50):
                file_path = excluded_dir / f"file_{i}.py"
                file_path.write_text(f"def excluded_function_{i}():\n    pass\n")
        
        # Create 100 normal files
        for i in range(100):
            file_path = Path(temp_dir) / f"normal_file_{i}.py"
            file_path.write_text(f"def normal_function_{i}():\n    pass\n")
        
        # Measure search time
        start_time = time.time()
        results = code_search.search_text(r"def\s+\w+_function", "*.py")
        elapsed_time = time.time() - start_time
        
        # Verify results - should only find normal files, not excluded
        assert isinstance(results, list)
        assert len(results) == 100  # Only normal files
        
        # Should be fast since excluded directories are skipped
        assert elapsed_time < 3.0, f"Search with exclusions took too long: {elapsed_time:.2f}s"
        
        print(f"Search with {len(excluded_names)} excluded dirs took {elapsed_time:.2f}s")
    
    def test_search_text_with_long_lines(self, code_search, temp_dir):
        """Test searching files with very long lines."""
        # Create file with very long lines (10KB per line)
        long_lines = []
        for i in range(100):
            # Create a line with 10,000 characters
            long_line = f"# This is a very long comment line {i} " + "x" * 9950
            long_lines.append(long_line + "\n")
        
        file_path = Path(temp_dir) / "long_lines.py"
        file_path.write_text("".join(long_lines))
        
        # Measure search time
        start_time = time.time()
        results = code_search.search_text(r"comment line 50", "*.py")
        elapsed_time = time.time() - start_time
        
        # Verify results
        assert isinstance(results, list)
        assert len(results) == 1
        
        # Performance assertion
        assert elapsed_time < 2.0, f"Search with long lines took too long: {elapsed_time:.2f}s"
        
        print(f"Search in file with long lines took {elapsed_time:.2f}s")
    
    def test_search_text_binary_files_mixed(self, code_search, temp_dir):
        """Test searching when binary files are mixed with text files."""
        # Create mix of text and binary-like files
        for i in range(50):
            text_file = Path(temp_dir) / f"text_{i}.py"
            text_file.write_text(f"def function_{i}():\n    pass\n")
            
            # Create "binary" file (file with non-UTF8 content)
            binary_file = Path(temp_dir) / f"binary_{i}.pyc"
            binary_file.write_bytes(bytes([i % 256 for _ in range(1000)]))
        
        # Search should handle binary files gracefully
        start_time = time.time()
        results = code_search.search_text(r"def function", "*.py*")
        elapsed_time = time.time() - start_time
        
        # Should find only text files
        assert isinstance(results, list)
        assert len(results) == 50  # Only the .py files
        
        # Should not crash on binary files
        assert elapsed_time < 5.0
        
        print(f"Search with mixed text/binary files took {elapsed_time:.2f}s")
    
    def test_search_extreme_regex_complexity(self, code_search, temp_dir):
        """Test performance with complex regex patterns."""
        # Create files with content
        for i in range(100):
            file_path = Path(temp_dir) / f"file_{i}.py"
            content = []
            for j in range(100):
                content.append(f"def function_{i}_{j}():\n")
                content.append(f"    return {i} + {j}\n")
            file_path.write_text("".join(content))
        
        # Complex regex pattern with multiple groups and lookaheads
        complex_pattern = r"def\s+function_\d+_\d+\s*\(\s*\)\s*:"
        
        # Measure search time
        start_time = time.time()
        results = code_search.search_text(complex_pattern, "*.py")
        elapsed_time = time.time() - start_time
        
        # Verify results
        assert isinstance(results, list)
        assert len(results) == 10000  # 100 files * 100 functions each
        
        # Performance assertion - complex regex should still be reasonably fast
        assert elapsed_time < 15.0, f"Complex regex search took too long: {elapsed_time:.2f}s"
        
        print(f"Complex regex search across 100 files took {elapsed_time:.2f}s")
    
    # Edge Cases Combining Multiple Factors
    
    def test_empty_results_with_valid_regex_and_files(self, code_search, temp_dir):
        """Test case where regex is valid, files exist, but no matches."""
        # Create files with specific content
        file1 = Path(temp_dir) / "module1.py"
        file1.write_text("import os\nimport sys\n\ndef main():\n    pass\n")
        
        file2 = Path(temp_dir) / "module2.py"
        file2.write_text("class MyClass:\n    def __init__(self):\n        pass\n")
        
        # Search for pattern that's valid but won't match
        results = code_search.search_text(r"^import\s+re$", "*.py")
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_malformed_regex_with_large_codebase(self, code_search, temp_dir):
        """Test malformed regex on large codebase doesn't cause issues."""
        # Create large codebase
        for i in range(200):
            file_path = Path(temp_dir) / f"file_{i}.py"
            file_path.write_text(f"def function_{i}():\n    pass\n")
        
        # Try invalid regex
        results = code_search.search_text(r"def\s+function_[0-9", "*.py")
        
        # Should handle gracefully
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_search_nonexistent_file_pattern(self, code_search, temp_dir):
        """Test searching with file pattern that matches no files."""
        # Create some files
        file1 = Path(temp_dir) / "file.py"
        file1.write_text("content")
        
        # Search with non-matching file pattern
        results = code_search.search_text("content", "*.nonexistent")
        
        assert isinstance(results, list)
        assert len(results) == 0
