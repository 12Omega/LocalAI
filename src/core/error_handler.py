"""Error handling utilities for Local AI Development Environment.

This module provides centralized error handling utilities including:
- Retry logic with exponential backoff for transient failures
- Error categorization and descriptive messaging
- Automatic recovery mechanisms
- Error context tracking for debugging

Requirements implemented:
- 14.1: Provide descriptive error messages
- 14.2: Attempt recovery strategies for common failure scenarios
- 14.3: Report specific permission issues
- 14.4: Detect and report timeouts
- 14.5: Explain why tasks cannot be completed and suggest next steps
"""

import time
import logging
from typing import Optional, Callable, TypeVar, Any, Dict, List
from dataclasses import dataclass
from enum import Enum
import functools


# Type variable for generic function return types
T = TypeVar('T')


class ErrorCategory(Enum):
    """Categories of errors for appropriate handling."""
    LLM_ERROR = "llm_error"
    FILE_SYSTEM_ERROR = "file_system_error"
    COMMAND_ERROR = "command_error"
    NETWORK_ERROR = "network_error"
    PARSE_ERROR = "parse_error"
    TASK_ERROR = "task_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """Context information for an error."""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    error_type: Optional[str] = None
    original_exception: Optional[Exception] = None
    recovery_suggestion: Optional[str] = None
    additional_context: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error context to dictionary for logging."""
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "error_type": self.error_type,
            "original_exception": str(self.original_exception) if self.original_exception else None,
            "recovery_suggestion": self.recovery_suggestion,
            "additional_context": self.additional_context,
            "retry_count": self.retry_count
        }


