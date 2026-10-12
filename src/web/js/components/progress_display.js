/**
 * Progress Display Component
 * 
 * Manages the real-time display of task execution progress and output.
 * Handles progress messages from backend, auto-scrolling, output management,
 * and clipboard operations.
 * 
 * Requirements implemented:
 * - 3.1: Show current operation being performed when task starts
 * - 3.2: Update with new output within 500ms of receiving it
 * - 3.3: Display colored/formatted text for different message types
 * - 3.4: Automatically scroll to show most recent output
 * - 3.5: Allow users to scroll up to review previous output
 * - 3.6: Show success indicator with completion timestamp
 * - 3.7: Show error indicator with error details
 * - 3.8: Provide clear button to remove current output
 * - 3.9: Provide copy button to copy output to clipboard
 * - 13.7: Batch updates to maintain 30fps minimum
 */

class ProgressDisplay {
    constructor() {
        this.messages = [];
        this.autoScroll = true;
        this.taskStatus = 'idle'; // 'idle', 'running', 'completed', 'failed', 'cancelled'
        this.isUpdating = false;
        this.pendingUpdates = [];
        this.updateBatchTimeout = null;
        
        // DOM elements
        this.outputContainer = document.getElementById('progress-output');
        this.autoScrollToggle = document.getElementById('auto-scroll-toggle');
        this.copyButton = document.getElementById('copy-output-btn');
        this.clearButton = document.getElementById('clear-output-btn');
        
        // Initialize component
        this.init();
    }
    
    /**
     * Initialize component: set up event listeners and register callbacks
     */
    init() {
        console.log('Initializing Progress Display component...');
        
        // Set up button event listeners
        if (this.autoScrollToggle) {
            this.autoScrollToggle.addEventListener('click', () => {
                this.toggleAutoScroll();
            });
            this.updateAutoScrollButton();
        }
        
        if (this.copyButton) {
            this.copyButton.addEventListener('click', () => {
                this.copyToClipboard();
            });
        }
        
        if (this.clearButton) {
            this.clearButton.addEventListener('click', () => {
                this.clearMessages();
            });
        }
        
        // Monitor user scrolling to detect manual scroll
        if (this.outputContainer) {
            this.outputContainer.addEventListener('scroll', () => {
                this.handleScroll();
            });
        }
        
        // Register Eel callbacks for backend updates
        this.registerEelCallbacks();
        
        console.log('Progress Display component initialized');
    }
    
    /**
     * Register Eel callbacks to receive progress updates from Python backend
     * 
     * Requirements: 3.1, 3.2, 3.6, 3.7, 11.4
     */
    registerEelCallbacks() {
        // Check if eel is available
        if (typeof eel === 'undefined') {
            console.warn('Eel not available, running in development mode');
            return;
        }
        
        // Expose functions for Python to call
        if (typeof eel.expose !== 'undefined') {
            eel.expose(this.handleProgressUpdate.bind(this), 'update_progress');
            eel.expose(this.handleTaskCompleted.bind(this), 'task_completed');
            eel.expose(this.handleTaskError.bind(this), 'task_error');
        }
        
        console.log('Eel callbacks registered');
    }
    
    /**
     * Handle progress update from backend
     * 
     * @param {Object} data - Progress data from backend
     *   - type: 'info' | 'warning' | 'error' | 'success'
     *   - message: Progress message text
     *   - timestamp: ISO timestamp
     * 
     * Requirements: 3.1, 3.2, 3.3, 13.7, 18.1
     */
    handleProgressUpdate(data) {
        try {
            // Queue update for batching (Req 13.7, 18.1)
            this.pendingUpdates.push({
                type: data.type || 'info',
                content: data.message,
                timestamp: data.timestamp ? new Date(data.timestamp) : new Date()
            });
            
            // Schedule batch update if not already scheduled
            // Use requestAnimationFrame for optimal 60fps batching (Req 18.1)
            if (!this.updateBatchTimeout) {
                this.updateBatchTimeout = true; // Flag to prevent duplicate scheduling
                this.processPendingUpdates();
            }
            
        } catch (error) {
            console.error('Error handling progress update:', error);
        }
    }
    
    /**
     * Process pending updates in batch for performance
     * Uses requestAnimationFrame for optimal DOM batching (60fps)
     * 
     * Requirements: 13.7, 18.1
     */
    processPendingUpdates() {
        if (this.pendingUpdates.length === 0) {
            this.updateBatchTimeout = null;
            return;
        }
        
        // Use requestAnimationFrame for smooth batched updates
        requestAnimationFrame(() => {
            // Batch DOM updates in a single frame
            const fragment = document.createDocumentFragment();
            
            // Create all message elements in memory
            this.pendingUpdates.forEach(message => {
                const messageElement = this.createMessageElement(message);
                fragment.appendChild(messageElement);
                
                // Add to messages array
                this.messages.push(message);
            });
            
            // Single DOM append for all messages (batched)
            if (this.outputContainer) {
                this.outputContainer.appendChild(fragment);
                
                // Auto-scroll if enabled
                if (this.autoScroll) {
                    this.scrollToBottom();
                }
            }
            
            // Clear pending updates
            this.pendingUpdates = [];
            this.updateBatchTimeout = null;
        });
    }
    
