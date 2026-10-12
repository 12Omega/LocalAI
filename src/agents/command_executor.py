"""Command execution module for Local AI Development Environment.

This module provides the CommandExecutor class that handles shell command
execution with output capture, timeout handling, and proper argument formatting
for both synchronous and asynchronous operations.

Requirements implemented:
- 10.1: Execute shell commands on the local machine
- 10.2: Capture command output and return codes
- 10.3: Capture error messages when commands fail
- 10.4: Execute commands in specified working directories
- 10.5: Handle commands with multiple arguments and flags
- 10.6: Provide progress updates for long-running commands
- 14.1: Provide descriptive error messages
"""

import subprocess
import shlex
import threading
import queue
import os
from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class CommandResult:
    """Result of a command execution."""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    command: str
    message: str
    error_type: Optional[str] = None  # timeout, not_found, permission, etc.


@dataclass
class AsyncCommandHandle:
    """Handle for an asynchronously executing command."""
    process: subprocess.Popen
    command: str
    cwd: Optional[str]
    stdout_queue: queue.Queue
    stderr_queue: queue.Queue
    
    def is_running(self) -> bool:
        """Check if the command is still running."""
        return self.process.poll() is None
    
    def get_output(self) -> Tuple[List[str], List[str]]:
        """Get accumulated output from the command.
        
        Returns:
            Tuple of (stdout_lines, stderr_lines)
        """
        stdout_lines = []
        stderr_lines = []
        
        # Get all available stdout
        while not self.stdout_queue.empty():
            try:
                stdout_lines.append(self.stdout_queue.get_nowait())
            except queue.Empty:
                break
        
        # Get all available stderr
        while not self.stderr_queue.empty():
            try:
                stderr_lines.append(self.stderr_queue.get_nowait())
            except queue.Empty:
                break
        
        return stdout_lines, stderr_lines
    
    def wait(self, timeout: Optional[int] = None) -> CommandResult:
        """Wait for the command to complete.
        
        Args:
            timeout: Maximum time to wait in seconds. None means wait indefinitely.
            
        Returns:
            CommandResult with the command execution results
        """
        try:
            self.process.wait(timeout=timeout)
            
            # Collect all remaining output
            stdout_lines, stderr_lines = self.get_output()
            
            stdout = '\n'.join(stdout_lines)
            stderr = '\n'.join(stderr_lines)
            return_code = self.process.returncode
            
            success = return_code == 0
            message = f"Command completed with return code {return_code}"
            
            return CommandResult(
                success=success,
                stdout=stdout,
                stderr=stderr,
                return_code=return_code,
                command=self.command,
                message=message,
                error_type=None if success else "non_zero_exit"
            )
            
        except subprocess.TimeoutExpired:
            # Kill the process
            self.process.kill()
            stdout_lines, stderr_lines = self.get_output()
            
            return CommandResult(
                success=False,
                stdout='\n'.join(stdout_lines),
                stderr='\n'.join(stderr_lines),
                return_code=-1,
                command=self.command,
                message=f"Command timed out after {timeout} seconds",
                error_type="timeout"
            )
    
    def terminate(self) -> None:
        """Terminate the running command."""
        if self.is_running():
            self.process.terminate()


