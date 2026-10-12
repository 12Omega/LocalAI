"""File operations module for Local AI Development Environment.

This module provides the FileOperations class that handles all file system
operations including create, read, update, delete, and move operations with
comprehensive error handling.

Requirements implemented:
- 9.1: Create new files with specified content
- 9.2: Read file contents
- 9.3: Modify existing files
- 9.4: Delete files when necessary
- 9.6: Move and rename files while updating references
- 9.7: Report specific errors for file operations
- 14.1: Provide descriptive error messages
- 14.3: Report specific permission issues
"""

import os
import shutil
import re
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass


@dataclass
class OperationResult:
    """Result of a file operation."""
    success: bool
    message: str
    error_type: Optional[str] = None  # permission, not_found, disk_full, etc.
    data: Optional[Dict[str, Any]] = None  # Optional data payload for operation results


class FileOperations:
    """Handles all file system operations with error handling.
    
    This class provides methods for creating, reading, updating, deleting,
    and moving files with comprehensive error handling for common failure
    scenarios including permission errors, file not found, and disk full.
    """
    
    def __init__(self, project_root: Optional[str] = None):
        """Initialize FileOperations.
        
        Args:
            project_root: Root directory for the project. If None, uses current directory.
        """
        self.project_root = project_root or os.getcwd()
    
    def create_file(self, path: str, content: str) -> OperationResult:
        """Create a new file with specified content.
        
        Args:
            path: Path to the file to create (absolute or relative to project_root)
            content: Content to write to the file
            
        Returns:
            OperationResult with success status and message
            
        Validates: Requirements 9.1, 14.1, 14.3
        """
        try:
            # Resolve path
            file_path = self._resolve_path(path)
            
            # Check if file already exists
            if file_path.exists():
                return OperationResult(
                    success=False,
                    message=f"File already exists: {file_path}",
                    error_type="file_exists"
                )
            
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content to file (newline='' preserves line endings exactly)
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                f.write(content)
            
            return OperationResult(
                success=True,
                message=f"File created successfully: {file_path}"
            )
            
        except PermissionError as e:
            return OperationResult(
                success=False,
                message=f"Permission denied when creating file '{path}': {str(e)}",
                error_type="permission"
            )
        except OSError as e:
            # Check for disk full error (errno 28 on Linux, errno 39 on some systems)
            if e.errno in (28, 39) or "No space left on device" in str(e):
                return OperationResult(
                    success=False,
                    message=f"Disk full when creating file '{path}': {str(e)}",
                    error_type="disk_full"
                )
            return OperationResult(
                success=False,
                message=f"OS error when creating file '{path}': {str(e)}",
                error_type="os_error"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Unexpected error when creating file '{path}': {str(e)}",
                error_type="unexpected"
            )
    
    def read_file(self, path: str) -> Tuple[Optional[str], OperationResult]:
        """Read file contents.
        
        Args:
            path: Path to the file to read (absolute or relative to project_root)
            
        Returns:
            Tuple of (file_content, OperationResult)
            If successful, file_content contains the file contents
            If failed, file_content is None
            
        Validates: Requirements 9.2, 14.1, 14.3
        """
        try:
            # Resolve path
            file_path = self._resolve_path(path)
            
            # Check if file exists
            if not file_path.exists():
                return None, OperationResult(
                    success=False,
                    message=f"File not found: {file_path}",
                    error_type="not_found"
                )
            
            # Check if it's a file (not a directory)
            if not file_path.is_file():
                return None, OperationResult(
                    success=False,
                    message=f"Path is not a file: {file_path}",
                    error_type="not_a_file"
                )
            
            # Read file content (newline='' preserves line endings exactly)
            with open(file_path, 'r', encoding='utf-8', newline='') as f:
                content = f.read()
            
            return content, OperationResult(
                success=True,
                message=f"File read successfully: {file_path}"
            )
            
        except PermissionError as e:
            return None, OperationResult(
                success=False,
                message=f"Permission denied when reading file '{path}': {str(e)}",
                error_type="permission"
            )
        except UnicodeDecodeError as e:
            return None, OperationResult(
                success=False,
                message=f"Cannot decode file '{path}' as UTF-8: {str(e)}",
                error_type="encoding"
            )
        except Exception as e:
            return None, OperationResult(
                success=False,
                message=f"Unexpected error when reading file '{path}': {str(e)}",
                error_type="unexpected"
            )
    
    def update_file(self, path: str, content: str) -> OperationResult:
        """Update existing file with new content.
        
        Args:
            path: Path to the file to update (absolute or relative to project_root)
            content: New content to write to the file
            
        Returns:
            OperationResult with success status and message
            
        Validates: Requirements 9.3, 14.1, 14.3
        """
        try:
            # Resolve path
            file_path = self._resolve_path(path)
            
            # Check if file exists
            if not file_path.exists():
                return OperationResult(
                    success=False,
                    message=f"File not found: {file_path}",
                    error_type="not_found"
                )
            
            # Check if it's a file (not a directory)
            if not file_path.is_file():
                return OperationResult(
                    success=False,
                    message=f"Path is not a file: {file_path}",
                    error_type="not_a_file"
                )
            
            # Write new content to file (newline='' preserves line endings exactly)
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                f.write(content)
            
            return OperationResult(
                success=True,
                message=f"File updated successfully: {file_path}"
            )
            
        except PermissionError as e:
            return OperationResult(
                success=False,
                message=f"Permission denied when updating file '{path}': {str(e)}",
                error_type="permission"
            )
        except OSError as e:
            # Check for disk full error
            if e.errno in (28, 39) or "No space left on device" in str(e):
                return OperationResult(
                    success=False,
                    message=f"Disk full when updating file '{path}': {str(e)}",
                    error_type="disk_full"
                )
            return OperationResult(
                success=False,
                message=f"OS error when updating file '{path}': {str(e)}",
                error_type="os_error"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Unexpected error when updating file '{path}': {str(e)}",
                error_type="unexpected"
            )
    
    def delete_file(self, path: str) -> OperationResult:
        """Delete a file.
        
        Args:
            path: Path to the file to delete (absolute or relative to project_root)
            
        Returns:
            OperationResult with success status and message
            
        Validates: Requirements 9.4, 14.1, 14.3
        """
        try:
            # Resolve path
            file_path = self._resolve_path(path)
            
            # Check if file exists
            if not file_path.exists():
                return OperationResult(
                    success=False,
                    message=f"File not found: {file_path}",
                    error_type="not_found"
                )
            
            # Check if it's a file (not a directory)
            if not file_path.is_file():
                return OperationResult(
                    success=False,
                    message=f"Path is not a file: {file_path}",
                    error_type="not_a_file"
                )
            
            # Delete the file
            file_path.unlink()
            
            return OperationResult(
                success=True,
                message=f"File deleted successfully: {file_path}"
            )
            
        except PermissionError as e:
            return OperationResult(
                success=False,
                message=f"Permission denied when deleting file '{path}': {str(e)}",
                error_type="permission"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Unexpected error when deleting file '{path}': {str(e)}",
                error_type="unexpected"
            )
    
    def move_file(self, src: str, dst: str) -> OperationResult:
        """Move or rename a file while updating references.
        
        This method moves a file from src to dst and attempts to update
        import statements and references in other files that point to the
        moved file.
        
        Args:
            src: Source path (absolute or relative to project_root)
            dst: Destination path (absolute or relative to project_root)
            
        Returns:
            OperationResult with success status and message
            
        Validates: Requirements 9.6, 9.7, 14.1, 14.3
        """
        try:
            # Resolve paths
            src_path = self._resolve_path(src)
            dst_path = self._resolve_path(dst)
            
            # Check if source file exists
            if not src_path.exists():
                return OperationResult(
                    success=False,
                    message=f"Source file not found: {src_path}",
                    error_type="not_found"
                )
            
            # Check if source is a file (not a directory)
            if not src_path.is_file():
                return OperationResult(
                    success=False,
                    message=f"Source path is not a file: {src_path}",
                    error_type="not_a_file"
                )
            
            # Check if destination already exists
            if dst_path.exists():
                return OperationResult(
                    success=False,
                    message=f"Destination already exists: {dst_path}",
                    error_type="file_exists"
                )
            
            # Create destination parent directories if needed
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Update references before moving
            references_updated = self._update_references(src_path, dst_path)
            
            # Move the file
            shutil.move(str(src_path), str(dst_path))
            
            message = f"File moved successfully from {src_path} to {dst_path}"
            if references_updated > 0:
                message += f" ({references_updated} references updated)"
            
            return OperationResult(
                success=True,
                message=message
            )
            
        except PermissionError as e:
            return OperationResult(
                success=False,
                message=f"Permission denied when moving file from '{src}' to '{dst}': {str(e)}",
                error_type="permission"
            )
        except OSError as e:
            # Check for disk full error
            if e.errno in (28, 39) or "No space left on device" in str(e):
                return OperationResult(
                    success=False,
                    message=f"Disk full when moving file from '{src}' to '{dst}': {str(e)}",
                    error_type="disk_full"
                )
            return OperationResult(
                success=False,
                message=f"OS error when moving file from '{src}' to '{dst}': {str(e)}",
                error_type="os_error"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Unexpected error when moving file from '{src}' to '{dst}': {str(e)}",
                error_type="unexpected"
            )
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve a path to an absolute Path object.
        
        Args:
            path: Path string (absolute or relative to project_root)
            
        Returns:
            Absolute Path object
        """
        path_obj = Path(path)
        if path_obj.is_absolute():
            return path_obj
        return Path(self.project_root) / path_obj
    
    def _update_references(self, old_path: Path, new_path: Path) -> int:
        """Update import statements and references to a moved file.
        
        Searches through project files to find references to the old file path
        and updates them to point to the new path.
        
        Args:
            old_path: Original file path
            new_path: New file path
            
        Returns:
            Number of files where references were updated
        """
        updated_count = 0
        
        try:
            # Get relative paths for import statement matching
            project_root = Path(self.project_root)
            old_relative = old_path.relative_to(project_root)
            new_relative = new_path.relative_to(project_root)
            
            # Convert to module paths (replace path separators with dots, remove extension)
            old_module = str(old_relative).replace(os.sep, '.').replace('.py', '')
            new_module = str(new_relative).replace(os.sep, '.').replace('.py', '')
            
            # Search for Python files in the project
            for file_path in project_root.rglob('*.py'):
                if file_path == old_path or file_path == new_path:
                    continue
                
                try:
                    content = file_path.read_text(encoding='utf-8')
                    original_content = content
                    
                    # Update import statements
                    # Match: import old.module
                    content = re.sub(
                        r'\bimport\s+' + re.escape(old_module) + r'\b',
                        'import ' + new_module,
                        content
                    )
                    
                    # Match: from old.module import ...
                    content = re.sub(
                        r'\bfrom\s+' + re.escape(old_module) + r'\b',
                        'from ' + new_module,
                        content
                    )
                    
                    # Match: from parent import old_filename
                    old_name = old_path.stem
                    new_name = new_path.stem
                    if old_path.parent == new_path.parent and old_name != new_name:
                        parent_module = str(old_relative.parent).replace(os.sep, '.')
                        content = re.sub(
                            r'(\bfrom\s+' + re.escape(parent_module) + r'\s+import\s+.*\b)' + 
                            re.escape(old_name) + r'\b',
                            r'\1' + new_name,
                            content
                        )
                    
                    # If content changed, write it back
                    if content != original_content:
                        file_path.write_text(content, encoding='utf-8')
                        updated_count += 1
                        
                except Exception:
                    # Skip files that can't be processed
                    continue
            
        except Exception:
            # If reference updating fails, don't fail the entire move operation
            pass
        
        return updated_count
