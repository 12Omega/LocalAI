/**
 * Integration Tests for Progress Display Component
 * 
 * Tests real-time progress updates, message formatting, auto-scroll,
 * and interaction with backend via Eel callbacks.
 * 
 * Requirements tested: 3.1-3.9, 13.7
 */

describe('ProgressDisplay - Integration Tests', () => {
    let progressDisplay;
    
    // Helper to set up DOM
    const setupDOM = () => {
        document.body.innerHTML = `
            <div id="progress-display-panel">
                <div id="progress-output" class="progress-output"></div>
                <div class="progress-controls">
                    <button id="auto-scroll-toggle" class="icon-button active" title="Auto-scroll: ON">
                        Auto-scroll
                    </button>
                    <button id="copy-output-btn" class="icon-button" title="Copy to clipboard">
                        Copy
                    </button>
                    <button id="clear-output-btn" class="icon-button" title="Clear output">
                        Clear
                    </button>
                </div>
            </div>
        `;
    };
    
    beforeEach(() => {
        setupDOM();
        
        // Mock clipboard API
        Object.assign(navigator, {
            clipboard: {
                writeText: jest.fn(() => Promise.resolve())
            }
        });
        
        // Create new instance
        progressDisplay = new ProgressDisplay();
    });
    
    afterEach(() => {
        document.body.innerHTML = '';
        jest.clearAllMocks();
    });
    
    /**
     * Requirement 3.1: Show current operation when task starts
     */
    describe('Task Start Display', () => {
        test('should display message when task starts', () => {
            const outputContainer = document.getElementById('progress-output');
            
            progressDisplay.addMessage('info', 'Starting task execution...');
            
            const messages = outputContainer.querySelectorAll('.progress-message');
            expect(messages.length).toBe(1);
            expect(messages[0].textContent).toContain('Starting task execution');
        });
    });
    
    /**
     * Requirement 3.2: Update with new output within 500ms
     * Requirement 13.7: Batch updates to maintain 30fps
     */
    describe('Real-time Progress Updates', () => {
        test('should add message to display within 500ms', (done) => {
            const outputContainer = document.getElementById('progress-output');
            const startTime = Date.now();
            
            progressDisplay.handleProgressUpdate({
                type: 'info',
                message: 'Processing file: main.py',
                timestamp: new Date().toISOString()
            });
            
            // Process pending updates immediately for testing
            setTimeout(() => {
                progressDisplay.processPendingUpdates();
                
                const elapsed = Date.now() - startTime;
                const messages = outputContainer.querySelectorAll('.progress-message');
                
                expect(elapsed).toBeLessThan(500);
                expect(messages.length).toBeGreaterThan(0);
                done();
            }, 50);
        });
        
        test('should batch rapid updates for performance (Req 13.7)', (done) => {
            const outputContainer = document.getElementById('progress-output');
            
            // Send 100 rapid updates
            for (let i = 0; i < 100; i++) {
                progressDisplay.handleProgressUpdate({
                    type: 'info',
                    message: `Processing file ${i}`,
                    timestamp: new Date().toISOString()
                });
            }
            
            // Check that they're queued
            expect(progressDisplay.pendingUpdates.length).toBe(100);
            
            // Wait for batch processing (33ms interval)
            setTimeout(() => {
                progressDisplay.processPendingUpdates();
                
                const messages = outputContainer.querySelectorAll('.progress-message');
                expect(messages.length).toBe(100);
                expect(progressDisplay.pendingUpdates.length).toBe(0);
                done();
            }, 50);
        });
        
        test('should process pending updates automatically within batch interval', (done) => {
            const outputContainer = document.getElementById('progress-output');
            
            progressDisplay.handleProgressUpdate({
                type: 'info',
                message: 'Test message',
                timestamp: new Date().toISOString()
            });
            
            // Wait for automatic batch processing (33ms + margin)
            setTimeout(() => {
                const messages = outputContainer.querySelectorAll('.progress-message');
                expect(messages.length).toBe(1);
                done();
            }, 100);
        });
    });
    
    /**
     * Requirement 3.3: Display colored/formatted text for different message types
     */
    describe('Message Formatting and Coloring', () => {
        test('should apply correct class for info messages', () => {
            progressDisplay.addMessage('info', 'Analyzing project structure');
            
            const message = document.querySelector('.progress-message');
            expect(message.classList.contains('info')).toBe(true);
            expect(message.dataset.type).toBe('info');
        });
        
        test('should apply correct class for warning messages', () => {
            progressDisplay.addMessage('warning', 'Deprecation warning detected');
            
            const message = document.querySelector('.progress-message');
            expect(message.classList.contains('warning')).toBe(true);
            expect(message.dataset.type).toBe('warning');
        });
        
        test('should apply correct class for error messages', () => {
            progressDisplay.addMessage('error', 'File not found: config.yaml');
            
            const message = document.querySelector('.progress-message');
            expect(message.classList.contains('error')).toBe(true);
            expect(message.dataset.type).toBe('error');
        });
        
        test('should apply correct class for success messages', () => {
            progressDisplay.addMessage('success', 'All tests passed');
            
            const message = document.querySelector('.progress-message');
            expect(message.classList.contains('success')).toBe(true);
            expect(message.dataset.type).toBe('success');
        });
        
        test('should format file paths as code', () => {
            progressDisplay.addMessage('info', 'Created file: src/calculator.py');
            
            const messageContent = document.querySelector('.message-content');
            expect(messageContent.innerHTML).toContain('<code class="filepath">');
            expect(messageContent.innerHTML).toContain('src/calculator.py');
        });
        
        test('should format inline code with backticks', () => {
            progressDisplay.addMessage('info', 'Function `calculate()` added');
            
            const messageContent = document.querySelector('.message-content');
            expect(messageContent.innerHTML).toContain('<code class="inline-code">');
        });
        
        test('should make URLs clickable', () => {
            progressDisplay.addMessage('info', 'See https://example.com for details');
            
            const messageContent = document.querySelector('.message-content');
            expect(messageContent.innerHTML).toContain('<a href="https://example.com"');
        });
        
        test('should escape HTML to prevent XSS', () => {
            progressDisplay.addMessage('info', '<script>alert("xss")</script>');
            
            const messageContent = document.querySelector('.message-content');
            expect(messageContent.innerHTML).not.toContain('<script>');
            expect(messageContent.innerHTML).toContain('&lt;script&gt;');
        });
    });
    
    /**
     * Requirements 3.4, 3.5: Auto-scroll and manual scroll
     */
    describe('Auto-scroll Functionality', () => {
        test('should auto-scroll to bottom when new message added (Req 3.4)', () => {
            const outputContainer = document.getElementById('progress-output');
            const scrollToSpy = jest.spyOn(outputContainer, 'scrollTo');
            
            // Add multiple messages to make scrolling necessary
            for (let i = 0; i < 20; i++) {
                progressDisplay.addMessage('info', `Message ${i}`);
            }
            
            expect(scrollToSpy).toHaveBeenCalled();
            expect(progressDisplay.autoScroll).toBe(true);
        });
        
        test('should allow users to scroll up to review previous output (Req 3.5)', () => {
            const outputContainer = document.getElementById('progress-output');
            
            // Add messages
            for (let i = 0; i < 20; i++) {
                progressDisplay.addMessage('info', `Message ${i}`);
            }
            
            // Simulate user scrolling up
            outputContainer.scrollTop = 0;
            outputContainer.dispatchEvent(new Event('scroll'));
            
            // Auto-scroll should be disabled
            expect(progressDisplay.autoScroll).toBe(false);
        });
        
        test('should toggle auto-scroll when button clicked', () => {
            const toggleButton = document.getElementById('auto-scroll-toggle');
            
            expect(progressDisplay.autoScroll).toBe(true);
            
            toggleButton.click();
            expect(progressDisplay.autoScroll).toBe(false);
            expect(toggleButton.classList.contains('active')).toBe(false);
            
            toggleButton.click();
            expect(progressDisplay.autoScroll).toBe(true);
            expect(toggleButton.classList.contains('active')).toBe(true);
        });
        
        test('should re-enable auto-scroll when user scrolls to bottom', () => {
            const outputContainer = document.getElementById('progress-output');
            
            // Add messages
            for (let i = 0; i < 20; i++) {
                progressDisplay.addMessage('info', `Message ${i}`);
            }
            
            // Disable auto-scroll by scrolling up
            progressDisplay.autoScroll = false;
            outputContainer.scrollTop = 0;
            
            // Mock scrolling to bottom
            Object.defineProperty(outputContainer, 'scrollHeight', { value: 1000 });
            Object.defineProperty(outputContainer, 'clientHeight', { value: 500 });
            outputContainer.scrollTop = 500; // At bottom
            
            outputContainer.dispatchEvent(new Event('scroll'));
            
            expect(progressDisplay.autoScroll).toBe(true);
        });
    });
    
    /**
     * Requirement 3.6: Show success indicator with completion timestamp
     */
    describe('Task Completion Display', () => {
        test('should show success message when task completes', () => {
            progressDisplay.handleTaskCompleted({
                status: 'success',
                duration: 145.5,
                summary: 'Created 3 files',
                timestamp: new Date().toISOString()
            });
            
            const successMessage = document.querySelector('.progress-message.success');
            expect(successMessage).toBeTruthy();
            expect(successMessage.textContent).toContain('completed successfully');
            expect(successMessage.textContent).toContain('2m 26s');
        });
        
        test('should display task summary on completion', () => {
            progressDisplay.handleTaskCompleted({
                status: 'success',
                duration: 45.0,
                summary: 'Created 3 files, ran 12 tests',
                timestamp: new Date().toISOString()
            });
            
            const messages = document.querySelectorAll('.progress-message.success');
            const summaryMessage = Array.from(messages).find(m => 
                m.textContent.includes('Created 3 files')
            );
            
            expect(summaryMessage).toBeTruthy();
        });
        
        test('should show cancelled status when task is cancelled', () => {
            progressDisplay.handleTaskCompleted({
                status: 'cancelled',
                duration: 30.0,
                timestamp: new Date().toISOString()
            });
            
            const warningMessage = document.querySelector('.progress-message.warning');
            expect(warningMessage).toBeTruthy();
            expect(warningMessage.textContent).toContain('cancelled');
        });
        
        test('should include timestamp with completion message', () => {
            progressDisplay.handleTaskCompleted({
                status: 'success',
                duration: 60.0,
                timestamp: new Date().toISOString()
            });
            
            const message = document.querySelector('.progress-message.success');
            const timestamp = message.querySelector('.message-timestamp');
            
            expect(timestamp).toBeTruthy();
            expect(timestamp.textContent).toMatch(/\d{2}:\d{2}:\d{2}/);
        });
    });
    
    /**
     * Requirement 3.7: Show error indicator with error details
     */
    describe('Task Error Display', () => {
        test('should show error message when task fails', () => {
            progressDisplay.handleTaskError({
                task_id: 'test-123',
                error_type: 'FileNotFoundError',
                error_message: 'Config file not found',
                timestamp: new Date().toISOString()
            });
            
            const errorMessage = document.querySelector('.progress-message.error');
            expect(errorMessage).toBeTruthy();
            expect(errorMessage.textContent).toContain('failed');
            expect(errorMessage.textContent).toContain('Config file not found');
        });
        
        test('should display suggestion when provided', () => {
            progressDisplay.handleTaskError({
                task_id: 'test-123',
                error_message: 'Connection failed',
                suggestion: 'Check if the LLM server is running',
                timestamp: new Date().toISOString()
            });
            
            const messages = document.querySelectorAll('.progress-message');
            const suggestionMessage = Array.from(messages).find(m =>
                m.textContent.includes('Suggestion')
            );
            
            expect(suggestionMessage).toBeTruthy();
            expect(suggestionMessage.textContent).toContain('Check if the LLM server is running');
        });
        
        test('should set task status to failed on error', () => {
            progressDisplay.handleTaskError({
                error_message: 'Test error',
                timestamp: new Date().toISOString()
            });
            
            expect(progressDisplay.taskStatus).toBe('failed');
        });
    });
    
    /**
     * Requirement 3.8: Clear button to remove current output
     */
    describe('Clear Output Functionality', () => {
        test('should provide clear button', () => {
            const clearButton = document.getElementById('clear-output-btn');
            
            expect(clearButton).toBeTruthy();
        });
        
        test('should clear all messages when clear button clicked', () => {
            const outputContainer = document.getElementById('progress-output');
            const clearButton = document.getElementById('clear-output-btn');
            
            // Add some messages
            progressDisplay.addMessage('info', 'Message 1');
            progressDisplay.addMessage('info', 'Message 2');
            progressDisplay.addMessage('info', 'Message 3');
            
            expect(outputContainer.children.length).toBe(3);
            
            // Click clear button
            clearButton.click();
            
            // Should have just one placeholder message
            expect(outputContainer.children.length).toBe(1);
            expect(outputContainer.textContent).toContain('Output cleared');
        });
        
        test('should reset task status when clearing', () => {
            const clearButton = document.getElementById('clear-output-btn');
            
            progressDisplay.taskStatus = 'completed';
            progressDisplay.addMessage('success', 'Task completed');
            
            clearButton.click();
            
            expect(progressDisplay.taskStatus).toBe('idle');
        });
        
        test('should clear messages array', () => {
            const clearButton = document.getElementById('clear-output-btn');
            
            progressDisplay.addMessage('info', 'Message 1');
            progressDisplay.addMessage('info', 'Message 2');
            
            expect(progressDisplay.messages.length).toBe(2);
            
            clearButton.click();
            
            // Should be cleared, then placeholder added
            expect(progressDisplay.messages.length).toBe(1);
        });
    });
    
    /**
     * Requirement 3.9: Copy button to copy output to clipboard
     */
    describe('Copy to Clipboard Functionality', () => {
        test('should provide copy button', () => {
            const copyButton = document.getElementById('copy-output-btn');
            
            expect(copyButton).toBeTruthy();
        });
        
        test('should copy all output to clipboard when button clicked', async () => {
            const copyButton = document.getElementById('copy-output-btn');
            
            // Add messages
            progressDisplay.addMessage('info', 'Message 1');
            progressDisplay.addMessage('success', 'Message 2');
            progressDisplay.addMessage('error', 'Message 3');
            
            // Click copy button
            await copyButton.click();
            
            expect(navigator.clipboard.writeText).toHaveBeenCalled();
            
            const copiedText = navigator.clipboard.writeText.mock.calls[0][0];
            expect(copiedText).toContain('Message 1');
            expect(copiedText).toContain('Message 2');
            expect(copiedText).toContain('Message 3');
        });
        
        test('should include timestamps and message types in copied text', async () => {
            const copyButton = document.getElementById('copy-output-btn');
            
            progressDisplay.addMessage('info', 'Test message');
            
            await copyButton.click();
            
            const copiedText = navigator.clipboard.writeText.mock.calls[0][0];
            expect(copiedText).toMatch(/\[\d{2}:\d{2}:\d{2}\]/); // Timestamp
            expect(copiedText).toContain('[INFO]'); // Message type
            expect(copiedText).toContain('Test message');
        });
        
        test('should show visual feedback after copying', async () => {
            const copyButton = document.getElementById('copy-output-btn');
            
            progressDisplay.addMessage('info', 'Test');
            await copyButton.click();
            
            // Check for success class
            expect(copyButton.classList.contains('success')).toBe(true);
        });
    });
    
    /**
     * Integration: Backend callback handling
     */
    describe('Backend Integration via Eel', () => {
        test('should expose callbacks globally for Eel', () => {
            expect(typeof window.update_progress).toBe('function');
            expect(typeof window.task_completed).toBe('function');
            expect(typeof window.task_error).toBe('function');
        });
        
        test('should handle progress update from backend', () => {
            const outputContainer = document.getElementById('progress-output');
            
            // Simulate backend call
            window.update_progress({
                type: 'info',
                message: 'Analyzing code...',
                timestamp: new Date().toISOString()
            });
            
            // Process pending updates
            setTimeout(() => {
                progressDisplay.processPendingUpdates();
                
                const messages = outputContainer.querySelectorAll('.progress-message');
                expect(messages.length).toBeGreaterThan(0);
            }, 50);
        });
        
        test('should handle task completion from backend', () => {
            const outputContainer = document.getElementById('progress-output');
            
            window.task_completed({
                task_id: 'test-123',
                status: 'success',
                duration: 60.0,
                timestamp: new Date().toISOString()
            });
            
            const successMessage = outputContainer.querySelector('.progress-message.success');
            expect(successMessage).toBeTruthy();
        });
        
        test('should handle task error from backend', () => {
            const outputContainer = document.getElementById('progress-output');
            
            window.task_error({
                task_id: 'test-123',
                error_message: 'Connection timeout',
                timestamp: new Date().toISOString()
            });
            
            const errorMessage = outputContainer.querySelector('.progress-message.error');
            expect(errorMessage).toBeTruthy();
        });
    });
    
    /**
     * Complete end-to-end workflow test
     */
    describe('Complete Workflow', () => {
        test('should handle complete task execution lifecycle', (done) => {
            const outputContainer = document.getElementById('progress-output');
            
            // Step 1: Task starts
            progressDisplay.handleProgressUpdate({
                type: 'info',
                message: 'Starting task execution...',
                timestamp: new Date().toISOString()
            });
            
            // Step 2: Progress updates
            setTimeout(() => {
                progressDisplay.processPendingUpdates();
                
                progressDisplay.handleProgressUpdate({
                    type: 'info',
                    message: 'Analyzing file: main.py',
                    timestamp: new Date().toISOString()
                });
                
                progressDisplay.handleProgressUpdate({
                    type: 'success',
                    message: 'File processed successfully',
                    timestamp: new Date().toISOString()
                });
                
                setTimeout(() => {
                    progressDisplay.processPendingUpdates();
                    
                    // Step 3: Task completes
                    progressDisplay.handleTaskCompleted({
                        status: 'success',
                        duration: 45.5,
                        summary: 'Task completed',
                        timestamp: new Date().toISOString()
                    });
                    
                    // Verify messages
                    const messages = outputContainer.querySelectorAll('.progress-message');
                    expect(messages.length).toBeGreaterThan(0);
                    
                    const successMessages = outputContainer.querySelectorAll('.progress-message.success');
                    expect(successMessages.length).toBeGreaterThan(0);
                    
                    expect(progressDisplay.taskStatus).toBe('completed');
                    
                    done();
                }, 50);
            }, 50);
        });
    });
});