class RetryStrategy:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        """Initialize retry strategy.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds before first retry
            max_delay: Maximum delay in seconds between retries
            exponential_base: Base for exponential backoff calculation
            jitter: Whether to add random jitter to delay
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def get_delay(self, retry_attempt: int) -> float:
        """Calculate delay before next retry attempt.
        
        Uses exponential backoff: delay = base_delay * (exponential_base ^ retry_attempt)
        
        Args:
            retry_attempt: Current retry attempt number (0-indexed)
            
        Returns:
            Delay in seconds before next retry
        """
        import random
        
        # Calculate exponential backoff
        delay = min(
            self.base_delay * (self.exponential_base ** retry_attempt),
            self.max_delay
        )
        
        # Add jitter if enabled (randomize between 0.5 and 1.5 times the delay)
        if self.jitter:
            delay = delay * (0.5 + random.random())
        
        return delay


class ErrorHandler:
    """Centralized error handling with retry logic and recovery mechanisms."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize error handler.
        
        Args:
            logger: Logger instance for error logging. If None, creates default logger.
        """
        self.logger = logger or logging.getLogger(__name__)
        self._error_history: List[ErrorContext] = []
    
    def categorize_error(self, exception: Exception) -> ErrorCategory:
        """Categorize an exception into an error category.
        
        Args:
            exception: Exception to categorize
            
        Returns:
            ErrorCategory enum value
        """
        exception_name = type(exception).__name__
        exception_str = str(exception).lower()
        
        # LLM errors
        if "llm" in exception_name.lower() or "model" in exception_name.lower():
            return ErrorCategory.LLM_ERROR
        
        # File system errors
        if any(name in exception_name for name in ["FileNotFoundError", "PermissionError", "OSError", "IOError"]):
            return ErrorCategory.FILE_SYSTEM_ERROR
        
        # Network errors
        if any(name in exception_name for name in ["ConnectionError", "Timeout", "RequestException", "HTTPError"]):
            return ErrorCategory.NETWORK_ERROR
        
        # Parse errors
        if "parse" in exception_name.lower() or "decode" in exception_name.lower():
            return ErrorCategory.PARSE_ERROR
        
        # Command errors
        if "subprocess" in exception_str or "command" in exception_str:
            return ErrorCategory.COMMAND_ERROR
        
        return ErrorCategory.UNKNOWN_ERROR
    
    def create_error_context(
        self,
        exception: Exception,
        operation: str,
        category: Optional[ErrorCategory] = None,
        recovery_suggestion: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> ErrorContext:
        """Create comprehensive error context from an exception.
        
        Args:
            exception: The exception that occurred
            operation: Description of the operation that failed
            category: Error category (auto-detected if None)
            recovery_suggestion: Suggested recovery action
            additional_context: Additional context information
            
        Returns:
            ErrorContext object with full error information
        """
        if category is None:
            category = self.categorize_error(exception)
        
        # Determine severity based on exception type
        severity = ErrorSeverity.ERROR
        if isinstance(exception, (ConnectionError, TimeoutError)):
            severity = ErrorSeverity.WARNING  # These are often transient
        elif severity == ErrorSeverity.CRITICAL:
            severity = ErrorSeverity.CRITICAL
        
        # Build descriptive error message
        message = f"{operation} failed: {str(exception)}"
        
        # Add recovery suggestion if not provided
        if recovery_suggestion is None:
            recovery_suggestion = self._get_default_recovery_suggestion(exception, category)
        
        # Determine error type
        error_type = type(exception).__name__
        
        return ErrorContext(
            category=category,
            severity=severity,
            message=message,
            error_type=error_type,
            original_exception=exception,
            recovery_suggestion=recovery_suggestion,
            additional_context=additional_context or {}
        )
    
    def _get_default_recovery_suggestion(
        self,
        exception: Exception,
        category: ErrorCategory
    ) -> str:
        """Get default recovery suggestion based on error type.
        
        Args:
            exception: The exception that occurred
            category: Error category
            
        Returns:
            Recovery suggestion string
        """
        exception_name = type(exception).__name__
        exception_str = str(exception).lower()
        
        # File system error suggestions
        if category == ErrorCategory.FILE_SYSTEM_ERROR:
            if "permission" in exception_name.lower():
                return "Check file permissions or run with elevated privileges"
            elif "not found" in exception_str:
                return "Verify the file path exists and is accessible"
            elif "disk full" in exception_str or "no space" in exception_str:
                return "Free up disk space and try again"
            return "Check file system access and permissions"
        
        # Network error suggestions
        if category == ErrorCategory.NETWORK_ERROR:
            if "timeout" in exception_str:
                return "Check network connectivity and try again with a longer timeout"
            elif "connection" in exception_str:
                return "Verify the service is running and accessible"
            return "Check network connectivity and service availability"
        
        # LLM error suggestions
        if category == ErrorCategory.LLM_ERROR:
            if "unavailable" in exception_str or "connection" in exception_str:
                return "Ensure the LLM server is running and the endpoint is correct"
            elif "timeout" in exception_str:
                return "The prompt may be too complex. Try simplifying or increase timeout"
            return "Check LLM configuration and service status"
        
        # Command error suggestions
        if category == ErrorCategory.COMMAND_ERROR:
            if "not found" in exception_str:
                return "Verify the command exists and is in PATH"
            elif "permission" in exception_str:
                return "Check command execution permissions"
            return "Verify command syntax and availability"
        
        # Parse error suggestions
        if category == ErrorCategory.PARSE_ERROR:
            return "Check input format and syntax"
        
        return "Review the error details and try again"
    
    def is_transient_error(self, exception: Exception) -> bool:
        """Determine if an error is transient and worth retrying.
        
        Args:
            exception: Exception to check
            
        Returns:
            True if error is likely transient, False otherwise
        """
        exception_name = type(exception).__name__
        exception_str = str(exception).lower()
        
        # Network timeouts are transient
        if "timeout" in exception_name.lower() or "timeout" in exception_str:
            return True
        
        # Connection errors are often transient
        if "connection" in exception_name.lower() or "connection" in exception_str:
            return True
        
        # Temporary network issues
        if any(phrase in exception_str for phrase in ["temporary failure", "try again", "service unavailable"]):
            return True
        
        # Rate limiting
        if "rate limit" in exception_str or "too many requests" in exception_str:
            return True
        
        return False
    
    def retry_with_backoff(
        self,
        func: Callable[..., T],
        *args,
        strategy: Optional[RetryStrategy] = None,
        operation_name: Optional[str] = None,
        **kwargs
    ) -> T:
        """Execute function with retry logic and exponential backoff.
        
        Automatically retries the function if it raises a transient error,
        using exponential backoff between attempts.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            strategy: Retry strategy configuration (uses default if None)
            operation_name: Name of operation for logging
            **kwargs: Keyword arguments for the function
            
        Returns:
            Return value from successful function execution
            
        Raises:
            The last exception if all retries are exhausted
        """
        if strategy is None:
            strategy = RetryStrategy()
        
        operation_name = operation_name or getattr(func, '__name__', 'unknown_operation')
        last_exception = None
        
        for attempt in range(strategy.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                
                # Log success if this was a retry
                if attempt > 0:
                    self.logger.info(
                        f"Operation '{operation_name}' succeeded after {attempt} retries"
                    )
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if this is the last attempt
                if attempt >= strategy.max_retries:
                    self.logger.error(
                        f"Operation '{operation_name}' failed after {attempt + 1} attempts: {str(e)}"
                    )
                    break
                
                # Check if error is transient
                if not self.is_transient_error(e):
                    self.logger.warning(
                        f"Operation '{operation_name}' failed with non-transient error: {str(e)}"
                    )
                    raise
                
                # Calculate delay and wait
                delay = strategy.get_delay(attempt)
                self.logger.info(
                    f"Operation '{operation_name}' failed (attempt {attempt + 1}/{strategy.max_retries + 1}), "
                    f"retrying in {delay:.2f} seconds: {str(e)}"
                )
                time.sleep(delay)
        
        # All retries exhausted
        error_context = self.create_error_context(
            last_exception,
            f"Operation '{operation_name}' after {strategy.max_retries + 1} attempts",
            additional_context={"retry_count": strategy.max_retries}
        )
        self._error_history.append(error_context)
        self.logger.error("Error context: %s", error_context.to_dict())
        
        raise last_exception
    
    def log_error_with_context(self, error_context: ErrorContext) -> None:
        """Log an error with full context information.
        
        Args:
            error_context: Error context to log
        """
        self._error_history.append(error_context)
        
        # Build log message
        log_message = (
            f"[{error_context.category.value}] {error_context.message}"
        )
        
        if error_context.recovery_suggestion:
            log_message += f"\n  Recovery suggestion: {error_context.recovery_suggestion}"
        
        if error_context.additional_context:
            log_message += f"\n  Additional context: {error_context.additional_context}"
        
        # Log at appropriate level
        if error_context.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error_context.severity == ErrorSeverity.ERROR:
            self.logger.error(log_message)
        elif error_context.severity == ErrorSeverity.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def get_error_history(self) -> List[ErrorContext]:
        """Get history of errors that have occurred.
        
        Returns:
            List of ErrorContext objects
        """
        return self._error_history.copy()
    
    def clear_error_history(self) -> None:
        """Clear the error history."""
        self._error_history.clear()


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    logger: Optional[logging.Logger] = None
):
    """Decorator to add retry logic with exponential backoff to a function.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay in seconds between retries
        logger: Logger instance for logging
        
    Returns:
        Decorator function
        
    Example:
        @with_retry(max_retries=3, base_delay=2.0)
        def fetch_data():
            # Function that might fail transiently
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            strategy = RetryStrategy(
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay
            )
            error_handler = ErrorHandler(logger=logger)
            return error_handler.retry_with_backoff(
                func,
                *args,
                strategy=strategy,
                operation_name=func.__name__,
                **kwargs
            )
        return wrapper
    return decorator
