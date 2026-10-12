/**
 * Accessibility Utilities
 * Provides functions for enhancing accessibility through screen reader
 * announcements, keyboard navigation tracking, and focus management.
 */

const Accessibility = {
    /**
     * Initialize accessibility features
     */
    init() {
        this.setupKeyboardNavigation();
        this.setupFocusManagement();
        this.setupSkipLinks();
        console.log('Accessibility features initialized');
    },

    /**
     * Announce a message to screen readers
     * @param {string} message - The message to announce
     * @param {string} priority - 'polite' or 'assertive'
     */
    announce(message, priority = 'polite') {
        const announcer = document.getElementById('sr-announcements');
        if (!announcer) {
            console.warn('Screen reader announcements element not found');
            return;
        }

        // Clear previous announcement
        announcer.textContent = '';
        
        // Set priority
        announcer.setAttribute('aria-live', priority);
        
        // Small delay to ensure screen readers detect the change
        setTimeout(() => {
            announcer.textContent = message;
        }, 100);

        // Clear after 5 seconds to prevent stale announcements
        setTimeout(() => {
            if (announcer.textContent === message) {
                announcer.textContent = '';
            }
        }, 5000);
    },

    /**
     * Track keyboard vs mouse navigation to show/hide focus indicators
     */
    setupKeyboardNavigation() {
        let isUsingKeyboard = false;

        // Detect keyboard navigation
        document.addEventListener('keydown', (e) => {
            // Tab, arrow keys, Enter, Space indicate keyboard navigation
            if (e.key === 'Tab' || e.key.startsWith('Arrow') || e.key === 'Enter' || e.key === ' ') {
                isUsingKeyboard = true;
                document.body.classList.add('keyboard-nav');
                document.body.classList.remove('using-mouse');
            }
        });

        // Detect mouse navigation
        document.addEventListener('mousedown', () => {
            isUsingKeyboard = false;
            document.body.classList.add('using-mouse');
            document.body.classList.remove('keyboard-nav');
        });

        // Also listen for touch events
        document.addEventListener('touchstart', () => {
            isUsingKeyboard = false;
            document.body.classList.remove('keyboard-nav');
        });
    },

    /**
     * Setup focus management for modals and dialogs
     */
    setupFocusManagement() {
        // Store the last focused element before opening a dialog
        this.lastFocusedElement = null;

        // Monitor for dialog opening
        document.addEventListener('dialog-opened', (e) => {
            this.trapFocus(e.detail.dialog);
        });

        // Monitor for dialog closing
        document.addEventListener('dialog-closed', () => {
            this.restoreFocus();
        });
    },

    /**
     * Trap focus within a dialog/modal
     * @param {HTMLElement} dialog - The dialog element
     */
    trapFocus(dialog) {
        if (!dialog) return;

        // Store currently focused element
        this.lastFocusedElement = document.activeElement;

        // Get all focusable elements within the dialog
        const focusableElements = dialog.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );

        if (focusableElements.length === 0) return;

        const firstFocusable = focusableElements[0];
        const lastFocusable = focusableElements[focusableElements.length - 1];

        // Focus the first element
        setTimeout(() => firstFocusable.focus(), 100);

        // Create focus trap
        const trapFocusHandler = (e) => {
            if (e.key !== 'Tab') return;

            if (e.shiftKey) {
                // Shift + Tab
                if (document.activeElement === firstFocusable) {
                    e.preventDefault();
                    lastFocusable.focus();
                }
            } else {
                // Tab
                if (document.activeElement === lastFocusable) {
                    e.preventDefault();
                    firstFocusable.focus();
                }
            }
        };

        dialog.addEventListener('keydown', trapFocusHandler);
        dialog.dataset.focusTrapActive = 'true';
    },

    /**
     * Restore focus to the element that was focused before a dialog opened
     */
    restoreFocus() {
        if (this.lastFocusedElement && typeof this.lastFocusedElement.focus === 'function') {
            setTimeout(() => {
                this.lastFocusedElement.focus();
                this.lastFocusedElement = null;
            }, 100);
        }
    },

    /**
     * Setup skip links for keyboard navigation
     */
    setupSkipLinks() {
        // Create skip to main content link
        const skipLink = document.createElement('a');
        skipLink.href = '#view-task';
        skipLink.className = 'skip-link';
        skipLink.textContent = 'Skip to main content';
        skipLink.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.getElementById('view-task');
            if (target) {
                target.setAttribute('tabindex', '-1');
                target.focus();
                target.scrollIntoView();
            }
        });

        // Insert at the beginning of body
        document.body.insertBefore(skipLink, document.body.firstChild);
    },

    /**
     * Update ARIA attributes for task status
     * @param {string} status - The status ('idle', 'running', 'success', 'error')
     * @param {string} message - Optional status message
     */
    updateTaskStatus(status, message = '') {
        const statusIndicator = document.getElementById('task-status-indicator');
        if (!statusIndicator) return;

        // Update visual status
        statusIndicator.className = `status-badge status-${status}`;
        
        // Update status text
        const statusTexts = {
            idle: 'Idle',
            running: 'Running...',
            success: 'Completed',
            error: 'Failed'
        };
        statusIndicator.textContent = statusTexts[status] || status;

        // Announce status change to screen readers
        const announcements = {
            idle: 'Task ready',
            running: 'Task is now running',
            success: message || 'Task completed successfully',
            error: message || 'Task failed'
        };

        const priority = status === 'error' ? 'assertive' : 'polite';
        this.announce(announcements[status], priority);

        // Update ARIA labels on buttons
        const runButton = document.getElementById('btn-run');
        const stopButton = document.getElementById('btn-stop');

        if (runButton) {
            runButton.disabled = status === 'running';
            runButton.setAttribute('aria-disabled', status === 'running');
        }

        if (stopButton) {
            stopButton.disabled = status !== 'running';
            stopButton.setAttribute('aria-disabled', status !== 'running');
        }
    },

    /**
     * Update ARIA attributes for progress output
     * @param {string} message - The progress message
     * @param {string} type - Message type ('info', 'warning', 'error', 'success')
     */
    announceProgress(message, type = 'info') {
        // For errors, use assertive to interrupt
        const priority = type === 'error' ? 'assertive' : 'polite';
        
        // Format announcement based on type
        const prefix = {
            info: '',
            warning: 'Warning: ',
            error: 'Error: ',
            success: 'Success: '
        }[type] || '';

        this.announce(prefix + message, priority);
    },

    /**
     * Manage tab navigation between views
     * @param {string} viewId - The ID of the view to activate
     */
    updateViewNavigation(viewId) {
        // Update ARIA attributes on tabs
        const tabs = document.querySelectorAll('[role="tab"]');
        tabs.forEach(tab => {
            const isActive = tab.getAttribute('data-view') === viewId.replace('view-', '');
            tab.setAttribute('aria-selected', isActive);
            tab.classList.toggle('active', isActive);
        });

        // Update tabpanel visibility
        const panels = document.querySelectorAll('[role="tabpanel"]');
        panels.forEach(panel => {
            const isActive = panel.id === viewId;
            panel.hidden = !isActive;
            panel.classList.toggle('active', isActive);
        });

        // Announce view change
        const viewNames = {
            'view-task': 'Task view',
            'view-history': 'History view',
            'view-settings': 'Settings view'
        };
        this.announce(`${viewNames[viewId] || 'View'} activated`);
    },

    /**
     * Add descriptive labels to dynamically created elements
     * @param {HTMLElement} element - The element to label
     * @param {string} label - The accessible label
     */
    addAriaLabel(element, label) {
        if (!element) return;
        element.setAttribute('aria-label', label);
    },

    /**
     * Create a live region for dynamic content
     * @param {HTMLElement} element - The element to make live
     * @param {string} politeness - 'polite' or 'assertive'
     */
    makeLiveRegion(element, politeness = 'polite') {
        if (!element) return;
        element.setAttribute('aria-live', politeness);
        element.setAttribute('aria-atomic', 'false');
    },

    /**
     * Show a confirmation dialog with proper focus management
     * @param {string} message - The confirmation message
     * @param {Function} onConfirm - Callback when confirmed
     * @param {Function} onCancel - Callback when cancelled
     */
    showConfirmDialog(message, onConfirm, onCancel) {
        // Create dialog element
        const dialog = document.createElement('div');
        dialog.setAttribute('role', 'dialog');
        dialog.setAttribute('aria-modal', 'true');
        dialog.setAttribute('aria-labelledby', 'dialog-title');
        dialog.className = 'confirmation-dialog';
        
        dialog.innerHTML = `
            <div class="dialog-content">
                <h2 id="dialog-title" class="dialog-title">Confirm Action</h2>
                <p class="dialog-message">${message}</p>
                <div class="dialog-actions">
                    <button id="dialog-cancel" class="btn btn-secondary">Cancel</button>
                    <button id="dialog-confirm" class="btn btn-primary">Confirm</button>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);
        document.body.classList.add('dialog-open');

        // Trap focus
        this.trapFocus(dialog);

        // Announce to screen reader
        this.announce('Confirmation dialog opened: ' + message, 'assertive');

        // Event handlers
        const confirmBtn = dialog.querySelector('#dialog-confirm');
        const cancelBtn = dialog.querySelector('#dialog-cancel');

        const closeDialog = () => {
            document.body.classList.remove('dialog-open');
            dialog.remove();
            this.restoreFocus();
            this.announce('Dialog closed');
        };

        confirmBtn.addEventListener('click', () => {
            closeDialog();
            if (onConfirm) onConfirm();
        });

        cancelBtn.addEventListener('click', () => {
            closeDialog();
            if (onCancel) onCancel();
        });

        // ESC key to close
        dialog.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeDialog();
                if (onCancel) onCancel();
            }
        });
    },

    /**
     * Validate if element is keyboard accessible
     * @param {HTMLElement} element - The element to check
     * @returns {boolean} True if accessible
     */
    isKeyboardAccessible(element) {
        if (!element) return false;

        // Check if element can receive focus
        const tabindex = element.getAttribute('tabindex');
        const focusableSelectors = 'a[href], button, input, textarea, select, [tabindex]';
        
        return element.matches(focusableSelectors) && tabindex !== '-1';
    },

    /**
     * Ensure all interactive elements have proper ARIA labels
     */
    auditAccessibility() {
        const issues = [];

        // Check buttons without labels
        document.querySelectorAll('button:not([aria-label]):not([aria-labelledby])').forEach(button => {
            if (!button.textContent.trim()) {
                issues.push({
                    element: button,
                    issue: 'Button without accessible label'
                });
            }
        });

        // Check images without alt text
        document.querySelectorAll('img:not([alt])').forEach(img => {
            issues.push({
                element: img,
                issue: 'Image without alt text'
            });
        });

        // Check form inputs without labels
        document.querySelectorAll('input, textarea, select').forEach(input => {
            const id = input.id;
            const hasLabel = id && document.querySelector(`label[for="${id}"]`);
            const hasAriaLabel = input.getAttribute('aria-label') || input.getAttribute('aria-labelledby');
            
            if (!hasLabel && !hasAriaLabel) {
                issues.push({
                    element: input,
                    issue: 'Form input without label'
                });
            }
        });

        if (issues.length > 0) {
            console.warn('Accessibility issues found:', issues);
        } else {
            console.log('No accessibility issues detected');
        }

        return issues;
    }
};

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => Accessibility.init());
} else {
    Accessibility.init();
}

// Export for use in other modules
window.Accessibility = Accessibility;
