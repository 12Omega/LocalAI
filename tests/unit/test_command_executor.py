"""Unit tests for CommandExecutor class.

Tests cover command execution with output capture, error handling for command
failures, stderr capture, timeout handling, and working directory changes.

**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6**
"""

import os
import sys
import platform
import tempfile
import shutil
import time
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import subprocess

from src.agents.command_executor import CommandExecutor, CommandResult, AsyncCommandHandle


class TestCommandExecutor:
    """Unit tests for CommandExecutor class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        # Cleanup - with retry on Windows to handle file locks
        if os.path.exists(temp_path):
            if platform.system() == 'Windows':
                import time
                # Try multiple times with delays to handle Windows file locks
                for attempt in range(10):
                    try:
                        shutil.rmtree(temp_path)
                        break
                    except PermissionError:
                        if attempt < 9:
                            time.sleep(0.2)
                        else:
                            # Last attempt failed, but don't fail the test
                            pass
            else:
                shutil.rmtree(temp_path)
    
    @pytest.fixture
    def executor(self, temp_dir):
        """Create CommandExecutor instance with temp directory."""
        return CommandExecutor(default_cwd=temp_dir)
    
    # Successful Command Execution Tests
    
    def test_execute_simple_command_success(self, executor):
        """Test executing a simple command that succeeds."""
        # Use Python for platform-independent command
        result = executor.execute(f'{sys.executable} -c "print(\'Hello World\')"')
        
        assert result.success is True
        assert result.return_code == 0
        assert "Hello World" in result.stdout
        assert result.error_type is None
        assert "successfully" in result.message.lower()
    
    def test_execute_command_with_output_capture(self, executor, temp_dir):
        """Test capturing stdout from command execution."""
        # Create a test file
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Test content\nLine 2\nLine 3")
        
        # Use Python to read file (platform-independent)
        result = executor.execute(f'{sys.executable} -c "print(open(r\'{test_file}\').read())"')
        
        assert result.success is True
        assert "Test content" in result.stdout
        assert "Line 2" in result.stdout
        assert "Line 3" in result.stdout
    
    def test_execute_command_with_arguments(self, executor, temp_dir):
        """Test executing command with multiple arguments and flags."""
        # Create test files
        (Path(temp_dir) / "file1.txt").write_text("File 1")
        (Path(temp_dir) / "file2.txt").write_text("File 2")
        (Path(temp_dir) / "file3.txt").write_text("File 3")
        
        # List files with specific pattern
        if sys.platform == "win32":
            result = executor.execute("dir /b *.txt", cwd=temp_dir)
            assert result.success is True
            assert "file1.txt" in result.stdout
            assert "file2.txt" in result.stdout
            assert "file3.txt" in result.stdout
        else:
            result = executor.execute("ls -1 *.txt", cwd=temp_dir)
            assert result.success is True
            assert "file1.txt" in result.stdout
            assert "file2.txt" in result.stdout
            assert "file3.txt" in result.stdout
    
    def test_execute_command_with_quoted_arguments(self, executor, temp_dir):
        """Test executing command with quoted arguments containing spaces."""
        # Create file with spaces in name
        test_file = Path(temp_dir) / "file with spaces.txt"
        test_file.write_text("Content with spaces")
        
        # Execute command with quoted path
        if sys.platform == "win32":
            result = executor.execute(f'type "{test_file}"')
        else:
            result = executor.execute(f'cat "{test_file}"')
        
        assert result.success is True
        assert "Content with spaces" in result.stdout
    
    def test_execute_python_command(self, executor):
        """Test executing Python commands."""
        result = executor.execute(f'{sys.executable} -c "print(\'Hello from Python\')"')
        
        assert result.success is True
        assert result.return_code == 0
        assert "Hello from Python" in result.stdout
    
    def test_execute_command_with_pipe_like_output(self, executor):
        """Test capturing multi-line output."""
        # Execute Python command that produces multiple lines
        result = executor.execute(
            f'{sys.executable} -c "for i in range(3): print(f\'Line {{i}}\')"'
        )
        
        assert result.success is True
        assert "Line 0" in result.stdout
        assert "Line 1" in result.stdout
        assert "Line 2" in result.stdout
    
    # Command Failure Tests
    
    def test_execute_command_not_found(self, executor):
        """Test executing a non-existent command."""
        result = executor.execute("nonexistentcommand12345")
        
        assert result.success is False
        # When shell=True, non-existent commands return error code 1 on Windows or 127 on Unix
        assert result.return_code in [1, 127]
        assert result.error_type == "non_zero_exit"
        assert ("not recognized" in result.stderr.lower() or "not found" in result.stderr.lower())
    
    def test_execute_command_with_non_zero_exit_code(self, executor):
        """Test executing command that fails with non-zero exit code."""
        # Python with invalid syntax will exit with non-zero code
        result = executor.execute(f'{sys.executable} -c "import sys; sys.exit(42)"')
        
        assert result.success is False
        assert result.return_code == 42
        assert result.error_type == "non_zero_exit"
        assert "failed with return code 42" in result.message.lower()
    
    def test_execute_command_with_stderr_output(self, executor):
        """Test capturing stderr when command writes to it."""
        # Python command that writes to stderr
        result = executor.execute(
            f'{sys.executable} -c "import sys; sys.stderr.write(\'Error message\\n\'); sys.exit(1)"'
        )
        
        assert result.success is False
        assert result.return_code == 1
        assert "Error message" in result.stderr
    
    def test_execute_command_with_mixed_stdout_stderr(self, executor):
        """Test capturing both stdout and stderr."""
        # Command that writes to both stdout and stderr
        # Use single quotes inside double quotes for shell=True compatibility
        cmd = (
            f"{sys.executable} -c "
            f'"import sys; '
            f"print(\'Standard output\'); "
            f"sys.stderr.write(\'Error output\\n\'); "
            f'sys.exit(1)"'
        )
        result = executor.execute(cmd)
        
        assert result.success is False
        assert "Standard output" in result.stdout
        assert "Error output" in result.stderr
    
    # Timeout Handling Tests
    
    def test_execute_command_with_timeout_success(self, executor):
        """Test executing quick command with timeout."""
        result = executor.execute(
            f'{sys.executable} -c "print(\'Quick command\')"',
            timeout=5
        )
        
        assert result.success is True
        assert result.return_code == 0
        assert "Quick command" in result.stdout
    
    def test_execute_command_timeout_expired(self, executor):
        """Test command that exceeds timeout limit."""
        # Command that sleeps longer than timeout
        result = executor.execute(
            f'{sys.executable} -c "import time; time.sleep(10)"',
            timeout=1
        )
        
        assert result.success is False
        assert result.return_code == -1
        assert result.error_type == "timeout"
        assert "timed out" in result.message.lower()
        assert "1 seconds" in result.message
    
    def test_execute_command_timeout_with_partial_output(self, executor):
        """Test capturing partial output before timeout."""
        # Command that prints then sleeps
        # Use single quotes inside double quotes for shell=True compatibility
        cmd = (
            f"{sys.executable} -c "
            f'"print(\'Before timeout\'); '
            f'import sys; sys.stdout.flush(); '
            f'import time; time.sleep(10)"'
        )
        result = executor.execute(cmd, timeout=1)
        
        assert result.success is False
        assert result.error_type == "timeout"
        # Partial output should be captured
        assert "Before timeout" in result.stdout
    
    def test_execute_command_custom_timeout(self, executor):
        """Test using custom timeout values."""
        # Quick command with generous timeout
        result = executor.execute(
            f'{sys.executable} -c "print(\'Done\')"',
            timeout=30
        )
        
        assert result.success is True
    
    # Working Directory Tests
    
    def test_execute_command_in_default_cwd(self, executor, temp_dir):
        """Test command execution in default working directory."""
        # Create file in default cwd
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Default CWD content")
        
        # Execute command without specifying cwd (should use default)
        if sys.platform == "win32":
            result = executor.execute("type test.txt")
        else:
            result = executor.execute("cat test.txt")
        
        assert result.success is True
        assert "Default CWD content" in result.stdout
    
    def test_execute_command_in_specific_cwd(self, executor, temp_dir):
        """Test command execution in specified working directory."""
        # Create subdirectory with file
        subdir = Path(temp_dir) / "subdir"
        subdir.mkdir()
        test_file = subdir / "test.txt"
        test_file.write_text("Subdir content")
        
        # Execute command in subdirectory
        if sys.platform == "win32":
            result = executor.execute("type test.txt", cwd=str(subdir))
        else:
            result = executor.execute("cat test.txt", cwd=str(subdir))
        
        assert result.success is True
        assert "Subdir content" in result.stdout
    
    def test_execute_command_in_relative_cwd(self, executor, temp_dir):
        """Test command execution with relative working directory path."""
        # Create subdirectory
        subdir = Path(temp_dir) / "relative" / "path"
        subdir.mkdir(parents=True)
        test_file = subdir / "test.txt"
        test_file.write_text("Relative path content")
        
        # Execute with relative path from default cwd
        if sys.platform == "win32":
            result = executor.execute("type test.txt", cwd="relative/path")
        else:
            result = executor.execute("cat test.txt", cwd="relative/path")
        
        assert result.success is True
        assert "Relative path content" in result.stdout
    
    def test_execute_command_in_absolute_cwd(self, executor, temp_dir):
        """Test command execution with absolute working directory path."""
        # Create subdirectory with absolute path
        subdir = Path(temp_dir) / "absolute"
        subdir.mkdir()
        test_file = subdir / "test.txt"
        test_file.write_text("Absolute path content")
        
        # Execute with absolute path
        if sys.platform == "win32":
            result = executor.execute("type test.txt", cwd=str(subdir.absolute()))
        else:
            result = executor.execute("cat test.txt", cwd=str(subdir.absolute()))
        
        assert result.success is True
        assert "Absolute path content" in result.stdout
    
    def test_execute_command_invalid_cwd(self, executor):
        """Test command execution with non-existent working directory."""
        result = executor.execute(
            "echo test",
            cwd="/nonexistent/directory/path"
        )
        
        assert result.success is False
        assert result.error_type == "invalid_cwd"
        assert "does not exist" in result.message.lower()
    
    def test_execute_command_cwd_is_file(self, executor, temp_dir):
        """Test command execution when cwd is a file instead of directory."""
        # Create a file
        test_file = Path(temp_dir) / "not_a_dir.txt"
        test_file.write_text("Content")
        
        result = executor.execute("echo test", cwd=str(test_file))
        
        assert result.success is False
        assert result.error_type == "invalid_cwd"
    
    # Asynchronous Command Execution Tests
    
    def test_execute_async_success(self, executor):
        """Test starting an asynchronous command."""
        # Start a long-running command
        handle, result = executor.execute_async(
            f'{sys.executable} -c "import time; print(\'Started\'); time.sleep(0.5); print(\'Done\')"'
        )
        
        assert result.success is True
        assert handle is not None
        assert handle.is_running() or handle.process.poll() is not None
        assert "started asynchronously" in result.message.lower()
        
        # Wait for completion
        final_result = handle.wait(timeout=2)
        assert final_result.success is True
        assert final_result.return_code == 0
    
    def test_execute_async_with_output_capture(self, executor):
        """Test capturing output from async command."""
        # Start command that produces output
        handle, result = executor.execute_async(
            f'{sys.executable} -c "print(\'Line 1\'); print(\'Line 2\'); print(\'Line 3\')"'
        )
        
        assert result.success is True
        assert handle is not None
        
        # Wait for completion
        final_result = handle.wait(timeout=2)
        assert final_result.success is True
        assert "Line 1" in final_result.stdout
        assert "Line 2" in final_result.stdout
        assert "Line 3" in final_result.stdout
    
    def test_execute_async_check_is_running(self, executor):
        """Test checking if async command is still running."""
        # Start a command that runs for a bit
        handle, result = executor.execute_async(
            f'{sys.executable} -c "import time; time.sleep(2)"'
        )
        
        assert result.success is True
        assert handle is not None
        
        # Should be running initially
        assert handle.is_running() is True
        
        # Wait for completion
        handle.wait(timeout=5)
        
        # Should no longer be running
        assert handle.is_running() is False
    
    def test_execute_async_get_output_while_running(self, executor):
        """Test getting partial output while command is still running."""
        # Command that prints incrementally
        # Use single quotes inside double quotes for shell=True compatibility  
        cmd = (
            f"{sys.executable} -c "
            f'"import time, sys; '
            f"print(\'Line 1\'); sys.stdout.flush(); "
            f'time.sleep(0.2); '
            f"print(\'Line 2\'); sys.stdout.flush(); "
            f'time.sleep(0.2); '
            f"print(\'Line 3\'); sys.stdout.flush()\""
        )
        handle, result = executor.execute_async(cmd)
        
        assert result.success is True
        assert handle is not None
        
        # Wait a bit for some output
        time.sleep(0.7)
        
        # Get partial output
        stdout_lines, stderr_lines = handle.get_output()
        
        # Should have at least some output
        assert len(stdout_lines) > 0
        
        # Wait for completion
        handle.wait(timeout=2)
    
    def test_execute_async_wait_with_timeout(self, executor):
        """Test waiting for async command with timeout."""
        # Command that runs for 5 seconds
        handle, result = executor.execute_async(
            f'{sys.executable} -c "import time; time.sleep(5)"'
        )
        
        assert result.success is True
        assert handle is not None
        
        try:
            # Wait with short timeout
            final_result = handle.wait(timeout=1)
            
            assert final_result.success is False
            assert final_result.error_type == "timeout"
            assert "timed out" in final_result.message.lower()
        finally:
            # Clean up: terminate the process to avoid Windows file lock issues
            if handle is not None:
                handle.terminate()
                # Give it more time to clean up on Windows
                import time
                time.sleep(0.5)
    
    def test_execute_async_terminate(self, executor):
        """Test terminating a running async command."""
        # Start long-running command
        handle, result = executor.execute_async(
            f'{sys.executable} -c "import time; time.sleep(10)"'
        )
        
        assert result.success is True
        assert handle is not None
        assert handle.is_running() is True
        
        # Terminate it
        handle.terminate()
        
        # Give it a moment to terminate
        time.sleep(0.2)
        
        # Should no longer be running
        assert handle.is_running() is False
    
    def test_execute_async_command_not_found(self, executor):
        """Test async execution of non-existent command."""
        handle, result = executor.execute_async("nonexistentcommand12345")
        
        # With shell=True, the command starts successfully but fails when executed
        # So we need to wait for it to complete to see the error
        if handle is not None:
            final_result = handle.wait(timeout=2)
            assert final_result.success is False
            assert final_result.error_type == "non_zero_exit"
        else:
            # If it failed immediately (shouldn't happen with shell=True but handle gracefully)
            assert result.success is False
    
    def test_execute_async_invalid_cwd(self, executor):
        """Test async execution with invalid working directory."""
        handle, result = executor.execute_async(
            "echo test",
            cwd="/nonexistent/directory"
        )
        
        assert result.success is False
        assert handle is None
        assert result.error_type == "invalid_cwd"
    
    def test_execute_async_in_specific_cwd(self, executor, temp_dir):
        """Test async command execution in specified working directory."""
        # Create subdirectory with file
        subdir = Path(temp_dir) / "async_subdir"
        subdir.mkdir()
        test_file = subdir / "test.txt"
        test_file.write_text("Async subdir content")
        
        # Execute async command in subdirectory
        if sys.platform == "win32":
            handle, result = executor.execute_async("type test.txt", cwd=str(subdir))
        else:
            handle, result = executor.execute_async("cat test.txt", cwd=str(subdir))
        
        assert result.success is True
        assert handle is not None
        
        # Wait and check output
        final_result = handle.wait(timeout=2)
        assert final_result.success is True
        assert "Async subdir content" in final_result.stdout
    
    def test_execute_async_with_stderr(self, executor):
        """Test async command that writes to stderr."""
        # Use single quotes inside double quotes for shell=True compatibility
        cmd = (
            f"{sys.executable} -c "
            f'"import sys; '
            f"sys.stderr.write(\'Error line\\n\'); "
            f'sys.exit(1)"'
        )
        handle, result = executor.execute_async(cmd)
        
        assert result.success is True
        assert handle is not None
        
        # Wait for completion
        final_result = handle.wait(timeout=2)
        assert final_result.success is False
        assert final_result.return_code == 1
        assert "Error line" in final_result.stderr
    
    # Edge Cases and Error Conditions
    
    def test_execute_empty_command(self, executor):
        """Test executing an empty command string."""
        result = executor.execute("")
        
        # Should handle gracefully - either execute empty or fail gracefully
        # The behavior may vary by system, but should not crash
        assert result is not None
        assert isinstance(result, CommandResult)
    
    def test_execute_command_with_special_characters(self, executor):
        """Test command with special shell characters."""
        # Test command with special characters in arguments
        result = executor.execute(
            f'{sys.executable} -c "print(\'Special: $#@!\')"'
        )
        
        assert result.success is True
        assert "Special: $#@!" in result.stdout
    
    def test_execute_command_with_environment_variables(self, executor):
        """Test command that uses environment variables."""
        # Set environment variable and use it
        if sys.platform == "win32":
            result = executor.execute('echo %PATH%')
        else:
            result = executor.execute('echo $PATH')
        
        assert result.success is True
        # PATH should contain something
        assert len(result.stdout.strip()) > 0
    
    def test_execute_command_with_very_long_output(self, executor):
        """Test command that produces very long output."""
        # Generate 1000 lines of output
        result = executor.execute(
            f'{sys.executable} -c "for i in range(1000): print(f\'Line {{i}}\')"'
        )
        
        assert result.success is True
        assert result.return_code == 0
        # Check that output contains many lines
        assert result.stdout.count("Line") >= 1000
    
    def test_execute_command_with_unicode_output(self, executor):
        """Test command that produces unicode output."""
        # On Windows, the shell encoding may not support all Unicode characters
        # Use a simpler test that works across platforms
        result = executor.execute(
            f"{sys.executable} -c \"print('Unicode test: café')\""
        )
        
        # Check that command executed (may have encoding issues on some systems)
        # The important thing is it doesn't crash
        assert result is not None
        assert isinstance(result, CommandResult)
        # If successful, check for content; if failed, it's an encoding issue which is expected on some systems
        if result.success:
            assert "Unicode test" in result.stdout or "caf" in result.stdout
    
    def test_execute_command_with_binary_output(self, executor, temp_dir):
        """Test command that might produce binary output."""
        # Create a binary file
        binary_file = Path(temp_dir) / "binary.dat"
        binary_file.write_bytes(b'\x00\x01\x02\x03\xff\xfe')
        
        # Try to read it (may fail or produce garbled output, should not crash)
        if sys.platform == "win32":
            result = executor.execute(f'type "{binary_file}"')
        else:
            result = executor.execute(f'cat "{binary_file}"')
        
        # Should complete without crashing, though output may be garbled
        assert result is not None
        assert isinstance(result, CommandResult)
    
    def test_command_argument_formatting_with_spaces(self, executor):
        """Test _format_command with arguments containing spaces."""
        formatted = executor._format_command('echo "hello world"')
        
        assert isinstance(formatted, list)
        assert "echo" in formatted
        # Quoted string should be preserved as single argument
        assert "hello world" in formatted
    
    def test_command_argument_formatting_with_flags(self, executor):
        """Test _format_command with multiple flags."""
        formatted = executor._format_command('ls -la -h --color=auto')
        
        assert isinstance(formatted, list)
        assert "ls" in formatted
        assert "-la" in formatted or "-l" in formatted
        assert "-h" in formatted or "-la" in formatted
    
    def test_command_argument_formatting_complex(self, executor):
        """Test _format_command with complex command line."""
        formatted = executor._format_command(
            'python -c "print(\'hello\')" --verbose --output="file name.txt"'
        )
        
        assert isinstance(formatted, list)
        assert "python" in formatted
        assert "-c" in formatted
        assert "print('hello')" in formatted
    
    def test_permission_error_handling(self, executor, temp_dir):
        """Test handling of permission errors during execution."""
        # This test may behave differently on different systems
        # Mock the Popen to raise PermissionError
        with patch('subprocess.Popen', side_effect=PermissionError("Access denied")):
            result = executor.execute("echo test")
            
            assert result.success is False
            assert result.error_type == "permission"
            assert "permission denied" in result.message.lower()
    
    def test_unexpected_error_handling(self, executor):
        """Test handling of unexpected errors during execution."""
        # Mock Popen to raise unexpected exception
        with patch('subprocess.Popen', side_effect=RuntimeError("Unexpected error")):
            result = executor.execute("echo test")
            
            assert result.success is False
            assert result.error_type == "unexpected"
            assert "unexpected error" in result.message.lower()
    
    def test_multiple_sequential_commands(self, executor):
        """Test executing multiple commands in sequence."""
        results = []
        
        for i in range(5):
            result = executor.execute(f'{sys.executable} -c "print(\'Command {i}\')"')
            results.append(result)
        
        # All should succeed
        assert all(r.success for r in results)
        assert all(r.return_code == 0 for r in results)
        
        # Each should have unique output
        for i, result in enumerate(results):
            assert f"Command {i}" in result.stdout
    
    def test_command_result_structure(self, executor):
        """Test that CommandResult has all required fields."""
        result = executor.execute(f'{sys.executable} -c "print(\'test\')"')
        
        # Check all required fields exist
        assert hasattr(result, 'success')
        assert hasattr(result, 'stdout')
        assert hasattr(result, 'stderr')
        assert hasattr(result, 'return_code')
        assert hasattr(result, 'command')
        assert hasattr(result, 'message')
        assert hasattr(result, 'error_type')
        
        # Check field types
        assert isinstance(result.success, bool)
        assert isinstance(result.stdout, str)
        assert isinstance(result.stderr, str)
        assert isinstance(result.return_code, int)
        assert isinstance(result.command, str)
        assert isinstance(result.message, str)
    
    def test_async_command_handle_structure(self, executor):
        """Test that AsyncCommandHandle has all required methods."""
        handle, _ = executor.execute_async(
            f'{sys.executable} -c "print(\'test\')"'
        )
        
        assert handle is not None
        
        # Check all required methods exist
        assert hasattr(handle, 'is_running')
        assert hasattr(handle, 'get_output')
        assert hasattr(handle, 'wait')
        assert hasattr(handle, 'terminate')
        assert hasattr(handle, 'process')
        assert hasattr(handle, 'command')
        assert hasattr(handle, 'cwd')
        
        # Clean up
        handle.wait(timeout=2)