class CommandExecutor:
    """Handles shell command execution with output capture and error handling.
    
    This class provides methods for executing commands both synchronously
    (with timeout) and asynchronously (for long-running commands) with
    comprehensive output capture and error handling.
    """
    
    def __init__(self, default_cwd: Optional[str] = None):
        """Initialize CommandExecutor.
        
        Args:
            default_cwd: Default working directory for commands. If None, uses current directory.
        """
        self.default_cwd = default_cwd or os.getcwd()
    
    def execute(self, command: str, cwd: Optional[str] = None, timeout: int = 60) -> CommandResult:
        """Execute a shell command and capture output.
        
        This method executes a command synchronously, waiting for it to complete
        or timeout. Use this for commands expected to complete quickly.
        
        Args:
            command: Command string to execute (will be properly parsed)
            cwd: Working directory for the command. If None, uses default_cwd
            timeout: Maximum time to wait in seconds (default: 60)
            
        Returns:
            CommandResult with success status, output, and return code
            
        Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5
        """
        # Resolve working directory
        working_dir = self._resolve_cwd(cwd)
        
        # Validate working directory
        if not os.path.isdir(working_dir):
            return CommandResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                command=command,
                message=f"Working directory does not exist: {working_dir}",
                error_type="invalid_cwd"
            )
        
        try:
            # Execute the command
            # Use shell=True to support built-in commands (dir, type, echo on Windows)
            # and to properly handle PATH lookup for executables
            process = subprocess.Popen(
                command,
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return_code = process.returncode
                
                success = return_code == 0
                message = f"Command executed successfully" if success else f"Command failed with return code {return_code}"
                
                return CommandResult(
                    success=success,
                    stdout=stdout,
                    stderr=stderr,
                    return_code=return_code,
                    command=command,
                    message=message,
                    error_type=None if success else "non_zero_exit"
                )
                
            except subprocess.TimeoutExpired:
                # Kill the process
                process.kill()
                stdout, stderr = process.communicate()
                
                return CommandResult(
                    success=False,
                    stdout=stdout,
                    stderr=stderr,
                    return_code=-1,
                    command=command,
                    message=f"Command timed out after {timeout} seconds",
                    error_type="timeout"
                )
        
        except FileNotFoundError as e:
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                command=command,
                message=f"Command not found: {command.split()[0] if command else 'unknown'}",
                error_type="not_found"
            )
        
        except PermissionError as e:
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                command=command,
                message=f"Permission denied when executing command: {str(e)}",
                error_type="permission"
            )
        
        except Exception as e:
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                command=command,
                message=f"Unexpected error when executing command: {str(e)}",
                error_type="unexpected"
            )
    
    def execute_async(self, command: str, cwd: Optional[str] = None) -> Tuple[Optional[AsyncCommandHandle], CommandResult]:
        """Execute a long-running command asynchronously.
        
        This method starts a command in the background and returns immediately
        with a handle that can be used to monitor progress and retrieve output.
        Use this for commands like development servers, build watchers, etc.
        
        Args:
            command: Command string to execute (will be properly parsed)
            cwd: Working directory for the command. If None, uses default_cwd
            
        Returns:
            Tuple of (AsyncCommandHandle or None, CommandResult)
            If successful, handle contains the running process
            If failed, handle is None and result contains error information
            
        Validates: Requirements 10.1, 10.4, 10.5, 10.6
        """
        # Resolve working directory
        working_dir = self._resolve_cwd(cwd)
        
        # Validate working directory
        if not os.path.isdir(working_dir):
            return None, CommandResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                command=command,
                message=f"Working directory does not exist: {working_dir}",
                error_type="invalid_cwd"
            )
        
        try:
            # Execute the command
            # Use shell=True to support built-in commands (dir, type, echo on Windows)
            # and to properly handle PATH lookup for executables
            process = subprocess.Popen(
                command,
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True
            )
            
            # Create queues for output
            stdout_queue = queue.Queue()
            stderr_queue = queue.Queue()
            
            # Start threads to read output
            def read_output(pipe, output_queue):
                """Read output from pipe and put into queue."""
                try:
                    for line in iter(pipe.readline, ''):
                        if line:
                            output_queue.put(line.rstrip('\n'))
                    pipe.close()
                except Exception:
                    pass
            
            stdout_thread = threading.Thread(
                target=read_output,
                args=(process.stdout, stdout_queue),
                daemon=True
            )
            stderr_thread = threading.Thread(
                target=read_output,
                args=(process.stderr, stderr_queue),
                daemon=True
            )
            
            stdout_thread.start()
            stderr_thread.start()
            
            # Create handle
            handle = AsyncCommandHandle(
                process=process,
                command=command,
                cwd=working_dir,
                stdout_queue=stdout_queue,
                stderr_queue=stderr_queue
            )
            
            return handle, CommandResult(
                success=True,
                stdout="",
                stderr="",
                return_code=0,
                command=command,
                message=f"Command started asynchronously (PID: {process.pid})"
            )
        
        except FileNotFoundError as e:
            return None, CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                command=command,
                message=f"Command not found: {command.split()[0] if command else 'unknown'}",
                error_type="not_found"
            )
        
        except PermissionError as e:
            return None, CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                command=command,
                message=f"Permission denied when executing command: {str(e)}",
                error_type="permission"
            )
        
        except Exception as e:
            return None, CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                command=command,
                message=f"Unexpected error when executing command: {str(e)}",
                error_type="unexpected"
            )
    
    def _resolve_cwd(self, cwd: Optional[str]) -> str:
        """Resolve working directory to absolute path.
        
        Args:
            cwd: Working directory path or None
            
        Returns:
            Absolute path to working directory
        """
        if cwd is None:
            return self.default_cwd
        
        cwd_path = Path(cwd)
        if cwd_path.is_absolute():
            return str(cwd_path)
        
        return str(Path(self.default_cwd) / cwd_path)
    
    def _format_command(self, command: str) -> List[str]:
        """Format command string into properly escaped argument list.
        
        Handles commands with multiple arguments and flags, properly escaping
        special characters and preserving quoted strings.
        
        Args:
            command: Command string to format
            
        Returns:
            List of command arguments with proper escaping
            
        Validates: Requirement 10.5
        """
        # Use shlex to properly parse the command string
        # This handles:
        # - Multiple arguments and flags
        # - Quoted strings with spaces
        # - Escaped special characters
        try:
            return shlex.split(command)
        except ValueError:
            # If parsing fails (unclosed quote, etc.), fall back to simple split
            return command.split()
