/**
 * Task Input Panel Component
 * 
 * Handles user input for task descriptions, validation, and execution control.
 * Implements character counting, button state management, and task lifecycle management.
 * 
 * Requirements: 2.1-2.9
 */

class TaskInputPanel {
    constructor() {
        // DOM Elements
        this.taskDescriptionTextarea = null;
        this.charCountSpan = null;
        this.runButton = null;
        this.stopButton = null;
        this.statusDiv = null;
        
        // State
        this.isRunning = false;
        this.currentTaskId = null;
        
        // Constants
        this.MAX_CHARACTERS = 5000;
        
        // Bind methods to maintain context
        this.handleInput = this.handleInput.bind(this);
        this.handleRunClick = this.handleRunClick.bind(this);
        this.handleStopClick = this.handleStopClick.bind(this);
        this.handleTaskCompleted = this.handleTaskCompleted.bind(this);
        this.handleTaskError = this.handleTaskError.bind(this);
        this.handleKeyDown = this.handleKeyDown.bind(this);
    }
    
    /**
     * Initialize the component
     */
    init() {
        // Get DOM elements
        this.taskDescriptionTextarea = document.getElementById('task-description');
        this.charCountSpan = document.getElementById('char-count');
        this.runButton = document.getElementById('run-task-btn');
        this.stopButton = document.getElementById('stop-task-btn');
        this.statusDiv = document.getElementById('task-status');
        
        if (!this.taskDescriptionTextarea || !this.charCountSpan || !this.runButton || !this.stopButton || !this.statusDiv) {
            console.error('Task Input Panel: Required DOM elements not found');
            return;
        }
        
        // Attach event listeners
        this.taskDescriptionTextarea.addEventListener('input', this.handleInput);
        this.taskDescriptionTextarea.addEventListener('keydown', this.handleKeyDown);
        this.runButton.addEventListener('click', this.handleRunClick);
        this.stopButton.addEventListener('click', this.handleStopClick);
        
        // Subscribe to state changes
        if (typeof stateManager !== 'undefined') {
            stateManager.subscribe('isTaskRunning', (isRunning) => {
                this.isRunning = isRunning;
                this.updateButtonStates();
            });
        }
        
        // Register callbacks for Python events
        if (typeof eel !== 'undefined') {
            // Expose functions that Python can call
            window.eel_task_completed = this.handleTaskCompleted;
            window.eel_task_error = this.handleTaskError;
        }
        
        // Initialize character count
        this.updateCharacterCount();
        
        console.log('Task Input Panel initialized');
    }
    
    /**
     * Handle input event on textarea
     * Updates character count and validates input
     */
    handleInput() {
        this.updateCharacterCount();
        this.validateInput();
    }
    