    /**
     * Handle task completion notification
     * 
     * @param {Object} data - Completion data
     *   - task_id: Task identifier
     *   - status: 'success' | 'cancelled'
     *   - duration: Duration in seconds
     *   - summary: Task summary text
     *   - timestamp: ISO timestamp
     * 
     * Requirements: 3.6
     */
    handleTaskCompleted(data) {
        try {
            const timestamp = data.timestamp ? new Date(data.timestamp) : new Date();
            
            if (data.status === 'success') {
                this.taskStatus = 'completed';
                const message = `✓ Task completed successfully in ${this.formatDuration(data.duration)}`;
                this.addMessage('success', message, timestamp);
                
                // Announce to screen readers
                if (typeof window.accessibility !== 'undefined' && window.accessibility.announceToScreenReader) {
                    window.accessibility.announceToScreenReader(
                        `Task completed successfully in ${this.formatDuration(data.duration)}`,
                        'polite'
                    );
                }
                
                if (data.summary) {
                    this.addMessage('success', data.summary, timestamp);
                }
            } else if (data.status === 'cancelled') {
                this.taskStatus = 'cancelled';
                const message = `⚠ Task was cancelled after ${this.formatDuration(data.duration)}`;
                this.addMessage('warning', message, timestamp);
                
                // Announce to screen readers
                if (typeof window.accessibility !== 'undefined' && window.accessibility.announceToScreenReader) {
                    window.accessibility.announceToScreenReader(
                        `Task was cancelled after ${this.formatDuration(data.duration)}`,
                        'polite'
                    );
                }
            }
            
            // Notify other components
            window.dispatchEvent(new CustomEvent('task-completed', { 
                detail: data 
            }));
            
        } catch (error) {
            console.error('Error handling task completion:', error);
        }
    }
    
    /**
     * Handle task error notification
     * 
     * @param {Object} data - Error data
     *   - task_id: Task identifier
     *   - error_type: Error type/category
     *   - error_message: Error message text
     *   - suggestion: Suggested resolution
     *   - timestamp: ISO timestamp
     * 
     * Requirements: 3.7
     */
    handleTaskError(data) {
        try {
            const timestamp = data.timestamp ? new Date(data.timestamp) : new Date();
            
            this.taskStatus = 'failed';
            
            // Display error message
            const errorMsg = `✗ Task failed: ${data.error_message}`;
            this.addMessage('error', errorMsg, timestamp);
            
            // Announce error to screen readers with assertive priority
            if (typeof window.accessibility !== 'undefined' && window.accessibility.announceToScreenReader) {
                window.accessibility.announceToScreenReader(
                    `Task failed: ${data.error_message}`,
                    'assertive'
                );
            }
            
            // Display suggestion if available
            if (data.suggestion) {
                this.addMessage('info', `Suggestion: ${data.suggestion}`, timestamp);
            }
            
            // Notify other components
            window.dispatchEvent(new CustomEvent('task-error', { 
                detail: data 
            }));
            
        } catch (error) {
            console.error('Error handling task error:', error);
        }
    }
    
    /**
     * Add a message to the progress display
     * 
     * @param {string} type - Message type: 'info', 'warning', 'error', 'success'
     * @param {string} content - Message content
     * @param {Date} timestamp - Optional timestamp (defaults to now)
     * 
     * Requirements: 3.2, 3.3, 3.4, 18.1
     */
    addMessage(type, content, timestamp = new Date()) {
        // Create message object
        const message = {
            type: type,
            content: content,
            timestamp: timestamp
        };
        
        // Add to messages array
        this.messages.push(message);
        
        // Limit messages to prevent memory bloat (keep last 1000)
        const MAX_MESSAGES = 1000;
        if (this.messages.length > MAX_MESSAGES) {
            const toRemove = this.messages.length - MAX_MESSAGES;
            this.messages.splice(0, toRemove);
            
            // Remove old DOM elements
            if (this.outputContainer) {
                const children = this.outputContainer.children;
                for (let i = 0; i < toRemove && children.length > 0; i++) {
                    this.outputContainer.removeChild(children[0]);
                }
            }
        }
        
        // Create DOM element
        const messageElement = this.createMessageElement(message);
        
        // Append to container
        if (this.outputContainer) {
            this.outputContainer.appendChild(messageElement);
            
            // Auto-scroll if enabled (Req 3.4)
            if (this.autoScroll) {
                this.scrollToBottom();
            }
        }
    }
    
