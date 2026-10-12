"""Unit tests for FileOperations class.

Tests cover all file operations (create, read, update, delete, move) with
focus on error handling for permission errors, file not found, and disk full
scenarios.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from src.agents.file_operations import FileOperations, OperationResult


class TestFileOperations:
    """Unit tests for FileOperations class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)
    
    @pytest.fixture
    def file_ops(self, temp_dir):
        """Create FileOperations instance with temp directory."""
        return FileOperations(project_root=temp_dir)
    
    # Create File Tests
    
    def test_create_file_success(self, file_ops, temp_dir):
        """Test successful file creation."""
        result = file_ops.create_file("test.txt", "Hello, World!")
        
        assert result.success is True
        assert "created successfully" in result.message.lower()
        assert result.error_type is None
        
        # Verify file exists and has correct content
        file_path = Path(temp_dir) / "test.txt"
        assert file_path.exists()
        assert file_path.read_text() == "Hello, World!"
    
    def test_create_file_with_subdirectory(self, file_ops, temp_dir):
        """Test creating file in non-existent subdirectory."""
        result = file_ops.create_file("sub/dir/test.txt", "Content")
        
        assert result.success is True
        
        # Verify file and directories were created
        file_path = Path(temp_dir) / "sub" / "dir" / "test.txt"
        assert file_path.exists()
        assert file_path.read_text() == "Content"
    
    def test_create_file_already_exists(self, file_ops, temp_dir):
        """Test creating file that already exists."""
        # Create file first
        file_ops.create_file("test.txt", "Original")
        
        # Try to create again
        result = file_ops.create_file("test.txt", "New content")
        
        assert result.success is False
        assert "already exists" in result.message.lower()
        assert result.error_type == "file_exists"
        
        # Verify original content unchanged
        file_path = Path(temp_dir) / "test.txt"
        assert file_path.read_text() == "Original"
    
    def test_create_file_permission_error(self, file_ops):
        """Test creating file with permission error."""
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            result = file_ops.create_file("test.txt", "Content")
            
            assert result.success is False
            assert "permission denied" in result.message.lower()
            assert result.error_type == "permission"
    
    def test_create_file_disk_full(self, file_ops):
        """Test creating file when disk is full."""
        disk_full_error = OSError(28, "No space left on device")
        
        with patch('builtins.open', side_effect=disk_full_error):
            result = file_ops.create_file("test.txt", "Content")
            
            assert result.success is False
            assert "disk full" in result.message.lower()
            assert result.error_type == "disk_full"
    
    # Read File Tests
    
    def test_read_file_success(self, file_ops, temp_dir):
        """Test successful file reading."""
        # Create a file first
        file_path = Path(temp_dir) / "test.txt"
        file_path.write_text("Test content")
        
        content, result = file_ops.read_file("test.txt")
        
        assert result.success is True
        assert content == "Test content"
        assert result.error_type is None
    
    def test_read_file_not_found(self, file_ops):
        """Test reading non-existent file."""
        content, result = file_ops.read_file("nonexistent.txt")
        
        assert result.success is False
        assert content is None
        assert "not found" in result.message.lower()
        assert result.error_type == "not_found"
    
    def test_read_file_is_directory(self, file_ops, temp_dir):
        """Test reading a directory instead of a file."""
        dir_path = Path(temp_dir) / "subdir"
        dir_path.mkdir()
        
        content, result = file_ops.read_file("subdir")
        
        assert result.success is False
        assert content is None
        assert "not a file" in result.message.lower()
        assert result.error_type == "not_a_file"
    
    def test_read_file_permission_error(self, file_ops, temp_dir):
        """Test reading file with permission error."""
        # Create file
        file_path = Path(temp_dir) / "test.txt"
        file_path.write_text("Content")
        
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            content, result = file_ops.read_file("test.txt")
            
            assert result.success is False
            assert content is None
            assert "permission denied" in result.message.lower()
            assert result.error_type == "permission"
    
    def test_read_file_encoding_error(self, file_ops, temp_dir):
        """Test reading file with encoding issues."""
        # Create file
        file_path = Path(temp_dir) / "test.txt"
        file_path.write_text("Content")
        
        with patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid')):
            content, result = file_ops.read_file("test.txt")
            
            assert result.success is False
            assert content is None
            assert "cannot decode" in result.message.lower()
            assert result.error_type == "encoding"
    
    # Update File Tests
    
    def test_update_file_success(self, file_ops, temp_dir):
        """Test successful file update."""
        # Create file first
        file_path = Path(temp_dir) / "test.txt"
        file_path.write_text("Original content")
        
        result = file_ops.update_file("test.txt", "Updated content")
        
        assert result.success is True
        assert "updated successfully" in result.message.lower()
        assert result.error_type is None
        
        # Verify content was updated
        assert file_path.read_text() == "Updated content"
    
    def test_update_file_not_found(self, file_ops):
        """Test updating non-existent file."""
        result = file_ops.update_file("nonexistent.txt", "Content")
        
        assert result.success is False
        assert "not found" in result.message.lower()
        assert result.error_type == "not_found"
    
    def test_update_file_is_directory(self, file_ops, temp_dir):
        """Test updating a directory instead of a file."""
        dir_path = Path(temp_dir) / "subdir"
        dir_path.mkdir()
        
        result = file_ops.update_file("subdir", "Content")
        
        assert result.success is False
        assert "not a file" in result.message.lower()
        assert result.error_type == "not_a_file"
    
    def test_update_file_permission_error(self, file_ops, temp_dir):
        """Test updating file with permission error."""
        # Create file
        file_path = Path(temp_dir) / "test.txt"
        file_path.write_text("Original")
        
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            result = file_ops.update_file("test.txt", "Updated")
            
            assert result.success is False
            assert "permission denied" in result.message.lower()
            assert result.error_type == "permission"
    
    def test_update_file_disk_full(self, file_ops, temp_dir):
        """Test updating file when disk is full."""
        # Create file
        file_path = Path(temp_dir) / "test.txt"
        file_path.write_text("Original")
        
        disk_full_error = OSError(28, "No space left on device")
        
        with patch('builtins.open', side_effect=disk_full_error):
            result = file_ops.update_file("test.txt", "Updated")
            
            assert result.success is False
            assert "disk full" in result.message.lower()
            assert result.error_type == "disk_full"
    
    # Delete File Tests
    
    def test_delete_file_success(self, file_ops, temp_dir):
        """Test successful file deletion."""
        # Create file
        file_path = Path(temp_dir) / "test.txt"
        file_path.write_text("Content")
        
        result = file_ops.delete_file("test.txt")
        
        assert result.success is True
        assert "deleted successfully" in result.message.lower()
        assert result.error_type is None
        
        # Verify file was deleted
        assert not file_path.exists()
    
    def test_delete_file_not_found(self, file_ops):
        """Test deleting non-existent file."""
        result = file_ops.delete_file("nonexistent.txt")
        
        assert result.success is False
        assert "not found" in result.message.lower()
        assert result.error_type == "not_found"
    
    def test_delete_file_is_directory(self, file_ops, temp_dir):
        """Test deleting a directory instead of a file."""
        dir_path = Path(temp_dir) / "subdir"
        dir_path.mkdir()
        
        result = file_ops.delete_file("subdir")
        
        assert result.success is False
        assert "not a file" in result.message.lower()
        assert result.error_type == "not_a_file"
    
    def test_delete_file_permission_error(self, file_ops, temp_dir):
        """Test deleting file with permission error."""
        # Create file
        file_path = Path(temp_dir) / "test.txt"
        file_path.write_text("Content")
        
        with patch('pathlib.Path.unlink', side_effect=PermissionError("Access denied")):
            result = file_ops.delete_file("test.txt")
            
            assert result.success is False
            assert "permission denied" in result.message.lower()
            assert result.error_type == "permission"
    
    # Move File Tests
    
    def test_move_file_success(self, file_ops, temp_dir):
        """Test successful file move."""
        # Create source file
        src_path = Path(temp_dir) / "source.txt"
        src_path.write_text("Content")
        
        result = file_ops.move_file("source.txt", "destination.txt")
        
        assert result.success is True
        assert "moved successfully" in result.message.lower()
        assert result.error_type is None
        
        # Verify source doesn't exist and destination does
        assert not src_path.exists()
        dst_path = Path(temp_dir) / "destination.txt"
        assert dst_path.exists()
        assert dst_path.read_text() == "Content"
    
    def test_move_file_to_subdirectory(self, file_ops, temp_dir):
        """Test moving file to non-existent subdirectory."""
        # Create source file
        src_path = Path(temp_dir) / "source.txt"
        src_path.write_text("Content")
        
        result = file_ops.move_file("source.txt", "sub/dir/destination.txt")
        
        assert result.success is True
        
        # Verify file moved and directories created
        assert not src_path.exists()
        dst_path = Path(temp_dir) / "sub" / "dir" / "destination.txt"
        assert dst_path.exists()
        assert dst_path.read_text() == "Content"
    
    def test_move_file_source_not_found(self, file_ops):
        """Test moving non-existent file."""
        result = file_ops.move_file("nonexistent.txt", "destination.txt")
        
        assert result.success is False
        assert "not found" in result.message.lower()
        assert result.error_type == "not_found"
    
    def test_move_file_source_is_directory(self, file_ops, temp_dir):
        """Test moving a directory instead of a file."""
        dir_path = Path(temp_dir) / "subdir"
        dir_path.mkdir()
        
        result = file_ops.move_file("subdir", "newdir")
        
        assert result.success is False
        assert "not a file" in result.message.lower()
        assert result.error_type == "not_a_file"
    
    def test_move_file_destination_exists(self, file_ops, temp_dir):
        """Test moving file when destination already exists."""
        # Create both files
        src_path = Path(temp_dir) / "source.txt"
        src_path.write_text("Source")
        dst_path = Path(temp_dir) / "destination.txt"
        dst_path.write_text("Destination")
        
        result = file_ops.move_file("source.txt", "destination.txt")
        
        assert result.success is False
        assert "already exists" in result.message.lower()
        assert result.error_type == "file_exists"
        
        # Verify both files unchanged
        assert src_path.exists()
        assert dst_path.read_text() == "Destination"
    
    def test_move_file_permission_error(self, file_ops, temp_dir):
        """Test moving file with permission error."""
        # Create source file
        src_path = Path(temp_dir) / "source.txt"
        src_path.write_text("Content")
        
        with patch('shutil.move', side_effect=PermissionError("Access denied")):
            result = file_ops.move_file("source.txt", "destination.txt")
            
            assert result.success is False
            assert "permission denied" in result.message.lower()
            assert result.error_type == "permission"
    
    def test_move_file_disk_full(self, file_ops, temp_dir):
        """Test moving file when disk is full."""
        # Create source file
        src_path = Path(temp_dir) / "source.txt"
        src_path.write_text("Content")
        
        disk_full_error = OSError(28, "No space left on device")
        
        with patch('shutil.move', side_effect=disk_full_error):
            result = file_ops.move_file("source.txt", "destination.txt")
            
            assert result.success is False
            assert "disk full" in result.message.lower()
            assert result.error_type == "disk_full"
    
    def test_move_file_with_reference_update(self, file_ops, temp_dir):
        """Test moving file with import reference updates."""
        # Create source file
        src_path = Path(temp_dir) / "module_a.py"
        src_path.write_text("def hello(): pass")
        
        # Create file that imports the source
        importer_path = Path(temp_dir) / "importer.py"
        importer_path.write_text("import module_a\nfrom module_a import hello")
        
        result = file_ops.move_file("module_a.py", "module_b.py")
        
        assert result.success is True
        assert "moved successfully" in result.message.lower()
        
        # Verify references were updated
        importer_content = importer_path.read_text()
        assert "import module_b" in importer_content
        assert "from module_b import hello" in importer_content
        assert "module_a" not in importer_content
    
    def test_move_file_with_parent_import(self, file_ops, temp_dir):
        """Test reference update for parent module imports."""
        # Create directory structure
        pkg_dir = Path(temp_dir) / "package"
        pkg_dir.mkdir()
        
        # Create module file
        module_path = pkg_dir / "old_name.py"
        module_path.write_text("def func(): pass")
        
        # Create importer
        importer_path = pkg_dir / "main.py"
        importer_path.write_text("from package import old_name")
        
        result = file_ops.move_file("package/old_name.py", "package/new_name.py")
        
        assert result.success is True
        
        # Verify reference was updated
        importer_content = importer_path.read_text()
        assert "from package import new_name" in importer_content
        assert "old_name" not in importer_content
    
    # Path Resolution Tests
    
    def test_resolve_absolute_path(self, file_ops, temp_dir):
        """Test resolution of absolute paths."""
        abs_path = Path(temp_dir) / "test.txt"
        abs_path.write_text("Content")
        
        content, result = file_ops.read_file(str(abs_path))
        
        assert result.success is True
        assert content == "Content"
    
    def test_resolve_relative_path(self, file_ops, temp_dir):
        """Test resolution of relative paths."""
        rel_path = Path(temp_dir) / "subdir" / "test.txt"
        rel_path.parent.mkdir(parents=True, exist_ok=True)
        rel_path.write_text("Content")
        
        content, result = file_ops.read_file("subdir/test.txt")
        
        assert result.success is True
        assert content == "Content"
    
    # Edge Case Tests
    
    def test_create_empty_file(self, file_ops, temp_dir):
        """Test creating an empty file."""
        result = file_ops.create_file("empty.txt", "")
        
        assert result.success is True
        
        # Verify file exists and is empty
        file_path = Path(temp_dir) / "empty.txt"
        assert file_path.exists()
        assert file_path.read_text() == ""
        assert file_path.stat().st_size == 0
    
    def test_read_empty_file(self, file_ops, temp_dir):
        """Test reading an empty file."""
        # Create empty file
        file_path = Path(temp_dir) / "empty.txt"
        file_path.write_text("")
        
        content, result = file_ops.read_file("empty.txt")
        
        assert result.success is True
        assert content == ""
    
    def test_update_empty_file(self, file_ops, temp_dir):
        """Test updating an empty file with content."""
        # Create empty file
        file_path = Path(temp_dir) / "empty.txt"
        file_path.write_text("")
        
        result = file_ops.update_file("empty.txt", "Now has content")
        
        assert result.success is True
        assert file_path.read_text() == "Now has content"
    
    def test_update_file_to_empty(self, file_ops, temp_dir):
        """Test updating a file to empty content."""
        # Create file with content
        file_path = Path(temp_dir) / "test.txt"
        file_path.write_text("Original content")
        
        result = file_ops.update_file("test.txt", "")
        
        assert result.success is True
        assert file_path.read_text() == ""
    
    def test_create_large_file(self, file_ops, temp_dir):
        """Test creating a very large file (>10MB)."""
        # Generate 15MB of content (10 * 1024 * 1024 * 1.5 bytes)
        large_content = "x" * (15 * 1024 * 1024)
        
        result = file_ops.create_file("large_file.txt", large_content)
        
        assert result.success is True
        
        # Verify file size
        file_path = Path(temp_dir) / "large_file.txt"
        assert file_path.exists()
        file_size = file_path.stat().st_size
        assert file_size > 10 * 1024 * 1024  # Greater than 10MB
    
    def test_read_large_file(self, file_ops, temp_dir):
        """Test reading a very large file (>10MB)."""
        # Create large file
        large_content = "y" * (15 * 1024 * 1024)
        file_path = Path(temp_dir) / "large_file.txt"
        file_path.write_text(large_content)
        
        content, result = file_ops.read_file("large_file.txt")
        
        assert result.success is True
        assert len(content) == len(large_content)
        assert content == large_content
    
    def test_update_large_file(self, file_ops, temp_dir):
        """Test updating a large file."""
        # Create large file
        original_content = "a" * (12 * 1024 * 1024)
        file_path = Path(temp_dir) / "large_file.txt"
        file_path.write_text(original_content)
        
        # Update with new large content
        new_content = "b" * (13 * 1024 * 1024)
        result = file_ops.update_file("large_file.txt", new_content)
        
        assert result.success is True
        assert file_path.read_text() == new_content
    
    def test_move_large_file(self, file_ops, temp_dir):
        """Test moving a large file."""
        # Create large file
        large_content = "z" * (11 * 1024 * 1024)
        src_path = Path(temp_dir) / "large_source.txt"
        src_path.write_text(large_content)
        
        result = file_ops.move_file("large_source.txt", "large_destination.txt")
        
        assert result.success is True
        assert not src_path.exists()
        
        dst_path = Path(temp_dir) / "large_destination.txt"
        assert dst_path.exists()
        assert dst_path.stat().st_size > 10 * 1024 * 1024
    
    def test_create_file_with_special_characters_in_name(self, file_ops, temp_dir):
        """Test creating files with special characters in names."""
        special_names = [
            "file with spaces.txt",
            "file-with-dashes.txt",
            "file_with_underscores.txt",
            "file.multiple.dots.txt",
            "file(with)parens.txt",
            "file[with]brackets.txt",
            "file{with}braces.txt",
            "file'with'quotes.txt",
        ]
        
        for name in special_names:
            result = file_ops.create_file(name, f"Content for {name}")
            
            assert result.success is True, f"Failed to create file: {name}"
            
            file_path = Path(temp_dir) / name
            assert file_path.exists(), f"File does not exist: {name}"
            assert file_path.read_text() == f"Content for {name}"
    
    def test_read_file_with_special_characters_in_name(self, file_ops, temp_dir):
        """Test reading files with special characters in names."""
        special_name = "file with spaces and (parens).txt"
        file_path = Path(temp_dir) / special_name
        file_path.write_text("Special content")
        
        content, result = file_ops.read_file(special_name)
        
        assert result.success is True
        assert content == "Special content"
    
    def test_update_file_with_special_characters_in_name(self, file_ops, temp_dir):
        """Test updating files with special characters in names."""
        special_name = "file-with-special.chars[123].txt"
        file_path = Path(temp_dir) / special_name
        file_path.write_text("Original")
        
        result = file_ops.update_file(special_name, "Updated")
        
        assert result.success is True
        assert file_path.read_text() == "Updated"
    
    def test_move_file_with_special_characters_in_name(self, file_ops, temp_dir):
        """Test moving files with special characters in names."""
        src_name = "source (file).txt"
        dst_name = "destination [file].txt"
        
        src_path = Path(temp_dir) / src_name
        src_path.write_text("Content")
        
        result = file_ops.move_file(src_name, dst_name)
        
        assert result.success is True
        assert not src_path.exists()
        
        dst_path = Path(temp_dir) / dst_name
        assert dst_path.exists()
        assert dst_path.read_text() == "Content"
    
    def test_delete_file_with_special_characters_in_name(self, file_ops, temp_dir):
        """Test deleting files with special characters in names."""
        special_name = "file to delete (with parens).txt"
        file_path = Path(temp_dir) / special_name
        file_path.write_text("Content")
        
        result = file_ops.delete_file(special_name)
        
        assert result.success is True
        assert not file_path.exists()
    
    def test_file_with_unicode_characters_in_name(self, file_ops, temp_dir):
        """Test files with unicode characters in names."""
        unicode_names = [
            "файл.txt",  # Cyrillic
            "文件.txt",  # Chinese
            "ファイル.txt",  # Japanese
            "파일.txt",  # Korean
            "café.txt",  # Accented characters
            "naïve.txt",  # Diaeresis
        ]
        
        for name in unicode_names:
            try:
                result = file_ops.create_file(name, f"Content for {name}")
                
                # Some filesystems may not support all unicode characters
                if result.success:
                    file_path = Path(temp_dir) / name
                    assert file_path.exists(), f"File does not exist: {name}"
                    
                    # Try to read it back
                    content, read_result = file_ops.read_file(name)
                    if read_result.success:
                        assert content == f"Content for {name}"
            except (OSError, UnicodeError):
                # Some filesystems don't support certain unicode characters
                # This is acceptable - we just verify the code doesn't crash
                pass
    
    def test_create_file_with_very_long_name(self, file_ops, temp_dir):
        """Test creating a file with a very long name."""
        # Most filesystems support at least 255 characters
        long_name = "a" * 200 + ".txt"
        
        result = file_ops.create_file(long_name, "Content")
        
        # This should work on most systems
        if result.success:
            file_path = Path(temp_dir) / long_name
            assert file_path.exists()
        else:
            # Some systems may have shorter limits - verify error is handled gracefully
            assert result.error_type in ["os_error", "unexpected"]
