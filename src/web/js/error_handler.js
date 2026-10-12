/**
 * Error Handler Module
 * 
 * Comprehensive error handling with categorization, logging, and user-friendly dialogs
 */

const errorHandler = {
    errorLog: [],
    maxLogSize: 100,
    listeners: []
};

/**
 * Error categories for different types of errors
 */
const ErrorCategory = {
    NETWORK: 'network',
    LLM_API: 'llm_api',
    FILE_OPERATION: 'file_operation',
    VALIDATION: 'validation',
    SYSTEM: 'system',
    UNKNOWN: 'unknown'
};

/**
 * Error severity levels
 */
const ErrorSeverity = {
    INFO: 'info',
    WARNING: 'warning',
    ERROR: 'error',
    CRITICAL: 'critical'
};

/**
 * Initialize error handler
 */
function initErrorHandler() {
    // Catch unhandled errors
    window.addEventListener('error', (event) => {
        handleUnhandledError({
            message: event.message,
            source: event.filename,
            lineno: event.lineno,
            colno: event.colno,
            error: event.error
        });
    });
    
    // Catch unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
        handleUnhandledPromiseRejection({
            reason: event.reason,
            promise: event.promise
        });
    });
    
    console.log('Error handler initialized');
}

/**
 * Handle an error with categorization and appropriate response
 * @param {Error|Object} error - The error object
 * @param {string} category - Error category
 * @param {string} severity - Error severity
 * @param {Object} context - Additional context information
 */
function handleError(error, category = ErrorCategory.UNKNOWN, severity = ErrorSeverity.ERROR, context = {}) {
    const errorEntry = {
        timestamp: new Date().toISOString(),
        message: error.message || error.toString(),
        category,
        severity,
        context,
        stack: error.stack || null,
        userAgent: navigator.userAgent
    };
    
    // Log error
    logError(errorEntry);
    
    // Determine how to present the error to the user
    if (severity === ErrorSeverity.CRITICAL) {
        showCriticalErrorDialog(errorEntry);
    } else if (severity === ErrorSeverity.ERROR) {
        showErrorDialog(errorEntry);
    } else if (severity === ErrorSeverity.WARNING) {
        showWarningNotification(errorEntry);
    }
    
    // Notify listeners
    notifyErrorListeners(errorEntry);
    
    return errorEntry;
}

/**
 * Handle network errors (connection issues, timeouts)
 * @param {Error} error - The network error
 * @param {Object} context - Request context
 */
function handleNetworkError(error, context = {}) {
    const message = getUserFriendlyNetworkMessage(error);
    
    return handleError(
        { message, originalError: error },
        ErrorCategory.NETWORK,
        ErrorSeverity.ERROR,
        context
    );
}

/**
 * Handle LLM API errors (rate limits, invalid keys, model errors)
 * @param {Error} error - The API error
 * @param {Object} context - API call context
 */
function handleLLMApiError(error, context = {}) {
    const message = getUserFriendlyLLMMessage(error, context);
    
    return handleError(
        { message, originalError: error },
        ErrorCategory.LLM_API,
        ErrorSeverity.ERROR,
        context
    );
}

/**
 * Handle file operation errors
 * @param {Error} error - The file error
 * @param {Object} context - File operation context
 */
function handleFileOperationError(error, context = {}) {
    const message = getUserFriendlyFileMessage(error, context);
    
    return handleError(
        { message, originalError: error },
        ErrorCategory.FILE_OPERATION,
        ErrorSeverity.ERROR,
        context
    );
}

/**
 * Handle validation errors
 * @param {string} field - Field that failed validation
 * @param {string} message - Validation message
 */
function handleValidationError(field, message) {
    return handleError(
        { message: `${field}: ${message}` },
        ErrorCategory.VALIDATION,
        ErrorSeverity.WARNING,
        { field }
    );
}

/**
 * Handle unhandled JavaScript errors
 * @param {Object} errorInfo - Error information
 */
function handleUnhandledError(errorInfo) {
    const error = {
        message: `Unhandled Error: ${errorInfo.message}`,
        stack: errorInfo.error?.stack,
        source: errorInfo.source,
        line: errorInfo.lineno,
        column: errorInfo.colno
    };
    
    return handleError(
        error,
        ErrorCategory.SYSTEM,
        ErrorSeverity.CRITICAL,
        { type: 'unhandled_error' }
    );
}

/**
 * Handle unhandled promise rejections
 * @param {Object} rejectionInfo - Rejection information
 */
function handleUnhandledPromiseRejection(rejectionInfo) {
    const error = {
        message: `Unhandled Promise Rejection: ${rejectionInfo.reason}`,
        stack: rejectionInfo.reason?.stack
    };
    
    return handleError(
        error,
        ErrorCategory.SYSTEM,
        ErrorSeverity.CRITICAL,
        { type: 'unhandled_rejection' }
    );
}

