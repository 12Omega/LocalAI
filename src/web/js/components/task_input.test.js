/**
 * Integration Tests for Task Input Panel Component
 * 
 * Tests the complete workflow of task input, validation, execution,
 * and interaction with the Eel backend.
 * 
 * Requirements tested: 2.1-2.9
 */

describe('TaskInputPanel - Integration Tests', () => {
    let taskInputPanel;
    let mockEel;
    let mockStateManager;
    
    // Helper to set up DOM
    const setupDOM = () => {
        document.body.innerHTML = `
            <div id="task-input-panel">
                <textarea 
                    id="task-description" 
                    placeholder="Enter your development task here..."
                    maxlength="5000"
                ></textarea>
                <div class="char-counter">
                    <span id="char-count">0</span> / 5000
                </div>
                <div class="button-group">
                    <button id="run-task-btn" class="btn btn-primary">
                        <span>Run Task</span>
                    </button>
                    <button id="stop-task-btn" class="btn btn-danger" style="display: none;">
                        <span>Stop</span>
                    </button>
                </div>
                <div id="task-status" class="task-status" style="display: none;"></div>
            </div>
        `;
    };
    
    // Helper to create mock Eel
    const createMockEel = () => {
        return {
            run_task: jest.fn(() => () => Promise.resolve({ 
                success: true, 
                task_id: 'test-task-123' 
            })),
            stop_task: jest.fn(() => () => Promise.resolve({ 
                success: true 
            }))
        };
    };
    
    // Helper to create mock StateManager
    const createMockStateManager = () => {
        const listeners = {};
        return {
            set: jest.fn(),
            get: jest.fn(),
            subscribe: jest.fn((key, callback) => {
                listeners[key] = callback;
            }),
            _trigger: (key, value) => {
                if (listeners[key]) {
                    listeners[key](value);
                }
            }
        };
    };
    
    beforeEach(() => {
        // Set up fresh DOM for each test
        setupDOM();
        
        // Create mocks
        mockEel = createMockEel();
        mockStateManager = createMockStateManager();
        
        // Inject mocks into global scope
        global.eel = mockEel;
        global.stateManager = mockStateManager;
        
        // Create new instance
        taskInputPanel = new TaskInputPanel();
        taskInputPanel.init();
    });
    
    afterEach(() => {
        // Clean up
        if (taskInputPanel && taskInputPanel.destroy) {
            taskInputPanel.destroy();
        }
        document.body.innerHTML = '';
        delete global.eel;
        delete global.stateManager;
        jest.clearAllMocks();
    });
    
    /**
     * Requirement 2.1: Multi-line text area accepting at least 5000 characters
     */
    describe('Text Input', () => {
        test('should provide textarea accepting 5000 characters', () => {
            const textarea = document.getElementById('task-description');
            
            expect(textarea).toBeTruthy();
            expect(textarea.tagName).toBe('TEXTAREA');
            expect(textarea.maxLength).toBeGreaterThanOrEqual(5000);
        });
        
        test('should allow input up to 5000 characters', () => {
            const textarea = document.getElementById('task-description');
            const longText = 'A'.repeat(5000);
            
            textarea.value = longText;
            textarea.dispatchEvent(new Event('input'));
            
            expect(textarea.value.length).toBe(5000);
        });
    });
    
    /**
     * Requirement 2.2: Character count indicator
     */
    describe('Character Counter', () => {
        test('should display character count indicator', () => {
            const charCount = document.getElementById('char-count');
            
            expect(charCount).toBeTruthy();
            expect(charCount.textContent).toBe('0');
        });
        
        test('should update character count as user types', () => {
            const textarea = document.getElementById('task-description');
            const charCount = document.getElementById('char-count');
            
            // Type some text
            textarea.value = 'Create a calculator module';
            textarea.dispatchEvent(new Event('input'));
            
            expect(charCount.textContent).toBe('26');
            
            // Type more text
            textarea.value = 'Create a calculator module with unit tests';
            textarea.dispatchEvent(new Event('input'));
            
            expect(charCount.textContent).toBe('43');
        });
        
        test('should add warning class when approaching limit', () => {
            const textarea = document.getElementById('task-description');
            const charCount = document.getElementById('char-count');
            
            // Type text near limit (90% = 4500 chars)
            textarea.value = 'A'.repeat(4500);
            textarea.dispatchEvent(new Event('input'));
            
            expect(charCount.classList.contains('warning')).toBe(true);
        });
    });
    
    /**
     * Requirements 2.3, 2.4: Button states based on input
     */
    describe('Run Button State', () => {
        test('should disable run button when textarea is empty (Req 2.4)', () => {
            const runButton = document.getElementById('run-task-btn');
            
            expect(runButton.disabled).toBe(true);
        });
        
        test('should enable run button when text is entered (Req 2.3)', () => {
            const textarea = document.getElementById('task-description');
            const runButton = document.getElementById('run-task-btn');
            
            textarea.value = 'Create a calculator module';
            textarea.dispatchEvent(new Event('input'));
            
            expect(runButton.disabled).toBe(false);
        });
        
        test('should disable run button when input is cleared', () => {
            const textarea = document.getElementById('task-description');
            const runButton = document.getElementById('run-task-btn');
            
            // Enter text
            textarea.value = 'Create a calculator module';
            textarea.dispatchEvent(new Event('input'));
            expect(runButton.disabled).toBe(false);
            
            // Clear text
            textarea.value = '';
            textarea.dispatchEvent(new Event('input'));
            expect(runButton.disabled).toBe(true);
        });
        
        test('should disable run button with only whitespace', () => {
            const textarea = document.getElementById('task-description');
            const runButton = document.getElementById('run-task-btn');
            
            textarea.value = '   \n\t  ';
            textarea.dispatchEvent(new Event('input'));
            
            expect(runButton.disabled).toBe(true);
        });
    });
    
    /**
     * Requirement 2.5: Pass task description to backend
     * Requirement 2.6: Disable run button while running
     * Requirement 2.7: Re-enable button when complete
     */
    describe('Task Execution Workflow', () => {
        test('should call backend run_task when run button clicked (Req 2.5)', async () => {
            const textarea = document.getElementById('task-description');
            const runButton = document.getElementById('run-task-btn');
            
            const taskDescription = 'Create a calculator module';
            textarea.value = taskDescription;
            textarea.dispatchEvent(new Event('input'));
            
            // Click run button
            runButton.click();
            
            // Wait for async operation
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(mockEel.run_task).toHaveBeenCalledWith(taskDescription);
        });
        
        test('should show running status and disable button while task executing (Req 2.6)', async () => {
            const textarea = document.getElementById('task-description');
            const runButton = document.getElementById('run-task-btn');
            const stopButton = document.getElementById('stop-task-btn');
            const statusDiv = document.getElementById('task-status');
            
            textarea.value = 'Create a calculator module';
            textarea.dispatchEvent(new Event('input'));
            
            // Click run button
            runButton.click();
            
            // Wait for async operation
            await new Promise(resolve => setTimeout(resolve, 0));
            
            // Check running state
            expect(runButton.style.display).toBe('none');
            expect(stopButton.style.display).toBe('inline-flex');
            expect(statusDiv.textContent).toContain('Running');
            expect(textarea.disabled).toBe(true);
        });
        
        test('should re-enable button when task completes (Req 2.7)', async () => {
            const textarea = document.getElementById('task-description');
            const runButton = document.getElementById('run-task-btn');
            const stopButton = document.getElementById('stop-task-btn');
            
            textarea.value = 'Create a calculator module';
            textarea.dispatchEvent(new Event('input'));
            
            // Start task
            runButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            // Simulate task completion from backend
            taskInputPanel.handleTaskCompleted({ 
                success: true, 
                message: 'Task completed successfully' 
            });
            
            // Check button states
            expect(runButton.style.display).toBe('inline-flex');
            expect(stopButton.style.display).toBe('none');
            expect(runButton.disabled).toBe(false);
            expect(textarea.disabled).toBe(false);
        });
        
        test('should handle backend error gracefully', async () => {
            const textarea = document.getElementById('task-description');
            const runButton = document.getElementById('run-task-btn');
            const statusDiv = document.getElementById('task-status');
            
            // Mock error response
            mockEel.run_task = jest.fn(() => () => Promise.resolve({ 
                success: false, 
                error: 'Connection failed' 
            }));
            
            textarea.value = 'Create a calculator module';
            textarea.dispatchEvent(new Event('input'));
            
            runButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(statusDiv.textContent).toContain('Connection failed');
            expect(runButton.disabled).toBe(false); // Re-enabled after error
        });
    });
    
    /**
     * Requirements 2.8, 2.9: Stop button functionality
     */
    describe('Stop Task Functionality', () => {
        test('should provide stop button to cancel running task (Req 2.8)', async () => {
            const stopButton = document.getElementById('stop-task-btn');
            
            expect(stopButton).toBeTruthy();
        });
        
        test('should call backend stop_task when stop button clicked (Req 2.9)', async () => {
            const textarea = document.getElementById('task-description');
            const runButton = document.getElementById('run-task-btn');
            const stopButton = document.getElementById('stop-task-btn');
            
            // Start a task
            textarea.value = 'Create a calculator module';
            textarea.dispatchEvent(new Event('input'));
            runButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            // Click stop button
            stopButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(mockEel.stop_task).toHaveBeenCalled();
        });
        
        test('should update UI when task is cancelled', async () => {
            const textarea = document.getElementById('task-description');
            const runButton = document.getElementById('run-task-btn');
            const stopButton = document.getElementById('stop-task-btn');
            const statusDiv = document.getElementById('task-status');
            
            // Start task
            textarea.value = 'Create a calculator module';
            textarea.dispatchEvent(new Event('input'));
            runButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            // Stop task
            stopButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            // Check UI state
            expect(statusDiv.textContent).toContain('cancelled');
            expect(runButton.style.display).toBe('inline-flex');
            expect(stopButton.style.display).toBe('none');
        });
        
        test('should only show stop button when task is running', async () => {
            const stopButton = document.getElementById('stop-task-btn');
            
            // Initially hidden
            expect(stopButton.style.display).toBe('none');
            
            // Start task
            const textarea = document.getElementById('task-description');
            const runButton = document.getElementById('run-task-btn');
            textarea.value = 'Test task';
            textarea.dispatchEvent(new Event('input'));
            runButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            // Should be visible
            expect(stopButton.style.display).toBe('inline-flex');
        });
    });
    
    /**
     * Integration: State Manager synchronization
     */
    describe('State Manager Integration', () => {
        test('should update state manager when task starts', async () => {
            const textarea = document.getElementById('task-description');
            const runButton = document.getElementById('run-task-btn');
            
            textarea.value = 'Create a calculator module';
            textarea.dispatchEvent(new Event('input'));
            runButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(mockStateManager.set).toHaveBeenCalledWith('isTaskRunning', true);
            expect(mockStateManager.set).toHaveBeenCalledWith('currentTaskId', 'test-task-123');
        });
        
        test('should update state manager when task stops', async () => {
            const textarea = document.getElementById('task-description');
            const runButton = document.getElementById('run-task-btn');
            
            // Start and stop task
            textarea.value = 'Create a calculator module';
            textarea.dispatchEvent(new Event('input'));
            runButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            taskInputPanel.handleTaskCompleted({ success: true });
            
            expect(mockStateManager.set).toHaveBeenCalledWith('isTaskRunning', false);
            expect(mockStateManager.set).toHaveBeenCalledWith('currentTaskId', null);
        });
        
        test('should respond to state changes from state manager', () => {
            const runButton = document.getElementById('run-task-btn');
            const textarea = document.getElementById('task-description');
            
            textarea.value = 'Test task';
            textarea.dispatchEvent(new Event('input'));
            
            // Simulate state change from external source
            mockStateManager._trigger('isTaskRunning', true);
            
            expect(runButton.disabled).toBe(true);
        });
    });
    
    /**
     * Integration: Keyboard shortcuts
     */
    describe('Keyboard Shortcuts', () => {
        test('should run task on Ctrl+Enter', async () => {
            const textarea = document.getElementById('task-description');
            
            textarea.value = 'Create a calculator module';
            textarea.dispatchEvent(new Event('input'));
            
            // Simulate Ctrl+Enter
            const event = new KeyboardEvent('keydown', { 
                key: 'Enter', 
                ctrlKey: true 
            });
            textarea.dispatchEvent(event);
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(mockEel.run_task).toHaveBeenCalled();
        });
        
        test('should run task on Cmd+Enter (Mac)', async () => {
            const textarea = document.getElementById('task-description');
            
            textarea.value = 'Create a calculator module';
            textarea.dispatchEvent(new Event('input'));
            
            // Simulate Cmd+Enter
            const event = new KeyboardEvent('keydown', { 
                key: 'Enter', 
                metaKey: true 
            });
            textarea.dispatchEvent(event);
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(mockEel.run_task).toHaveBeenCalled();
        });
        
        test('should not run task on Enter without Ctrl/Cmd', () => {
            const textarea = document.getElementById('task-description');
            
            textarea.value = 'Create a calculator module';
            textarea.dispatchEvent(new Event('input'));
            
            // Simulate Enter without modifier
            const event = new KeyboardEvent('keydown', { key: 'Enter' });
            textarea.dispatchEvent(event);
            
            expect(mockEel.run_task).not.toHaveBeenCalled();
        });
    });
    
    /**
     * Complete end-to-end workflow test
     */
    describe('Complete Workflow', () => {
        test('should handle complete task lifecycle from input to completion', async () => {
            const textarea = document.getElementById('task-description');
            const charCount = document.getElementById('char-count');
            const runButton = document.getElementById('run-task-btn');
            const stopButton = document.getElementById('stop-task-btn');
            const statusDiv = document.getElementById('task-status');
            
            // Step 1: Initially disabled
            expect(runButton.disabled).toBe(true);
            expect(charCount.textContent).toBe('0');
            
            // Step 2: Enter text
            const taskDescription = 'Create a calculator module with unit tests';
            textarea.value = taskDescription;
            textarea.dispatchEvent(new Event('input'));
            
            expect(charCount.textContent).toBe(String(taskDescription.length));
            expect(runButton.disabled).toBe(false);
            
            // Step 3: Start task
            runButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(mockEel.run_task).toHaveBeenCalledWith(taskDescription);
            expect(runButton.style.display).toBe('none');
            expect(stopButton.style.display).toBe('inline-flex');
            expect(statusDiv.textContent).toContain('Running');
            expect(textarea.disabled).toBe(true);
            
            // Step 4: Task completes
            taskInputPanel.handleTaskCompleted({
                success: true,
                message: 'Task completed successfully'
            });
            
            expect(runButton.style.display).toBe('inline-flex');
            expect(stopButton.style.display).toBe('none');
            expect(statusDiv.textContent).toContain('success');
            expect(textarea.disabled).toBe(false);
            expect(runButton.disabled).toBe(false);
        });
    });
});
