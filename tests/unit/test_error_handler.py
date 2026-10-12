"""Unit tests for error handler.

Tests error handling, retry logic, and recovery mechanisms.

Task: 17.2 - Write unit tests for error handling
Requirements: 14.1, 14.2, 14.3, 14.4, 14.5
"""

import pytest
import time
import logging
from unittest.mock import Mock, patch

from src.core.error_handler import (
    ErrorHandler,
    ErrorCategory,
    ErrorSeverity,
    ErrorContext,
    RetryStrategy,
    with_retry
)


class TestErrorCategorization:
    """Test error categorization logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ErrorHandler()
    
    def test_categorize_file_system_error(self):
        """Test categorization of file system errors."""
        errors = [
            FileNotFoundError("File not found"),
            PermissionError("Permission denied"),
            OSError("OS error"),
            IOError("I/O error")
        ]
        
        for error in errors:
            category = self.handler.categorize_error(error)
            assert category == ErrorCategory.FILE_SYSTEM_ERROR
    
    def test_categorize_network_error(self):
        """Test categorization of network errors."""
        errors = [
            ConnectionError("Connection failed"),
            TimeoutError("Request timed out")
        ]
        
        for error in errors:
            category = self.handler.categorize_error(error)
            assert category == ErrorCategory.NETWORK_ERROR
    
    def test_categorize_parse_error(self):
        """Test categorization of parse errors."""
        error = ValueError("Failed to parse JSON")
        # Create a mock with lowercase 'parse' in name
        parse_error = type('ParseError', (Exception,), {})('Parse failed')
        category = self.handler.categorize_error(parse_error)
        assert category == ErrorCategory.PARSE_ERROR
    
    def test_categorize_unknown_error(self):
        """Test categorization of unknown errors."""
        error = RuntimeError("Some runtime error")
        category = self.handler.categorize_error(error)
        assert category == ErrorCategory.UNKNOWN_ERROR


class TestErrorContext:
    """Test error context creation and management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ErrorHandler()
    
    def test_create_error_context_with_exception(self):
        """Test creating error context from exception."""
        exception = FileNotFoundError("test.txt not found")
        context = self.handler.create_error_context(
            exception,
            operation="Reading file"
        )
        
        assert context.category == ErrorCategory.FILE_SYSTEM_ERROR
        assert "Reading file failed" in context.message
        assert context.error_type == "FileNotFoundError"
        assert context.original_exception is exception
        assert context.recovery_suggestion is not None
    
    def test_create_error_context_with_custom_category(self):
        """Test creating error context with custom category."""
        exception = ValueError("Invalid input")
        context = self.handler.create_error_context(
            exception,
            operation="Validating input",
            category=ErrorCategory.PARSE_ERROR
        )
        
        assert context.category == ErrorCategory.PARSE_ERROR
    
    def test_create_error_context_with_additional_context(self):
        """Test creating error context with additional information."""
        exception = TimeoutError("Connection timeout")
        additional = {"url": "http://example.com", "timeout": 30}
        context = self.handler.create_error_context(
            exception,
            operation="Fetching data",
            additional_context=additional
        )
        
        assert context.additional_context == additional
    
    def test_error_context_to_dict(self):
        """Test converting error context to dictionary."""
        context = ErrorContext(
            category=ErrorCategory.LLM_ERROR,
            severity=ErrorSeverity.ERROR,
            message="LLM request failed",
            error_type="LLMError",
            recovery_suggestion="Check LLM configuration"
        )
        
        context_dict = context.to_dict()
        
        assert context_dict["category"] == "llm_error"
        assert context_dict["severity"] == "error"
        assert context_dict["message"] == "LLM request failed"
        assert context_dict["error_type"] == "LLMError"
        assert context_dict["recovery_suggestion"] == "Check LLM configuration"