/**
 * Get user-friendly network error message
 * @param {Error} error - The network error
 * @returns {string} User-friendly message
 */
function getUserFriendlyNetworkMessage(error) {
    const message = error.message?.toLowerCase() || '';
    
    if (message.includes('network') || message.includes('fetch')) {
        return 'Unable to connect to the backend service. Please check if the application is running.';
    }
    
    if (message.includes('timeout')) {
        return 'The request timed out. Please try again.';
    }
    
    if (message.includes('cors')) {
        return 'Cross-origin request blocked. This is a configuration issue.';
    }
    
    return 'A network error occurred. Please check your connection and try again.';
}

/**
 * Get user-friendly LLM API error message
 * @param {Error} error - The API error
 * @param {Object} context - API context
 * @returns {string} User-friendly message
 */
function getUserFriendlyLLMMessage(error, context) {
    const message = error.message?.toLowerCase() || '';
    const statusCode = context.statusCode || error.statusCode;
    
    if (statusCode === 401 || message.includes('unauthorized') || message.includes('api key')) {
        return 'Invalid API key or authentication failed. Please check your LLM settings.';
    }
    
    if (statusCode === 429 || message.includes('rate limit')) {
        return 'Rate limit exceeded. Please wait a moment and try again.';
    }
    
    if (statusCode === 404 || message.includes('not found')) {
        return 'LLM model not found. Please check your model name in settings.';
    }
    
    if (statusCode === 503 || message.includes('unavailable')) {
        return 'LLM service is temporarily unavailable. Please try again later.';
    }
    
    if (message.includes('context length') || message.includes('token limit')) {
        return 'The task description is too long. Please reduce the size and try again.';
    }
    
    return 'An error occurred while communicating with the LLM. Please check your settings.';
}

/**
 * Get user-friendly file operation error message
 * @param {Error} error - The file error
 * @param {Object} context - File context
 * @returns {string} User-friendly message
 */
function getUserFriendlyFileMessage(error, context) {
    const message = error.message?.toLowerCase() || '';
    
    if (message.includes('permission') || message.includes('access denied')) {
        return `Permission denied: Cannot access ${context.path || 'file'}. Check file permissions.`;
    }
    
    if (message.includes('not found') || message.includes('enoent')) {
        return `File not found: ${context.path || 'The requested file does not exist'}.`;
    }
    
    if (message.includes('already exists')) {
        return `File already exists: ${context.path || 'A file with this name already exists'}.`;
    }
    
    if (message.includes('disk') || message.includes('space')) {
        return 'Insufficient disk space. Please free up space and try again.';
    }
    
    return `File operation failed: ${context.operation || 'Unknown operation'}. Please try again.`;
}

/**
 * Log error to internal log
 * @param {Object} errorEntry - Error entry to log
 */
function logError(errorEntry) {
    // Add to internal log
    errorHandler.errorLog.push(errorEntry);
    
    // Limit log size
    if (errorHandler.errorLog.length > errorHandler.maxLogSize) {
        errorHandler.errorLog.shift();
    }
    
    // Log to console
    console.error('[Error Handler]', errorEntry);
    
    // Persist critical errors to localStorage
    if (errorEntry.severity === ErrorSeverity.CRITICAL) {
        saveCriticalErrorToStorage(errorEntry);
    }
}

/**
 * Save critical error to localStorage for crash reporting
 * @param {Object} errorEntry - Error entry
 */
function saveCriticalErrorToStorage(errorEntry) {
    try {
        const crashLog = JSON.parse(localStorage.getItem('crashLog') || '[]');
        crashLog.push(errorEntry);
        
        // Keep only last 10 crashes
        if (crashLog.length > 10) {
            crashLog.shift();
        }
        
        localStorage.setItem('crashLog', JSON.stringify(crashLog));
    } catch (e) {
        console.error('Failed to save crash log:', e);
    }
}

/**
 * Get crash log from localStorage
 * @returns {Array} Crash log entries
 */
function getCrashLog() {
    try {
        return JSON.parse(localStorage.getItem('crashLog') || '[]');
    } catch (e) {
        console.error('Failed to retrieve crash log:', e);
        return [];
    }
}

/**
 * Clear crash log
 */
function clearCrashLog() {
    try {
        localStorage.removeItem('crashLog');
    } catch (e) {
        console.error('Failed to clear crash log:', e);
    }
}

/**
 * Show critical error dialog
 * @param {Object} errorEntry - Error entry
 */
