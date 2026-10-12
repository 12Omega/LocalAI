"""Property-based tests for file content round-trip operations.

This module tests Property 8: File Content Round-Trip
**Validates: Requirements 9.2**

The property ensures that writing content to a file and reading it back
returns identical content (byte-for-byte identity).
"""

import os
import tempfile
import shutil
import uuid
from pathlib import Path
import pytest
from hypothesis import given, strategies as st, settings

from src.agents.file_operations import FileOperations


# Strategy for generating valid file names (avoiding problematic characters)
@st.composite
def valid_filename(draw):
    """Generate valid file names without problematic characters."""
    # Use alphanumeric, underscores, hyphens, and periods
    # Avoid reserved names and empty strings
    length = draw(st.integers(min_value=1, max_value=50))
    chars = st.sampled_from('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-')
    name = ''.join(draw(st.lists(chars, min_size=1, max_size=length)))
    
    # Add an extension
    extension = draw(st.sampled_from(['.txt', '.py', '.md', '.json', '.xml', '.log']))
    return name + extension


# Strategy for generating file content with various character types
file_content_strategy = st.one_of(
    st.text(min_size=0, max_size=10000),  # Unicode text
    st.binary().map(lambda b: b.decode('utf-8', errors='ignore')),  # Binary decoded as UTF-8
    st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Z', 'S')), min_size=0, max_size=5000),  # Various Unicode categories
    st.from_regex(r'[a-zA-Z0-9!@#$%^&*()_+={}\[\]:;"\'<>,.?/\\|\n\t ]*', fullmatch=True),  # ASCII with special chars
)


@pytest.mark.property
class TestFileContentRoundTrip:
    """Property-based tests for file content round-trip operations.
    
    Tag: Feature: local-ai-dev-environment, Property 8: File Content Round-Trip
    """
    
    def setup_method(self):
        """Create a temporary directory for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_ops = FileOperations(project_root=self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary directory after each test method."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @given(filename=valid_filename(), content=file_content_strategy)
    @settings(max_examples=100, deadline=None)
    def test_file_content_roundtrip_simple(self, filename, content):
        """Test that writing and reading a file returns identical content.
        
        **Validates: Requirements 9.2**
        
        Property: For any file path and content, writing the content to the file
        and then immediately reading the file SHALL return content that exactly
        matches the original content (byte-for-byte identity).
        
        Tag: Feature: local-ai-dev-environment, Property 8: File Content Round-Trip
        """
        # Make filename unique to avoid collisions across hypothesis examples
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Write content to file
        result = self.file_ops.create_file(unique_filename, content)
        assert result.success, f"Failed to create file: {result.message}"
        
        # Read content back
        read_content, read_result = self.file_ops.read_file(unique_filename)
        assert read_result.success, f"Failed to read file: {read_result.message}"
        
        # Verify content is identical
        assert read_content == content, (
            f"Content mismatch! Original length: {len(content)}, "
            f"Read length: {len(read_content)}"
        )
    
    @given(
        filename=valid_filename(),
        content=st.text(
            alphabet=st.characters(
                blacklist_characters='\x00',  # Exclude null bytes
                blacklist_categories=('Cs',)   # Exclude surrogates
            ),
            min_size=0,
            max_size=10000
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_file_content_roundtrip_with_special_chars(self, filename, content):
        """Test round-trip with special characters and Unicode.
        
        **Validates: Requirements 9.2**
        
        This test specifically focuses on content with special characters,
        newlines, tabs, and various Unicode characters to ensure proper
        encoding/decoding.
        
        Tag: Feature: local-ai-dev-environment, Property 8: File Content Round-Trip
        """
        # Make filename unique to avoid collisions
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Write content to file
        result = self.file_ops.create_file(unique_filename, content)
        assert result.success, f"Failed to create file: {result.message}"
        
        # Read content back
        read_content, read_result = self.file_ops.read_file(unique_filename)
        assert read_result.success, f"Failed to read file: {read_result.message}"
        
        # Verify exact byte-for-byte match
        assert read_content == content
        assert len(read_content) == len(content)
        assert type(read_content) == type(content)
    
    @given(
        subdir=st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
                min_size=1,
                max_size=10
            ).filter(lambda x: x.upper() not in ('CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9')),
            min_size=1,
            max_size=3
        ),
        filename=valid_filename(),
        content=file_content_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_file_content_roundtrip_nested_paths(self, subdir, filename, content):
        """Test round-trip with nested directory paths.
        
        **Validates: Requirements 9.2**
        
        Ensures that file operations work correctly with nested directory
        structures and that content is preserved regardless of path depth.
        
        Tag: Feature: local-ai-dev-environment, Property 8: File Content Round-Trip
        """
        # Create nested path with unique identifier
        unique_id = uuid.uuid4().hex
        nested_path = os.path.join(*subdir, f"{unique_id}_{filename}")
        
        # Write content to nested location
        result = self.file_ops.create_file(nested_path, content)
        assert result.success, f"Failed to create file: {result.message}"
        
        # Read content back
        read_content, read_result = self.file_ops.read_file(nested_path)
        assert read_result.success, f"Failed to read file: {read_result.message}"
        
        # Verify content is identical
        assert read_content == content
    
    @given(
        filename=valid_filename(),
        initial_content=file_content_strategy,
        updated_content=file_content_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_file_content_roundtrip_after_update(self, filename, initial_content, updated_content):
        """Test round-trip after updating file content.
        
        **Validates: Requirements 9.2**
        
        Ensures that updating a file and reading it back returns the new
        content exactly, not the old content.
        
        Tag: Feature: local-ai-dev-environment, Property 8: File Content Round-Trip
        """
        # Make filename unique
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Create file with initial content
        result = self.file_ops.create_file(unique_filename, initial_content)
        assert result.success, f"Failed to create file: {result.message}"
        
        # Update file with new content
        update_result = self.file_ops.update_file(unique_filename, updated_content)
        assert update_result.success, f"Failed to update file: {update_result.message}"
        
        # Read content back
        read_content, read_result = self.file_ops.read_file(unique_filename)
        assert read_result.success, f"Failed to read file: {read_result.message}"
        
        # Verify content matches the updated content, not initial content
        assert read_content == updated_content
        assert read_content != initial_content or initial_content == updated_content
    
    @given(content=st.text(min_size=0, max_size=1000))
    @settings(max_examples=100, deadline=None)
    def test_empty_and_whitespace_content(self, content):
        """Test round-trip with empty strings and whitespace-only content.
        
        **Validates: Requirements 9.2**
        
        Edge case testing for empty files and files containing only whitespace.
        
        Tag: Feature: local-ai-dev-environment, Property 8: File Content Round-Trip
        """
        # Use unique filename for each test run
        filename = f"test_whitespace_{uuid.uuid4().hex}.txt"
        
        # Write content
        result = self.file_ops.create_file(filename, content)
        assert result.success, f"Failed to create file: {result.message}"
        
        # Read content back
        read_content, read_result = self.file_ops.read_file(filename)
        assert read_result.success, f"Failed to read file: {read_result.message}"
        
        # Verify exact match (including empty strings)
        assert read_content == content
        assert len(read_content) == len(content)