class TestRecoverySuggestions:
    """Test automatic recovery suggestion generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ErrorHandler()
    
    def test_recovery_suggestion_for_permission_error(self):
        """Test recovery suggestion for permission errors."""
        exception = PermissionError("Permission denied")
        suggestion = self.handler._get_default_recovery_suggestion(
            exception,
            ErrorCategory.FILE_SYSTEM_ERROR
        )
        
        assert "permission" in suggestion.lower()
    
    def test_recovery_suggestion_for_network_timeout(self):
        """Test recovery suggestion for network timeouts."""
        exception = TimeoutError("Connection timeout")
        suggestion = self.handler._get_default_recovery_suggestion(
            exception,
            ErrorCategory.NETWORK_ERROR
        )
        
        assert "timeout" in suggestion.lower() or "network" in suggestion.lower()
    
    def test_recovery_suggestion_for_llm_error(self):
        """Test recovery suggestion for LLM errors."""
        exception = Exception("LLM service unavailable")
        suggestion = self.handler._get_default_recovery_suggestion(
            exception,
            ErrorCategory.LLM_ERROR
        )
        
        assert "llm" in suggestion.lower() or "configuration" in suggestion.lower()
    
    def test_recovery_suggestion_for_command_not_found(self):
        """Test recovery suggestion for command not found errors."""
        exception = Exception("command not found")
        suggestion = self.handler._get_default_recovery_suggestion(
            exception,
            ErrorCategory.COMMAND_ERROR
        )
        
        assert "command" in suggestion.lower() and "path" in suggestion.lower()


class TestTransientErrorDetection:
    """Test transient error detection logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ErrorHandler()
    
    def test_timeout_is_transient(self):
        """Test that timeout errors are considered transient."""
        errors = [
            TimeoutError("Request timed out"),
            Exception("Operation timeout")
        ]
        
        for error in errors:
            assert self.handler.is_transient_error(error) is True
    
    def test_connection_error_is_transient(self):
        """Test that connection errors are considered transient."""
        errors = [
            ConnectionError("Connection refused"),
            Exception("Connection failed")
        ]
        
        for error in errors:
            assert self.handler.is_transient_error(error) is True
    
    def test_rate_limit_is_transient(self):
        """Test that rate limit errors are considered transient."""
        error = Exception("Rate limit exceeded")
        assert self.handler.is_transient_error(error) is True
    
    def test_permission_error_is_not_transient(self):
        """Test that permission errors are not considered transient."""
        error = PermissionError("Permission denied")
        assert self.handler.is_transient_error(error) is False
    
    def test_file_not_found_is_not_transient(self):
        """Test that file not found errors are not considered transient."""
        error = FileNotFoundError("File not found")
        assert self.handler.is_transient_error(error) is False


class TestRetryStrategy:
    """Test retry strategy and exponential backoff."""
    
    def test_default_retry_strategy(self):
        """Test default retry strategy parameters."""
        strategy = RetryStrategy()
        
        assert strategy.max_retries == 3
        assert strategy.base_delay == 1.0
        assert strategy.max_delay == 60.0
        assert strategy.exponential_base == 2.0
        assert strategy.jitter is True
    
    def test_custom_retry_strategy(self):
        """Test custom retry strategy parameters."""
        strategy = RetryStrategy(
            max_retries=5,
            base_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
            jitter=False
        )
        
        assert strategy.max_retries == 5
        assert strategy.base_delay == 2.0
        assert strategy.max_delay == 120.0
        assert strategy.exponential_base == 3.0
        assert strategy.jitter is False
    
    def test_exponential_backoff_calculation(self):
        """Test exponential backoff delay calculation."""
        strategy = RetryStrategy(base_delay=1.0, exponential_base=2.0, jitter=False)
        
        # Test delays increase exponentially
        delay_0 = strategy.get_delay(0)
        delay_1 = strategy.get_delay(1)
        delay_2 = strategy.get_delay(2)
        
        assert delay_0 == 1.0  # 1.0 * 2^0
        assert delay_1 == 2.0  # 1.0 * 2^1
        assert delay_2 == 4.0  # 1.0 * 2^2
    
    def test_max_delay_cap(self):
        """Test that delays are capped at max_delay."""
        strategy = RetryStrategy(
            base_delay=1.0,
            max_delay=5.0,
            exponential_base=2.0,
            jitter=False
        )
        
        # After enough retries, delay should cap at max_delay
        delay = strategy.get_delay(10)  # Would be 1024 without cap
        assert delay == 5.0
    
    def test_jitter_adds_randomness(self):
        """Test that jitter adds randomness to delays."""
        strategy = RetryStrategy(base_delay=10.0, exponential_base=2.0, jitter=True)
        
        # Get multiple delays for the same retry attempt
        delays = [strategy.get_delay(0) for _ in range(10)]
        
        # With jitter, delays should vary
        assert len(set(delays)) > 1
        
        # All delays should be within reasonable range (5.0 to 15.0)
        for delay in delays:
            assert 5.0 <= delay <= 15.0