function showCriticalErrorDialog(errorEntry) {
    const content = `
        <div class="error-content">
            <p class="error-main-message">${escapeHtml(errorEntry.message)}</p>
            <details class="error-details">
                <summary>Technical Details</summary>
                <pre class="error-stack">${escapeHtml(errorEntry.stack || 'No stack trace available')}</pre>
            </details>
            <p class="error-help">
                This is a critical error. The application may not function correctly. 
                Please restart the application.
            </p>
        </div>
    `;
    
    if (typeof showDialog !== 'undefined') {
        showDialog('Critical Error', content, 'error');
    } else {
        alert(`Critical Error\n\n${errorEntry.message}`);
    }
}

/**
 * Show error dialog
 * @param {Object} errorEntry - Error entry
 */
function showErrorDialog(errorEntry) {
    const content = `
        <div class="error-content">
            <p class="error-main-message">${escapeHtml(errorEntry.message)}</p>
            ${errorEntry.stack ? `
                <details class="error-details">
                    <summary>Technical Details</summary>
                    <pre class="error-stack">${escapeHtml(errorEntry.stack)}</pre>
                </details>
            ` : ''}
            ${getSuggestedActions(errorEntry)}
        </div>
    `;
    
    if (typeof showDialog !== 'undefined') {
        showDialog('Error', content, 'error');
    } else {
        alert(`Error\n\n${errorEntry.message}`);
    }
}

/**
 * Show warning notification
 * @param {Object} errorEntry - Error entry
 */
function showWarningNotification(errorEntry) {
    // Create toast notification for warnings
    const toast = document.createElement('div');
    toast.className = 'toast-notification toast-warning';
    toast.innerHTML = `
        <div class="toast-content">
            <strong>Warning:</strong> ${escapeHtml(errorEntry.message)}
        </div>
        <button class="toast-close" aria-label="Close">&times;</button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        toast.classList.add('toast-fade-out');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
    
    // Manual close
    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.classList.add('toast-fade-out');
        setTimeout(() => toast.remove(), 300);
    });
}

/**
 * Get suggested actions based on error category
 * @param {Object} errorEntry - Error entry
 * @returns {string} HTML for suggested actions
 */
function getSuggestedActions(errorEntry) {
    const actions = [];
    
    switch (errorEntry.category) {
        case ErrorCategory.NETWORK:
            actions.push('Check if the backend service is running');
            actions.push('Verify your network connection');
            break;
        case ErrorCategory.LLM_API:
            actions.push('Check your LLM settings in the Settings tab');
            actions.push('Verify your API key is valid');
            actions.push('Check if the LLM service is accessible');
            break;
        case ErrorCategory.FILE_OPERATION:
            actions.push('Check file permissions');
            actions.push('Verify the file path is correct');
            actions.push('Ensure sufficient disk space');
            break;
        case ErrorCategory.VALIDATION:
            actions.push('Review the input and correct any errors');
            break;
    }
    
    if (actions.length === 0) {
        return '';
    }
    
    return `
        <div class="error-suggestions">
            <strong>Suggested actions:</strong>
            <ul>
                ${actions.map(action => `<li>${escapeHtml(action)}</li>`).join('')}
            </ul>
        </div>
    `;
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped HTML
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Add error listener
 * @param {Function} listener - Listener function
 */
function addErrorListener(listener) {
    errorHandler.listeners.push(listener);
}

/**
 * Notify all error listeners
 * @param {Object} errorEntry - Error entry
 */
function notifyErrorListeners(errorEntry) {
    errorHandler.listeners.forEach(listener => {
        try {
            listener(errorEntry);
        } catch (e) {
            console.error('Error in error listener:', e);
        }
    });
}

/**
 * Get error statistics
 * @returns {Object} Error statistics
 */
function getErrorStatistics() {
    const stats = {
        total: errorHandler.errorLog.length,
        byCategory: {},
        bySeverity: {},
        recent: errorHandler.errorLog.slice(-10)
    };
    
    errorHandler.errorLog.forEach(entry => {
        stats.byCategory[entry.category] = (stats.byCategory[entry.category] || 0) + 1;
        stats.bySeverity[entry.severity] = (stats.bySeverity[entry.severity] || 0) + 1;
    });
    
    return stats;
}

/**
 * Export error log for bug reporting
 * @returns {string} JSON string of error log
 */
function exportErrorLog() {
    return JSON.stringify({
        errors: errorHandler.errorLog,
        crashLog: getCrashLog(),
        statistics: getErrorStatistics(),
        exportDate: new Date().toISOString(),
        userAgent: navigator.userAgent,
        appVersion: window.app?.version || 'unknown'
    }, null, 2);
}

// Initialize error handler when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initErrorHandler);
} else {
    initErrorHandler();
}

// Export functions
if (typeof window !== 'undefined') {
    window.errorHandler = {
        handleError,
        handleNetworkError,
        handleLLMApiError,
        handleFileOperationError,
        handleValidationError,
        addErrorListener,
        getErrorStatistics,
        exportErrorLog,
        getCrashLog,
        clearCrashLog,
        ErrorCategory,
        ErrorSeverity
    };
}