    /**
     * Create DOM element for a message
     * 
     * @param {Object} message - Message object
     * @returns {HTMLElement} Message element
     * 
     * Requirements: 3.3
     */
    createMessageElement(message) {
        const div = document.createElement('div');
        div.className = `progress-message ${message.type}`;
        div.setAttribute('data-type', message.type);
        
        // Create timestamp span
        const timestampSpan = document.createElement('span');
        timestampSpan.className = 'message-timestamp';
        timestampSpan.textContent = this.formatTimestamp(message.timestamp);
        
        // Create content span
        const contentSpan = document.createElement('span');
        contentSpan.className = 'message-content';
        
        // Format content (handle code blocks and special formatting)
        contentSpan.innerHTML = this.formatMessage(message.content);
        
        // Append children
        div.appendChild(timestampSpan);
        div.appendChild(contentSpan);
        
        return div;
    }
    
    /**
     * Format message content with syntax highlighting for code blocks
     * 
     * @param {string} content - Raw message content
     * @returns {string} Formatted HTML content
     * 
     * Requirements: 3.3
     */
    formatMessage(content) {
        // Escape HTML to prevent XSS
        let formatted = content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
        
        // Detect and highlight file paths (common in progress messages)
        formatted = formatted.replace(
            /(\/[\w\-./]+|[A-Z]:\\[\w\-\\/.]+|[\w\-./]+\.(py|js|ts|jsx|tsx|json|yaml|yml|md|txt|html|css))/gi,
            '<code class="filepath">$1</code>'
        );
        
        // Detect and highlight code blocks (backticks)
        formatted = formatted.replace(
            /`([^`]+)`/g,
            '<code class="inline-code">$1</code>'
        );
        
        // Make URLs clickable
        formatted = formatted.replace(
            /(https?:\/\/[^\s]+)/g,
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );
        
        return formatted;
    }
    
    /**
     * Format timestamp for display
     * 
     * @param {Date} timestamp - Timestamp to format
     * @returns {string} Formatted time string (HH:MM:SS)
     */
    formatTimestamp(timestamp) {
        const hours = String(timestamp.getHours()).padStart(2, '0');
        const minutes = String(timestamp.getMinutes()).padStart(2, '0');
        const seconds = String(timestamp.getSeconds()).padStart(2, '0');
        return `${hours}:${minutes}:${seconds}`;
    }
    
    /**
     * Format duration in seconds to human-readable string
     * 
     * @param {number} seconds - Duration in seconds
     * @returns {string} Formatted duration (e.g., "2m 34s")
     */
    formatDuration(seconds) {
        if (seconds < 60) {
            return `${Math.round(seconds)}s`;
        } else if (seconds < 3600) {
            const mins = Math.floor(seconds / 60);
            const secs = Math.round(seconds % 60);
            return `${mins}m ${secs}s`;
        } else {
            const hours = Math.floor(seconds / 3600);
            const mins = Math.floor((seconds % 3600) / 60);
            return `${hours}h ${mins}m`;
        }
    }
    
    /**
     * Toggle auto-scroll on/off
     * 
     * Requirements: 3.4, 3.5
     */
    toggleAutoScroll() {
        this.autoScroll = !this.autoScroll;
        this.updateAutoScrollButton();
        
        // If turning on, scroll to bottom immediately
        if (this.autoScroll) {
            this.scrollToBottom();
        }
        
        console.log(`Auto-scroll ${this.autoScroll ? 'enabled' : 'disabled'}`);
    }
    
    /**
     * Update auto-scroll button visual state
     */
    updateAutoScrollButton() {
        if (this.autoScrollToggle) {
            this.autoScrollToggle.classList.toggle('active', this.autoScroll);
            this.autoScrollToggle.setAttribute(
                'title',
                this.autoScroll ? 'Auto-scroll: ON' : 'Auto-scroll: OFF'
            );
        }
    }
    
    /**
     * Handle scroll event to detect manual scrolling
     * 
     * Requirements: 3.5
     */
    handleScroll() {
        if (!this.outputContainer) return;
        
        // Check if user is at bottom
        const isAtBottom = this.isScrolledToBottom();
        
        // If user manually scrolled up, disable auto-scroll
        if (!isAtBottom && this.autoScroll) {
            this.autoScroll = false;
            this.updateAutoScrollButton();
            console.log('Auto-scroll disabled (user scrolled up)');
        }
        // If user manually scrolled to bottom, enable auto-scroll
        else if (isAtBottom && !this.autoScroll) {
            this.autoScroll = true;
            this.updateAutoScrollButton();
            console.log('Auto-scroll enabled (user scrolled to bottom)');
        }
    }
    
    /**
     * Check if container is scrolled to bottom
     * 
     * @returns {boolean} True if at bottom
     */
    isScrolledToBottom() {
        if (!this.outputContainer) return true;
        
        const threshold = 50; // pixels from bottom to consider "at bottom"
        const scrollTop = this.outputContainer.scrollTop;
        const scrollHeight = this.outputContainer.scrollHeight;
        const clientHeight = this.outputContainer.clientHeight;
        
        return scrollHeight - scrollTop - clientHeight < threshold;
    }
    
    /**
     * Scroll output container to bottom
     * 
     * Requirements: 3.4
     */
    scrollToBottom() {
        if (!this.outputContainer) return;
        
        // Use smooth scrolling for better UX
        this.outputContainer.scrollTo({
            top: this.outputContainer.scrollHeight,
            behavior: 'smooth'
        });
    }
    
    /**
     * Clear all messages from display
     * 
     * Requirements: 3.8
     */
    clearMessages() {
        // Clear messages array
        this.messages = [];
        
        // Clear pending updates
        this.pendingUpdates = [];
        
        // Clear DOM
        if (this.outputContainer) {
            this.outputContainer.innerHTML = '';
            
            // Add placeholder message
            this.addMessage('info', 'Output cleared. Ready for next task.');
        }
        
        // Reset task status
        this.taskStatus = 'idle';
        
        // Announce to screen readers
        if (typeof window.accessibility !== 'undefined' && window.accessibility.announceToScreenReader) {
            window.accessibility.announceToScreenReader('Output cleared', 'polite');
        }
        
        console.log('Progress output cleared');
    }
    
    /**
     * Copy all output to clipboard
     * 
     * Requirements: 3.9
     */
    async copyToClipboard() {
        try {
            // Generate plain text output from messages
            const plainText = this.messages
                .map(msg => `[${this.formatTimestamp(msg.timestamp)}] [${msg.type.toUpperCase()}] ${msg.content}`)
                .join('\n');
            
            // Use Clipboard API
            if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(plainText);
                console.log('Output copied to clipboard');
                
                // Show visual feedback
                this.showCopyFeedback();
            } else {
                // Fallback for browsers that don't support Clipboard API
                this.copyToClipboardFallback(plainText);
            }
            
        } catch (error) {
            console.error('Error copying to clipboard:', error);
            alert('Failed to copy to clipboard. Please try again.');
        }
    }
    
    /**
     * Fallback clipboard copy for older browsers
     * 
     * @param {string} text - Text to copy
     */
    copyToClipboardFallback(text) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.left = '-9999px';
        document.body.appendChild(textarea);
        
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        
        console.log('Output copied to clipboard (fallback method)');
        this.showCopyFeedback();
    }
    
    /**
     * Show visual feedback when text is copied
     */
    showCopyFeedback() {
        if (!this.copyButton) return;
        
        // Announce to screen readers
        if (typeof window.accessibility !== 'undefined' && window.accessibility.announceToScreenReader) {
            window.accessibility.announceToScreenReader('Output copied to clipboard', 'polite');
        }
        
        // Temporarily change button content
        const originalHTML = this.copyButton.innerHTML;
        this.copyButton.innerHTML = `
            <svg class="icon" viewBox="0 0 24 24" width="20" height="20">
                <path d="M5 13l4 4L19 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
            </svg>
        `;
        this.copyButton.classList.add('success');
        
        // Restore after 2 seconds
        setTimeout(() => {
            this.copyButton.innerHTML = originalHTML;
            this.copyButton.classList.remove('success');
        }, 2000);
    }
    
    /**
     * Get current task status
     * 
     * @returns {string} Current status
     */
    getTaskStatus() {
        return this.taskStatus;
    }
    
    /**
     * Set task status (used by Task Input component)
     * 
     * @param {string} status - New status
     */
    setTaskStatus(status) {
        this.taskStatus = status;
    }
    
    /**
     * Get all messages
     * 
     * @returns {Array} Array of message objects
     */
    getMessages() {
        return [...this.messages];
    }
}

// Create singleton instance
const progressDisplay = new ProgressDisplay();

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.progressDisplay = progressDisplay;
}

// Also expose globally for Eel callbacks
if (typeof window !== 'undefined') {
    window.update_progress = progressDisplay.handleProgressUpdate.bind(progressDisplay);
    window.task_completed = progressDisplay.handleTaskCompleted.bind(progressDisplay);
    window.task_error = progressDisplay.handleTaskError.bind(progressDisplay);
}