class TestRetryWithBackoff:
    """Test retry logic with exponential backoff."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ErrorHandler()
    
    def test_successful_first_attempt(self):
        """Test that successful functions don't retry."""
        mock_func = Mock(return_value="success")
        
        result = self.handler.retry_with_backoff(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_on_transient_error(self):
        """Test that transient errors trigger retries."""
        mock_func = Mock(side_effect=[
            TimeoutError("Timeout"),
            TimeoutError("Timeout"),
            "success"
        ])
        
        result = self.handler.retry_with_backoff(
            mock_func,
            strategy=RetryStrategy(max_retries=3, base_delay=0.01)
        )
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_no_retry_on_non_transient_error(self):
        """Test that non-transient errors don't retry."""
        mock_func = Mock(side_effect=PermissionError("Permission denied"))
        
        with pytest.raises(PermissionError):
            self.handler.retry_with_backoff(
                mock_func,
                strategy=RetryStrategy(max_retries=3)
            )
        
        assert mock_func.call_count == 1
    
    def test_exhausted_retries_raises_exception(self):
        """Test that exhausted retries raise the last exception."""
        mock_func = Mock(side_effect=TimeoutError("Timeout"))
        
        with pytest.raises(TimeoutError):
            self.handler.retry_with_backoff(
                mock_func,
                strategy=RetryStrategy(max_retries=2, base_delay=0.01)
            )
        
        # Should try initial + 2 retries = 3 times
        assert mock_func.call_count == 3
    
    def test_retry_with_function_arguments(self):
        """Test retry with function arguments."""
        mock_func = Mock(side_effect=[
            TimeoutError("Timeout"),
            "success"
        ])
        
        result = self.handler.retry_with_backoff(
            mock_func,
            "arg1",
            "arg2",
            kwarg1="value1",
            strategy=RetryStrategy(max_retries=2, base_delay=0.01)
        )
        
        assert result == "success"
        mock_func.assert_called_with("arg1", "arg2", kwarg1="value1")
    
    def test_retry_logs_attempts(self):
        """Test that retry attempts are logged."""
        mock_logger = Mock()
        handler = ErrorHandler(logger=mock_logger)
        
        mock_func = Mock(side_effect=[
            TimeoutError("Timeout"),
            "success"
        ])
        
        handler.retry_with_backoff(
            mock_func,
            strategy=RetryStrategy(max_retries=2, base_delay=0.01)
        )
        
        # Should log the retry and success
        assert mock_logger.info.call_count >= 1


class TestRetryDecorator:
    """Test the @with_retry decorator."""
    
    def test_decorator_adds_retry_logic(self):
        """Test that decorator adds retry logic to function."""
        call_count = 0
        
        @with_retry(max_retries=2, base_delay=0.01)
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("Timeout")
            return "success"
        
        result = failing_func()
        
        assert result == "success"
        assert call_count == 3
    
    def test_decorator_preserves_function_name(self):
        """Test that decorator preserves function metadata."""
        @with_retry(max_retries=2)
        def my_function():
            """My function docstring."""
            return "result"
        
        assert my_function.__name__ == "my_function"
        assert "My function docstring" in my_function.__doc__


class TestErrorHistory:
    """Test error history tracking."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ErrorHandler()
    
    def test_error_history_initially_empty(self):
        """Test that error history is initially empty."""
        history = self.handler.get_error_history()
        assert len(history) == 0
    
    def test_error_history_tracks_errors(self):
        """Test that error history tracks errors."""
        context = ErrorContext(
            category=ErrorCategory.FILE_SYSTEM_ERROR,
            severity=ErrorSeverity.ERROR,
            message="Test error"
        )
        
        self.handler.log_error_with_context(context)
        
        history = self.handler.get_error_history()
        assert len(history) == 1
        assert history[0].message == "Test error"
    
    def test_clear_error_history(self):
        """Test clearing error history."""
        context = ErrorContext(
            category=ErrorCategory.FILE_SYSTEM_ERROR,
            severity=ErrorSeverity.ERROR,
            message="Test error"
        )
        
        self.handler.log_error_with_context(context)
        self.handler.clear_error_history()
        
        history = self.handler.get_error_history()
        assert len(history) == 0
    
    def test_get_error_history_returns_copy(self):
        """Test that get_error_history returns a copy."""
        context = ErrorContext(
            category=ErrorCategory.FILE_SYSTEM_ERROR,
            severity=ErrorSeverity.ERROR,
            message="Test error"
        )
        
        self.handler.log_error_with_context(context)
        history = self.handler.get_error_history()
        
        # Modify the returned list
        history.clear()
        
        # Original history should be unchanged
        assert len(self.handler.get_error_history()) == 1


class TestErrorLogging:
    """Test error logging with context."""
    
    def test_log_error_at_appropriate_level(self):
        """Test that errors are logged at appropriate levels."""
        mock_logger = Mock()
        handler = ErrorHandler(logger=mock_logger)
        
        # Test critical
        context_critical = ErrorContext(
            category=ErrorCategory.FILE_SYSTEM_ERROR,
            severity=ErrorSeverity.CRITICAL,
            message="Critical error"
        )
        handler.log_error_with_context(context_critical)
        assert mock_logger.critical.called
        
        # Test error
        context_error = ErrorContext(
            category=ErrorCategory.FILE_SYSTEM_ERROR,
            severity=ErrorSeverity.ERROR,
            message="Error"
        )
        handler.log_error_with_context(context_error)
        assert mock_logger.error.called
        
        # Test warning
        context_warning = ErrorContext(
            category=ErrorCategory.FILE_SYSTEM_ERROR,
            severity=ErrorSeverity.WARNING,
            message="Warning"
        )
        handler.log_error_with_context(context_warning)
        assert mock_logger.warning.called
    
    def test_log_includes_recovery_suggestion(self):
        """Test that log messages include recovery suggestions."""
        mock_logger = Mock()
        handler = ErrorHandler(logger=mock_logger)
        
        context = ErrorContext(
            category=ErrorCategory.FILE_SYSTEM_ERROR,
            severity=ErrorSeverity.ERROR,
            message="File operation failed",
            recovery_suggestion="Check file permissions"
        )
        
        handler.log_error_with_context(context)
        
        # Check that logger was called with message containing recovery suggestion
        call_args = str(mock_logger.error.call_args)
        assert "Check file permissions" in call_args
