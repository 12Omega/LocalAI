/**
 * Loading Indicator Utilities
 * Manages loading overlays and spinners for async operations
 */

/**
 * Show the loading overlay
 * @param {string} message - Optional message to display (default: empty)
 */
function showLoading(message = '') {
    const overlay = document.getElementById('loading-overlay');
    const textElement = overlay?.querySelector('.loading-text');
    
    if (overlay) {
        if (textElement) {
            textElement.textContent = message;
        }
        overlay.classList.remove('hidden');
    }
}

/**
 * Hide the loading overlay
 */
function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.add('hidden');
        // Clear the text after fade out completes
        setTimeout(() => {
            const textElement = overlay.querySelector('.loading-text');
            if (textElement) {
                textElement.textContent = '';
            }
        }, 200); // Match transition duration
    }
}

/**
 * Wrap an async function with automatic loading indicator
 * Shows loading spinner if operation takes longer than 1 second
 * @param {Function} asyncFn - The async function to wrap
 * @param {string} message - Loading message to display
 * @returns {Promise} - Result of the async function
 */
async function withLoading(asyncFn, message = 'Loading...') {
    let showSpinner = false;
    let timerHandle = null;
    
    // Start a timer to show spinner after 1 second
    timerHandle = setTimeout(() => {
        showSpinner = true;
        showLoading(message);
    }, 1000);
    
    try {
        const result = await asyncFn();
        return result;
    } finally {
        // Clear timer if operation completed before 1 second
        clearTimeout(timerHandle);
        
        // Hide spinner if it was shown
        if (showSpinner) {
            hideLoading();
        }
    }
}

/**
 * Show a loading spinner on a specific button
 * @param {HTMLButtonElement} button - The button element
 */
function showButtonLoading(button) {
    if (button) {
        button.classList.add('loading');
        button.disabled = true;
    }
}

/**
 * Hide the loading spinner on a specific button
 * @param {HTMLButtonElement} button - The button element
 */
function hideButtonLoading(button) {
    if (button) {
        button.classList.remove('loading');
        button.disabled = false;
    }
}

/**
 * Create an inline spinner element
 * @param {string} size - Size of spinner ('small' or 'default')
 * @returns {HTMLElement} - Spinner element
 */
function createSpinner(size = 'default') {
    const spinner = document.createElement('div');
    spinner.className = size === 'small' ? 'spinner-small' : 'spinner';
    spinner.setAttribute('role', 'status');
    spinner.setAttribute('aria-label', 'Loading');
    return spinner;
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.Loading = {
        show: showLoading,
        hide: hideLoading,
        withLoading: withLoading,
        showButton: showButtonLoading,
        hideButton: hideButtonLoading,
        createSpinner: createSpinner
    };
}
