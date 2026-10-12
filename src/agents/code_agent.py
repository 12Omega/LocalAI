"""Code agent module for Local AI Development Environment.

This module provides the CodeAgent class that orchestrates code-related operations
by integrating FileOperations, CodeSearch, and CommandExecutor to provide high-level
code generation and editing capabilities.

Requirements implemented:
- 2.1: Generate complete, functional code for tasks
- 2.2: Create new files in appropriate directories
- 2.3: Follow existing code style and conventions
- 2.4: Include appropriate comments and documentation
- 2.5: Generate syntactically correct code
- 2.6: Create all necessary files to complete tasks
- 3.1: Locate relevant code sections for editing
- 3.2: Make precise edits preserving existing functionality
- 3.3: Maintain consistency with surrounding code style
- 3.4: Preserve code structure and formatting conventions
- 3.5: Update all affected sections when introducing dependencies
- 15.2: Log all file operations with timestamps
- 15.4: Log all code changes made
"""

import logging
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

# Import required components
from .file_operations import FileOperations, OperationResult
from .code_search import CodeSearch
from .command_executor import CommandExecutor, CommandResult


class CodeAgent:
    """Orchestrates code generation and editing operations.
    
    The CodeAgent integrates FileOperations, CodeSearch, and CommandExecutor
    to provide high-level capabilities for creating and editing code. It implements
    intelligent code generation strategies that analyze existing code style and
    conventions, and precise code editing strategies that modify specific line ranges.
    
    This class does NOT directly interact with the LLM - that's handled by the
    Task Executor. The CodeAgent provides the tools/methods that the Task Executor
    will orchestrate.
    """
    
    def __init__(
        self,
        project_root: Optional[str] = None,
        excluded_dirs: Optional[set] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize CodeAgent.
        
        Args:
            project_root: Root directory for the project. If None, uses current directory.
            excluded_dirs: Set of directory names to exclude from searches.
            logger: Logger instance for logging operations. If None, creates a default logger.
        """
        self.project_root = project_root or str(Path.cwd())
        
        # Initialize component modules
        self.file_ops = FileOperations(project_root=self.project_root)
        self.code_search = CodeSearch(project_root=self.project_root, excluded_dirs=excluded_dirs)
        self.command_executor = CommandExecutor(default_cwd=self.project_root)
        
        # Initialize logger
        self.logger = logger or self._create_default_logger()
        
        self.logger.info(f"CodeAgent initialized with project_root: {self.project_root}")
    
    def create_code(self, task_description: str, context: Dict[str, Any]) -> OperationResult:
        """Create new code files based on task description and context.
        
        This method implements the code generation strategy:
        1. Analyze existing code style and conventions from context
        2. Generate code that follows detected patterns
        3. Create file(s) with appropriate content
        4. Log all operations
        
        Args:
            task_description: Description of what code to create
            context: Dictionary containing:
                - file_path: Path where to create the file (required)
                - content: Code content to write (required)
                - related_files: List of related file paths for style analysis (optional)
                - language: Programming language (optional, inferred from file_path if not provided)
                
        Returns:
            OperationResult with success status and message
            
        Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 15.2, 15.4
        
        Example:
            context = {
                'file_path': 'src/utils/helper.py',
                'content': 'def calculate(x, y):\\n    return x + y\\n',
                'related_files': ['src/utils/math_utils.py'],
                'language': 'python'
            }
            result = agent.create_code("Create helper function", context)
        """
        start_time = datetime.now()
        self.logger.info(f"[{start_time}] Starting code creation: {task_description}")
        
        try:
            # Validate required context fields
            if 'file_path' not in context:
                self.logger.error("Missing required field 'file_path' in context")
                return OperationResult(
                    success=False,
                    message="Missing required field 'file_path' in context",
                    error_type="invalid_context"
                )
            
            if 'content' not in context:
                self.logger.error("Missing required field 'content' in context")
                return OperationResult(
                    success=False,
                    message="Missing required field 'content' in context",
                    error_type="invalid_context"
                )
            
            file_path = context['file_path']
            content = context['content']
            
            # Analyze existing code style if related files are provided
            style_info = None
            if 'related_files' in context and context['related_files']:
                self.logger.debug(f"Analyzing code style from {len(context['related_files'])} related files")
                style_info = self._analyze_code_style(context['related_files'])
                self.logger.debug(f"Detected style: {style_info}")
            
            # Log the code creation operation
            self.logger.info(f"Creating file: {file_path}")
            self.logger.debug(f"Content length: {len(content)} characters")
            if style_info:
                self.logger.debug(f"Following style conventions: {style_info}")
            
            # Create the file
            result = self.file_ops.create_file(file_path, content)
            
            # Log result
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result.success:
                self.logger.info(f"[{end_time}] Code creation successful: {file_path} (duration: {duration:.2f}s)")
                self.logger.info(f"Code change: Created {file_path} with {len(content)} characters")
            else:
                self.logger.error(f"[{end_time}] Code creation failed: {result.message} (duration: {duration:.2f}s)")
            
            return result
            
        except Exception as e:
            end_time = datetime.now()
            error_msg = f"Unexpected error in create_code: {str(e)}"
            self.logger.error(f"[{end_time}] {error_msg}")
            return OperationResult(
                success=False,
                message=error_msg,
                error_type="unexpected"
            )
    
    def edit_code(
        self,
        file_path: str,
        modification_request: str,
        context: Dict[str, Any]
    ) -> OperationResult:
        """Edit existing code based on modification request and context.
        
        This method implements the code editing strategy:
        1. Read the full file content
        2. Identify exact line ranges to modify (from context)
        3. Apply precise edits to those ranges
        4. Preserve formatting and style of surrounding code
        5. Log all operations
        
        Args:
            file_path: Path to the file to edit
            modification_request: Description of what modifications to make
            context: Dictionary containing:
                - new_content: Complete new content for the file (option 1), OR
                - edits: List of edit operations (option 2), where each edit has:
                    - start_line: Starting line number (1-indexed)
                    - end_line: Ending line number (1-indexed, inclusive)
                    - new_text: Text to replace the line range with
                
        Returns:
            OperationResult with success status and message
            
        Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 15.2, 15.4
        
        Example (full content replacement):
            context = {'new_content': 'def foo():\\n    return 42\\n'}
            result = agent.edit_code('src/utils.py', 'Update function', context)
            
        Example (precise line edits):
            context = {
                'edits': [
                    {'start_line': 10, 'end_line': 12, 'new_text': 'def new_func():\\n    pass\\n'}
                ]
            }
            result = agent.edit_code('src/utils.py', 'Replace function', context)
        """
        start_time = datetime.now()
        self.logger.info(f"[{start_time}] Starting code edit: {modification_request}")
        self.logger.info(f"Editing file: {file_path}")
        
        try:
            # Read the current file content
            current_content, read_result = self.file_ops.read_file(file_path)
            
            if not read_result.success:
                self.logger.error(f"Failed to read file for editing: {read_result.message}")
                return read_result
            
            self.logger.debug(f"Current file content: {len(current_content)} characters")
            
            # Determine edit strategy based on context
            if 'new_content' in context:
                # Full content replacement
                new_content = context['new_content']
                self.logger.debug(f"Applying full content replacement: {len(new_content)} characters")
                
            elif 'edits' in context:
                # Precise line range edits
                edits = context['edits']
                self.logger.debug(f"Applying {len(edits)} precise edits")
                new_content = self._apply_line_edits(current_content, edits)
                
                if new_content is None:
                    self.logger.error("Failed to apply line edits")
                    return OperationResult(
                        success=False,
                        message="Failed to apply line edits - invalid line ranges",
                        error_type="invalid_edit"
                    )
            else:
                self.logger.error("Missing required field 'new_content' or 'edits' in context")
                return OperationResult(
                    success=False,
                    message="Missing required field 'new_content' or 'edits' in context",
                    error_type="invalid_context"
                )
            
            # Update the file
            result = self.file_ops.update_file(file_path, new_content)
            
            # Log result
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result.success:
                self.logger.info(f"[{end_time}] Code edit successful: {file_path} (duration: {duration:.2f}s)")
                
                # Log the specific changes
                old_lines = current_content.count('\n') + 1
                new_lines = new_content.count('\n') + 1
                self.logger.info(f"Code change: Modified {file_path} ({old_lines} -> {new_lines} lines)")
                
                # Calculate diff size
                chars_added = len(new_content) - len(current_content)
                self.logger.debug(f"Characters changed: {chars_added:+d}")
            else:
                self.logger.error(f"[{end_time}] Code edit failed: {result.message} (duration: {duration:.2f}s)")
            
            return result
            
        except Exception as e:
            end_time = datetime.now()
            error_msg = f"Unexpected error in edit_code: {str(e)}"
            self.logger.error(f"[{end_time}] {error_msg}")
            return OperationResult(
                success=False,
                message=error_msg,
                error_type="unexpected"
            )
    
    def _analyze_code_style(self, file_paths: List[str]) -> Dict[str, Any]:
        """Analyze code style and conventions from existing files.
        
        Examines related files to detect:
        - Indentation style (spaces vs tabs, indent size)
        - Naming conventions (camelCase, snake_case, PascalCase)
        - Import style (relative vs absolute)
        - Documentation style (docstrings, comments)
        
        Args:
            file_paths: List of file paths to analyze
            
        Returns:
            Dictionary with detected style information:
                - indent_style: 'spaces' or 'tabs'
                - indent_size: Number of spaces (if indent_style is 'spaces')
                - naming_convention: 'snake_case', 'camelCase', or 'PascalCase'
                - quote_style: 'single' or 'double'
        """
        style_info = {
            'indent_style': 'spaces',
            'indent_size': 4,
            'naming_convention': 'snake_case',
            'quote_style': 'double'
        }
        
        indent_samples = []
        naming_samples = []
        quote_samples = {'single': 0, 'double': 0}
        
        for file_path in file_paths[:5]:  # Analyze up to 5 files
            content, result = self.file_ops.read_file(file_path)
            
            if not result.success:
                continue
            
            lines = content.split('\n')
            
            # Analyze indentation
            for line in lines:
                if line and (line[0] == ' ' or line[0] == '\t'):
                    # Count leading whitespace
                    indent = len(line) - len(line.lstrip())
                    if line[0] == '\t':
                        indent_samples.append(('tabs', 1))
                    else:
                        indent_samples.append(('spaces', indent))
            
            # Analyze naming conventions (look for function/class definitions)
            func_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
            class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[:(]'
            
            for match in re.finditer(func_pattern, content):
                naming_samples.append(match.group(1))
            
            for match in re.finditer(class_pattern, content):
                naming_samples.append(match.group(1))
            
            # Analyze quote style
            quote_samples['single'] += content.count("'")
            quote_samples['double'] += content.count('"')
        
        # Determine indent style
        if indent_samples:
            tabs_count = sum(1 for style, _ in indent_samples if style == 'tabs')
            spaces_count = sum(1 for style, _ in indent_samples if style == 'spaces')
            
            if tabs_count > spaces_count:
                style_info['indent_style'] = 'tabs'
            else:
                style_info['indent_style'] = 'spaces'
                # Calculate most common indent size
                space_indents = [size for style, size in indent_samples if style == 'spaces' and size > 0]
                if space_indents:
                    style_info['indent_size'] = max(set(space_indents), key=space_indents.count)
        
        # Determine naming convention
        if naming_samples:
            snake_case_count = sum(1 for name in naming_samples if '_' in name and name.islower())
            camel_case_count = sum(1 for name in naming_samples if name[0].islower() and any(c.isupper() for c in name))
            pascal_case_count = sum(1 for name in naming_samples if name[0].isupper())
            
            if snake_case_count >= camel_case_count and snake_case_count >= pascal_case_count:
                style_info['naming_convention'] = 'snake_case'
            elif pascal_case_count >= camel_case_count:
                style_info['naming_convention'] = 'PascalCase'
            else:
                style_info['naming_convention'] = 'camelCase'
        
        # Determine quote style
        if quote_samples['single'] > quote_samples['double']:
            style_info['quote_style'] = 'single'
        
        return style_info
    
    def _apply_line_edits(self, content: str, edits: List[Dict[str, Any]]) -> Optional[str]:
        """Apply precise line range edits to file content.
        
        Args:
            content: Original file content
            edits: List of edit operations, each with:
                - start_line: Starting line number (1-indexed)
                - end_line: Ending line number (1-indexed, inclusive)
                - new_text: Text to replace the line range with
                
        Returns:
            Modified content, or None if edits are invalid
        """
        try:
            lines = content.split('\n')
            
            # Sort edits by start_line in reverse order (edit from bottom to top)
            # This prevents line number shifts from affecting subsequent edits
            sorted_edits = sorted(edits, key=lambda e: e['start_line'], reverse=True)
            
            for edit in sorted_edits:
                start_line = edit['start_line']
                end_line = edit['end_line']
                new_text = edit['new_text']
                
                # Validate line numbers (1-indexed)
                if start_line < 1 or end_line < start_line or start_line > len(lines):
                    self.logger.error(f"Invalid line range: {start_line}-{end_line} (file has {len(lines)} lines)")
                    return None
                
                # Adjust end_line if it exceeds file length
                end_line = min(end_line, len(lines))
                
                # Convert to 0-indexed
                start_idx = start_line - 1
                end_idx = end_line  # end_line is inclusive, so no -1 needed for slice
                
                # Replace the line range with new text
                new_lines = new_text.split('\n')
                lines[start_idx:end_idx] = new_lines
            
            return '\n'.join(lines)
            
        except Exception as e:
            self.logger.error(f"Error applying line edits: {str(e)}")
            return None
    
    def _create_default_logger(self) -> logging.Logger:
        """Create a default logger for the CodeAgent.
        
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger('CodeAgent')
        logger.setLevel(logging.INFO)
        
        # Only add handler if none exist
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            
            logger.addHandler(handler)
        
        return logger
