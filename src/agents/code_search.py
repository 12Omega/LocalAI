"""Code search module for Local AI Development Environment.

This module provides the CodeSearch class that handles searching for text patterns,
files, and symbols across a codebase with support for regex patterns and directory
exclusions.

Requirements implemented:
- 8.1: Search for text patterns across the codebase
- 8.2: Search for file names and paths
- 8.3: Identify function and class definitions
- 8.4: Return results with file paths and line numbers
- 8.5: Support regex patterns for advanced searches
- 8.6: Exclude irrelevant directories from searches
- 14.1: Provide descriptive error messages
"""

import re
import os
import logging
from pathlib import Path
from typing import List, Optional, Set
from dataclasses import dataclass

# Import SearchResult and SymbolLocation from core models
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.models import SearchResult, SymbolLocation

# Configure logger
logger = logging.getLogger(__name__)


class CodeSearch:
    """Handles code search operations across a codebase.
    
    This class provides methods for searching text patterns, finding files,
    and locating symbols (functions and classes) with support for regex
    patterns and directory exclusions.
    """
    
    # Default directories to exclude from searches
    DEFAULT_EXCLUDED_DIRS = {
        "node_modules", ".git", "__pycache__", ".pytest_cache",
        "venv", ".venv", "build", "dist", ".egg-info", ".tox",
        "htmlcov", ".coverage", ".mypy_cache", ".hypothesis",
        ".idea", ".vscode", ".vs", "bin", "obj"
    }
    
    def __init__(self, project_root: Optional[str] = None, excluded_dirs: Optional[Set[str]] = None):
        """Initialize CodeSearch.
        
        Args:
            project_root: Root directory for the project. If None, uses current directory.
            excluded_dirs: Set of directory names to exclude from searches. 
                         If None, uses DEFAULT_EXCLUDED_DIRS.
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.excluded_dirs = excluded_dirs if excluded_dirs is not None else self.DEFAULT_EXCLUDED_DIRS.copy()
    
    def search_text(self, pattern: str, file_pattern: str = "*") -> List[SearchResult]:
        """Search for text pattern (regex) across files.
        
        Searches all files matching file_pattern for occurrences of the regex pattern.
        Returns results with file path, line number, matching text, and surrounding context.
        
        Args:
            pattern: Regex pattern to search for
            file_pattern: Glob pattern for files to search (e.g., "*.py", "*.js", "*")
                         Default is "*" which searches all files.
            
        Returns:
            List of SearchResult objects containing matches with context
            
        Validates: Requirements 8.1, 8.4, 8.5, 8.6, 14.1
        
        Examples:
            search_text(r"def\\s+\\w+", "*.py")  # Find all function definitions in Python files
            search_text(r"TODO", "*")            # Find all TODO comments
            search_text(r"class\\s+\\w+", "*.js") # Find all class definitions in JS files
        """
        results = []
        
        try:
            # Compile the regex pattern
            regex = re.compile(pattern)
            logger.debug(f"Searching for pattern: {pattern} in files: {file_pattern}")
        except re.error as e:
            # Invalid regex pattern - log error and return empty results
            error_msg = f"Invalid regex pattern '{pattern}': {str(e)}"
            logger.error(error_msg)
            # Return empty results rather than raising exception
            # This allows graceful handling of malformed patterns
            return results
        
        # Find all files matching the file pattern
        files_searched = 0
        files_with_errors = 0
        
        for file_path in self._find_files(file_pattern):
            files_searched += 1
            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # Search each line for the pattern
                for line_num, line in enumerate(lines, start=1):
                    if regex.search(line):
                        # Extract context (3 lines before and after)
                        context_before = []
                        context_after = []
                        
                        # Get lines before (up to 3)
                        start_idx = max(0, line_num - 4)
                        for idx in range(start_idx, line_num - 1):
                            if idx < len(lines):
                                context_before.append(lines[idx].rstrip('\n'))
                        
                        # Get lines after (up to 3)
                        for idx in range(line_num, min(line_num + 3, len(lines))):
                            if idx < len(lines):
                                context_after.append(lines[idx].rstrip('\n'))
                        
                        # Create search result
                        result = SearchResult(
                            file_path=str(file_path),
                            line_number=line_num,
                            match_text=line.rstrip('\n'),
                            context_before=context_before,
                            context_after=context_after
                        )
                        results.append(result)
                        
            except (IOError, OSError) as e:
                # Skip files that can't be read (permissions, binary files, etc.)
                files_with_errors += 1
                logger.debug(f"Could not read file {file_path}: {str(e)}")
                continue
            except Exception as e:
                # Log unexpected errors but continue searching
                files_with_errors += 1
                logger.warning(f"Unexpected error reading file {file_path}: {str(e)}")
                continue
        
        logger.info(
            f"Search completed: found {len(results)} matches in {files_searched} files "
            f"({files_with_errors} files skipped due to errors)"
        )
        
        return results
    
    def search_files(self, name_pattern: str) -> List[str]:
        """Find files matching name pattern.
        
        Searches the project directory for files whose names match the given pattern.
        Supports glob patterns like "*.py", "test_*.js", "README.*", etc.
        
        Args:
            name_pattern: Glob pattern for file names (e.g., "*.py", "test_*.js")
            
        Returns:
            List of file paths (as strings) matching the pattern
            
        Validates: Requirements 8.2, 8.4, 8.6
        
        Examples:
            search_files("*.py")        # Find all Python files
            search_files("test_*.py")   # Find all Python test files
            search_files("README.*")    # Find README files with any extension
        """
        results = []
        
        # Find all files matching the pattern
        for file_path in self._find_files(name_pattern):
            results.append(str(file_path))
        
        return results
    
    def find_symbol(self, symbol_name: str) -> List[SymbolLocation]:
        """Find function/class definitions by symbol name.
        
        Searches Python files for function and class definitions matching the
        given symbol name. Returns the locations with metadata about the symbol type.
        
        Args:
            symbol_name: Name of the function or class to find
            
        Returns:
            List of SymbolLocation objects with file path, line number, 
            symbol name, and symbol type
            
        Validates: Requirements 8.3, 8.4, 8.6
        
        Examples:
            find_symbol("CodeSearch")     # Find the CodeSearch class definition
            find_symbol("search_text")    # Find the search_text function/method
            find_symbol("main")           # Find main function definitions
        """
        results = []
        
        # Regex patterns for Python function and class definitions
        # Function: def symbol_name(...):
        # Use [ \t]* instead of \s* to avoid matching newlines
        func_pattern = re.compile(
            r'^[ \t]*def\s+' + re.escape(symbol_name) + r'\s*\(',
            re.MULTILINE
        )
        
        # Class: class symbol_name(...):
        # Use [ \t]* instead of \s* to avoid matching newlines
        class_pattern = re.compile(
            r'^[ \t]*class\s+' + re.escape(symbol_name) + r'\s*[(:[]',
            re.MULTILINE
        )
        
        # Method within a class: def symbol_name(...): (indented)
        # Use [ \t]+ instead of \s+ to avoid matching newlines
        method_pattern = re.compile(
            r'^[ \t]+def\s+' + re.escape(symbol_name) + r'\s*\(',
            re.MULTILINE
        )
        
        # Search all Python files
        for file_path in self._find_files("*.py"):
            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    content = ''.join(lines)
                
                # Track results by line number to sort them
                line_results = []
                
                # Search for class definitions
                for match in class_pattern.finditer(content):
                    line_num = content[:match.start()].count('\n') + 1
                    result = SymbolLocation(
                        file_path=str(file_path),
                        line_number=line_num,
                        symbol_name=symbol_name,
                        symbol_type="class"
                    )
                    line_results.append((line_num, 0, result))  # 0 = class priority
                
                # Search for function definitions (top-level functions and methods)
                for match in func_pattern.finditer(content):
                    line_num = content[:match.start()].count('\n') + 1
                    
                    # Check if it's actually a method (indented)
                    line_start = content.rfind('\n', 0, match.start()) + 1
                    line_text = content[line_start:match.end()]
                    
                    if line_text.startswith(' ') or line_text.startswith('\t'):
                        # This is a method, not a top-level function
                        symbol_type = "method"
                        priority = 2  # methods last
                    else:
                        # This is a top-level function
                        symbol_type = "function"
                        priority = 1  # functions middle
                    
                    result = SymbolLocation(
                        file_path=str(file_path),
                        line_number=line_num,
                        symbol_name=symbol_name,
                        symbol_type=symbol_type
                    )
                    line_results.append((line_num, priority, result))
                
                # Sort by line number first, then by priority (class < function < method)
                # This gives predictable ordering while keeping related symbols together
                line_results.sort(key=lambda x: (x[0], x[1]))
                results.extend([r[2] for r in line_results])
                    
            except (IOError, OSError):
                # Skip files that can't be read
                continue
        
        return results
    
    def _find_files(self, pattern: str) -> List[Path]:
        """Find all files matching the glob pattern in the project.
        
        Recursively searches the project directory for files matching the pattern,
        excluding directories in the excluded_dirs set.
        
        Args:
            pattern: Glob pattern for files (e.g., "*.py", "*.js", "*")
            
        Returns:
            List of Path objects for matching files
        """
        results = []
        
        # Walk through the project directory
        for root, dirs, files in os.walk(self.project_root):
            # Remove excluded directories from dirs list (modifies in-place)
            # This prevents os.walk from descending into excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
            
            # Check each file against the pattern
            root_path = Path(root)
            for file_name in files:
                file_path = root_path / file_name
                
                # Match against the pattern
                if self._matches_pattern(file_name, pattern):
                    results.append(file_path)
        
        return results
    
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches the glob pattern.
        
        Args:
            filename: Name of the file to check
            pattern: Glob pattern (e.g., "*.py", "test_*.js", "*")
            
        Returns:
            True if filename matches pattern, False otherwise
        """
        # Convert glob pattern to regex
        # * matches any characters except /
        # ? matches any single character except /
        # [seq] matches any character in seq
        # [!seq] matches any character not in seq
        
        regex_pattern = pattern
        regex_pattern = regex_pattern.replace('.', r'\.')  # Escape dots
        regex_pattern = regex_pattern.replace('*', '.*')   # * -> .*
        regex_pattern = regex_pattern.replace('?', '.')    # ? -> .
        regex_pattern = '^' + regex_pattern + '$'          # Anchor to start and end
        
        try:
            return bool(re.match(regex_pattern, filename))
        except re.error:
            # If pattern is invalid, no match
            return False
