/**
 * Accessibility Module
 * 
 * Handles keyboard navigation detection, screen reader announcements,
 * and other accessibility features
 */

const accessibility = {
    isTabbing: false,
    announcer: null
};

/**
 * Initialize accessibility features
 */
function initAccessibility() {
    setupKeyboardDetection();
    setupScreenReaderAnnouncer();
    setupFocusTrap();
    setupAriaLiveRegions();
    console.log('Accessibility features initialized');
}

/**
 * Detect keyboard navigation to show enhanced focus indicators
 */
function setupKeyboardDetection() {
    // Detect Tab key to add visual focus indicators
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            document.body.classList.add('user-is-tabbing');
            accessibility.isTabbing = true;
        }
    });
    
    // Remove visual indicators when using mouse
    document.addEventListener('mousedown', () => {
        document.body.classList.remove('user-is-tabbing');
        accessibility.isTabbing = false;
    });
}

/**
 * Setup screen reader announcer (aria-live region)
 */
function setupScreenReaderAnnouncer() {
    // Create announcer element if it doesn't exist
    let announcer = document.getElementById('screen-reader-announcer');
    
    if (!announcer) {
        announcer = document.createElement('div');
        announcer.id = 'screen-reader-announcer';
        announcer.className = 'sr-only';
        announcer.setAttribute('role', 'status');
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('aria-atomic', 'true');
        document.body.appendChild(announcer);
    }
    
    accessibility.announcer = announcer;
}

/**
 * Announce a message to screen readers
 * @param {string} message - The message to announce
 * @param {string} priority - 'polite' (default) or 'assertive'
 */
function announceToScreenReader(message, priority = 'polite') {
    if (!accessibility.announcer) {
        setupScreenReaderAnnouncer();
    }
    
    // Set priority
    accessibility.announcer.setAttribute('aria-live', priority);
    
    // Clear previous message
    accessibility.announcer.textContent = '';
    
    // Announce new message with slight delay to ensure it's read
    setTimeout(() => {
        accessibility.announcer.textContent = message;
    }, 100);
    
    console.log(`Screen reader announcement (${priority}): ${message}`);
}

/**
 * Setup focus trap for modal dialogs
 */
function setupFocusTrap() {
    // Monitor dialog opening to trap focus
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'hidden') {
                const dialog = mutation.target;
                
                if (dialog.classList.contains('dialog-overlay')) {
                    if (!dialog.hasAttribute('hidden')) {
                        // Dialog opened - trap focus
                        trapFocusInDialog(dialog);
                    } else {
                        // Dialog closed - restore focus
                        restoreFocusAfterDialog();
                    }
                }
            }
        });
    });
    
    // Observe all dialog overlays
    observer.observe(document.body, {
        attributes: true,
        attributeFilter: ['hidden'],
        subtree: true
    });
}

/**
 * Trap focus within a dialog
 * @param {HTMLElement} dialog - The dialog element
 */
function trapFocusInDialog(dialog) {
    const focusableElements = dialog.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];
    
    // Store the element that had focus before dialog opened
    dialog.dataset.previousFocus = document.activeElement?.id || '';
    
    // Focus first element
    if (firstFocusable) {
        firstFocusable.focus();
    }
    
    // Handle Tab key to loop focus within dialog
    const handleTabKey = (e) => {
        if (e.key === 'Tab') {
            if (e.shiftKey) {
                // Shift+Tab: if on first element, go to last
                if (document.activeElement === firstFocusable) {
                    e.preventDefault();
                    lastFocusable.focus();
                }
            } else {
                // Tab: if on last element, go to first
                if (document.activeElement === lastFocusable) {
                    e.preventDefault();
                    firstFocusable.focus();
                }
            }
        }
    };
    
    dialog.addEventListener('keydown', handleTabKey);
    dialog.dataset.focusTrapHandler = 'true';
    
    // Announce dialog opened to screen readers
    const dialogTitle = dialog.querySelector('.dialog-title')?.textContent || 'Dialog opened';
    announceToScreenReader(dialogTitle, 'assertive');
}

/**
 * Restore focus after dialog closes
 */
function restoreFocusAfterDialog() {
    const dialog = document.querySelector('.dialog-overlay[data-previous-focus]');
    
    if (dialog && dialog.dataset.previousFocus) {
        const previousElement = document.getElementById(dialog.dataset.previousFocus);
        
        if (previousElement) {
            previousElement.focus();
        }
        
        delete dialog.dataset.previousFocus;
    }
}

/**
 * Setup ARIA live regions for dynamic content updates
 */
function setupAriaLiveRegions() {
    // Task status updates
    const taskStatus = document.getElementById('task-status');
    if (taskStatus) {
        taskStatus.setAttribute('role', 'status');
        taskStatus.setAttribute('aria-live', 'polite');
        taskStatus.setAttribute('aria-atomic', 'true');
    }
    
    // Progress output
    const progressOutput = document.getElementById('progress-output');
    if (progressOutput) {
        progressOutput.setAttribute('role', 'log');
        progressOutput.setAttribute('aria-live', 'polite');
        progressOutput.setAttribute('aria-atomic', 'false');
    }
}