    /**
     * Handle keyboard shortcuts
     * @param {KeyboardEvent} event - The keyboard event
     */
    handleKeyDown(event) {
        // Ctrl+Enter or Cmd+Enter to run task
        if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
            event.preventDefault();
            if (!this.isRunning && this.isInputValid()) {
                this.handleRunClick();
            }
        }
    }
    
    /**
     * Update character count display
     */
    updateCharacterCount() {
        const currentLength = this.taskDescriptionTextarea.value.length;
        this.charCountSpan.textContent = currentLength;
        
        // Add warning class if approaching limit
        if (currentLength >= this.MAX_CHARACTERS * 0.9) {
            this.charCountSpan.classList.add('warning');
        } else {
            this.charCountSpan.classList.remove('warning');
        }
    }
    
    /**
     * Validate input and update run button state
     */
    validateInput() {
        const isValid = this.isInputValid();
        this.runButton.disabled = !isValid || this.isRunning;
    }
    
    /**
     * Check if input is valid
     * @returns {boolean} True if input is valid
     */
    isInputValid() {
        const value = this.taskDescriptionTextarea.value.trim();
        return value.length > 0 && value.length <= this.MAX_CHARACTERS;
    }
    
    /**
     * Handle run button click
     * Starts task execution
     */
    async handleRunClick() {
        if (!this.isInputValid() || this.isRunning) {
            return;
        }
        
        const taskDescription = this.taskDescriptionTextarea.value.trim();
        
        try {
            // Update UI to running state
            this.setRunningState(true);
            this.setStatus('running', 'Running...');
            
            // Call Python backend via Eel
            if (typeof eel !== 'undefined' && eel.run_task) {
                const response = await eel.run_task(taskDescription)();
                
                if (response && response.success) {
                    this.currentTaskId = response.task_id || null;
                    console.log('Task started successfully:', this.currentTaskId);
                    
                    // Update state manager
                    if (typeof stateManager !== 'undefined') {
                        stateManager.set('isTaskRunning', true);
                        stateManager.set('currentTaskId', this.currentTaskId);
                    }
                } else {
                    // Handle error from Python
                    const errorMessage = response?.error || 'Failed to start task';
                    this.setStatus('error', errorMessage);
                    this.setRunningState(false);
                    this.showError(errorMessage);
                }
            } else {
                console.error('Eel is not available or run_task is not exposed');
                this.setStatus('error', 'Cannot connect to backend');
                this.setRunningState(false);
            }
        } catch (error) {
            console.error('Error starting task:', error);
            this.setStatus('error', 'Failed to start task');
            this.setRunningState(false);
            this.showError('An unexpected error occurred while starting the task');
        }
    }
    
    /**
     * Handle stop button click
     * Cancels task execution
     */
    async handleStopClick() {
        if (!this.isRunning) {
            return;
        }
        
        try {
            this.setStatus('cancelling', 'Stopping task...');
            
            // Call Python backend via Eel
            if (typeof eel !== 'undefined' && eel.stop_task) {
                const response = await eel.stop_task()();
                
                if (response && response.success) {
                    console.log('Task stopped successfully');
                    this.setStatus('cancelled', 'Task cancelled');
                    this.setRunningState(false);
                    
                    // Update state manager
                    if (typeof stateManager !== 'undefined') {
                        stateManager.set('isTaskRunning', false);
                        stateManager.set('currentTaskId', null);
                    }
                } else {
                    const errorMessage = response?.error || 'Failed to stop task';
                    this.setStatus('error', errorMessage);
                    this.showError(errorMessage);
                }
            } else {
                console.error('Eel is not available or stop_task is not exposed');
                this.setStatus('error', 'Cannot connect to backend');
            }
        } catch (error) {
            console.error('Error stopping task:', error);
            this.setStatus('error', 'Failed to stop task');
            this.showError('An unexpected error occurred while stopping the task');
        }
    }
    
    /**
     * Handle task completion callback from Python
     * @param {Object} result - Result object from Python
     */
    handleTaskCompleted(result) {
        console.log('Task completed:', result);
        
        const success = result?.success !== false;
        const message = result?.message || (success ? 'Task completed successfully' : 'Task completed with errors');
        
        this.setStatus(success ? 'success' : 'error', message);
        this.setRunningState(false);
        
        // Update state manager
        if (typeof stateManager !== 'undefined') {
            stateManager.set('isTaskRunning', false);
            stateManager.set('currentTaskId', null);
        }
        
        // Clear status after a delay
        setTimeout(() => {
            this.clearStatus();
        }, 5000);
    }
    
    /**
     * Handle task error callback from Python
     * @param {Object} error - Error object from Python
     */
    handleTaskError(error) {
        console.error('Task error:', error);
        
        const errorMessage = error?.message || error?.error || 'An error occurred during task execution';
        
        this.setStatus('error', errorMessage);
        this.setRunningState(false);
        this.showError(errorMessage);
        
        // Update state manager
        if (typeof stateManager !== 'undefined') {
            stateManager.set('isTaskRunning', false);
            stateManager.set('currentTaskId', null);
        }
    }
    
    /**
     * Set running state and update UI
     * @param {boolean} isRunning - Whether a task is running
     */
    setRunningState(isRunning) {
        this.isRunning = isRunning;
        this.updateButtonStates();
    }
    
    /**
     * Update button states based on running state
     */
    updateButtonStates() {
        // Run button: enabled when not running and input is valid
        const runDisabled = this.isRunning || !this.isInputValid();
        this.runButton.disabled = runDisabled;
        this.runButton.setAttribute('aria-disabled', runDisabled.toString());
        
        // Stop button: visible and enabled only when running
        if (this.isRunning) {
            this.stopButton.style.display = 'inline-flex';
            this.stopButton.setAttribute('aria-hidden', 'false');
            this.runButton.style.display = 'none';
            this.runButton.setAttribute('aria-hidden', 'true');
        } else {
            this.stopButton.style.display = 'none';
            this.stopButton.setAttribute('aria-hidden', 'true');
            this.runButton.style.display = 'inline-flex';
            this.runButton.setAttribute('aria-hidden', 'false');
        }
        
        // Disable textarea while running (optional, for clarity)
        this.taskDescriptionTextarea.disabled = this.isRunning;
        this.taskDescriptionTextarea.setAttribute('aria-disabled', this.isRunning.toString());
    }
    
    /**
     * Set status indicator
     * @param {string} type - Status type (idle, running, success, error, cancelled, cancelling)
     * @param {string} message - Status message
     */
    setStatus(type, message) {
        this.statusDiv.textContent = message;
        this.statusDiv.className = `task-status status-${type}`;
        this.statusDiv.style.display = 'block';
        
        // Update ARIA live region for screen readers
        this.statusDiv.setAttribute('aria-live', type === 'error' ? 'assertive' : 'polite');
        
        // Announce status change to screen readers
        if (typeof window.accessibility !== 'undefined' && window.accessibility.announceToScreenReader) {
            const priority = type === 'error' || type === 'failed' ? 'assertive' : 'polite';
            window.accessibility.announceToScreenReader(message, priority);
        }
        
        // Also use the announceTaskStatus helper if available
        if (typeof window.accessibility !== 'undefined' && window.accessibility.announceTaskStatus) {
            window.accessibility.announceTaskStatus(type);
        }
    }
    
    /**
     * Clear status indicator
     */
    clearStatus() {
        this.statusDiv.textContent = '';
        this.statusDiv.className = 'task-status';
        this.statusDiv.style.display = 'none';
    }
    
    /**
     * Show error dialog or notification
     * @param {string} message - Error message
     */
    showError(message) {
        // Use error handler if available
        if (typeof window.errorHandler !== 'undefined') {
            window.errorHandler.handleError(
                { message },
                window.errorHandler.ErrorCategory.SYSTEM,
                window.errorHandler.ErrorSeverity.ERROR
            );
        } else {
            // Fallback to console logging
            console.error('Task error:', message);
        }
        
        // Emit event for other components
        if (typeof window.dispatchEvent === 'function') {
            window.dispatchEvent(new CustomEvent('task-error', {
                detail: { message }
            }));
        }
    }
    
    /**
     * Get current task description
     * @returns {string} The task description
     */
    getTaskDescription() {
        return this.taskDescriptionTextarea.value;
    }
    
    /**
     * Set task description
     * @param {string} description - The task description to set
     */
    setTaskDescription(description) {
        this.taskDescriptionTextarea.value = description;
        this.updateCharacterCount();
        this.validateInput();
    }
    
    /**
     * Clear task description
     */
    clearTaskDescription() {
        this.setTaskDescription('');
    }
    
    /**
     * Focus on task input
     */
    focus() {
        this.taskDescriptionTextarea.focus();
    }
    
    /**
     * Destroy the component and clean up
     */
    destroy() {
        // Remove event listeners
        if (this.taskDescriptionTextarea) {
            this.taskDescriptionTextarea.removeEventListener('input', this.handleInput);
            this.taskDescriptionTextarea.removeEventListener('keydown', this.handleKeyDown);
        }
        if (this.runButton) {
            this.runButton.removeEventListener('click', this.handleRunClick);
        }
        if (this.stopButton) {
            this.stopButton.removeEventListener('click', this.handleStopClick);
        }
        
        // Clear references
        this.taskDescriptionTextarea = null;
        this.charCountSpan = null;
        this.runButton = null;
        this.stopButton = null;
        this.statusDiv = null;
        
        console.log('Task Input Panel destroyed');
    }
}

// Create singleton instance
const taskInputPanel = new TaskInputPanel();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = taskInputPanel;
}