/**
 * Update button state with proper ARIA attributes
 * @param {HTMLElement} button - The button element
 * @param {boolean} disabled - Whether button should be disabled
 * @param {string} label - Optional updated aria-label
 */
function updateButtonState(button, disabled, label) {
    if (!button) return;
    
    button.disabled = disabled;
    button.setAttribute('aria-disabled', disabled.toString());
    
    if (label) {
        button.setAttribute('aria-label', label);
    }
}

/**
 * Create an accessible tooltip
 * @param {HTMLElement} element - Element to attach tooltip to
 * @param {string} text - Tooltip text
 * @returns {string} Tooltip ID for aria-describedby
 */
function createAccessibleTooltip(element, text) {
    const tooltipId = `tooltip-${Math.random().toString(36).substr(2, 9)}`;
    
    const tooltip = document.createElement('div');
    tooltip.id = tooltipId;
    tooltip.className = 'tooltip';
    tooltip.setAttribute('role', 'tooltip');
    tooltip.textContent = text;
    tooltip.style.display = 'none';
    
    document.body.appendChild(tooltip);
    
    // Show tooltip on focus/hover
    element.addEventListener('mouseenter', () => {
        showTooltip(tooltip, element);
    });
    
    element.addEventListener('focus', () => {
        showTooltip(tooltip, element);
    });
    
    // Hide tooltip on blur/mouseleave
    element.addEventListener('mouseleave', () => {
        hideTooltip(tooltip);
    });
    
    element.addEventListener('blur', () => {
        hideTooltip(tooltip);
    });
    
    // Link tooltip to element
    element.setAttribute('aria-describedby', tooltipId);
    
    return tooltipId;
}

/**
 * Show a tooltip
 * @param {HTMLElement} tooltip - Tooltip element
 * @param {HTMLElement} target - Target element
 */
function showTooltip(tooltip, target) {
    const rect = target.getBoundingClientRect();
    
    tooltip.style.display = 'block';
    tooltip.style.top = `${rect.bottom + 8}px`;
    tooltip.style.left = `${rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2)}px`;
}

/**
 * Hide a tooltip
 * @param {HTMLElement} tooltip - Tooltip element
 */
function hideTooltip(tooltip) {
    tooltip.style.display = 'none';
}

/**
 * Announce task status change
 * @param {string} status - The new status
 */
function announceTaskStatus(status) {
    const messages = {
        'running': 'Task is now running',
        'completed': 'Task completed successfully',
        'failed': 'Task failed with an error',
        'cancelled': 'Task was cancelled'
    };
    
    const message = messages[status] || `Task status: ${status}`;
    announceToScreenReader(message, status === 'failed' ? 'assertive' : 'polite');
}

/**
 * Announce navigation change
 * @param {string} viewName - The new view name
 */
function announceViewChange(viewName) {
    const messages = {
        'task': 'Switched to Task view',
        'history': 'Switched to History view',
        'settings': 'Switched to Settings view'
    };
    
    const message = messages[viewName] || `Switched to ${viewName} view`;
    announceToScreenReader(message);
}

/**
 * Add ARIA labels to dynamically created elements
 * @param {HTMLElement} element - The element to enhance
 * @param {object} attributes - ARIA attributes to add
 */
function enhanceAccessibility(element, attributes) {
    Object.keys(attributes).forEach(key => {
        element.setAttribute(key, attributes[key]);
    });
}

/**
 * Create accessible error message
 * @param {string} fieldId - The field that has an error
 * @param {string} message - Error message
 */
function showAccessibleError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const errorId = `${fieldId}-error`;
    const errorElement = document.getElementById(errorId);
    
    if (field && errorElement) {
        // Update error message
        errorElement.textContent = message;
        errorElement.setAttribute('role', 'alert');
        
        // Link field to error
        field.setAttribute('aria-invalid', 'true');
        field.setAttribute('aria-describedby', errorId);
        
        // Announce error
        announceToScreenReader(`Error: ${message}`, 'assertive');
    }
}

/**
 * Clear accessible error
 * @param {string} fieldId - The field to clear error from
 */
function clearAccessibleError(fieldId) {
    const field = document.getElementById(fieldId);
    const errorId = `${fieldId}-error`;
    const errorElement = document.getElementById(errorId);
    
    if (field && errorElement) {
        // Clear error message
        errorElement.textContent = '';
        errorElement.removeAttribute('role');
        
        // Remove error state from field
        field.setAttribute('aria-invalid', 'false');
        field.removeAttribute('aria-describedby');
    }
}

// Initialize accessibility when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAccessibility);
} else {
    initAccessibility();
}

// Export functions for use in other modules
if (typeof window !== 'undefined') {
    window.accessibility = {
        announceToScreenReader,
        updateButtonState,
        createAccessibleTooltip,
        announceTaskStatus,
        announceViewChange,
        enhanceAccessibility,
        showAccessibleError,
        clearAccessibleError
    };
}
