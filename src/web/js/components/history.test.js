/**
 * Integration Tests for History View Component
 * 
 * Tests history loading, search/filter functionality, entry actions (view, re-run, delete),
 * and export functionality.
 * 
 * Requirements tested: 5.1-5.9
 */

describe('HistoryView - Integration Tests', () => {
    let historyView;
    let mockEel;
    let mockStateManager;
    let mockNavigateToView;
    
    // Mock history data
    const mockHistoryEntries = [
        {
            entry_id: 'entry-1',
            task_description: 'Create a calculator module with unit tests',
            timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
            duration_seconds: 145.5,
            status: 'success',
            output: 'Task completed successfully. Created files: src/calculator.py, tests/test_calculator.py',
            error_message: null
        },
        {
            entry_id: 'entry-2',
            task_description: 'Refactor authentication system to use JWT tokens',
            timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
            duration_seconds: 320.2,
            status: 'success',
            output: 'Refactoring completed. Modified 5 files.',
            error_message: null
        },
        {
            entry_id: 'entry-3',
            task_description: 'Fix bug in user registration validation',
            timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days ago
            duration_seconds: 89.7,
            status: 'failed',
            output: 'Error occurred during execution',
            error_message: 'Validation logic incomplete'
        },
        {
            entry_id: 'entry-4',
            task_description: 'Add REST API endpoint for user registration',
            timestamp: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days ago
            duration_seconds: 180.0,
            status: 'success',
            output: 'API endpoint created successfully',
            error_message: null
        }
    ];
    
    // Helper to set up DOM
    const setupDOM = () => {
        document.body.innerHTML = `
            <div id="history-view">
                <div class="history-controls">
                    <input type="text" id="history-search" placeholder="Search tasks..." />
                    <select id="status-filter">
                        <option value="all">All</option>
                        <option value="success">Success</option>
                        <option value="failed">Failed</option>
                        <option value="cancelled">Cancelled</option>
                    </select>
                    <select id="sort-order">
                        <option value="newest">Newest First</option>
                        <option value="oldest">Oldest First</option>
                    </select>
                    <button id="export-history-btn">Export</button>
                    <button id="clear-history-btn">Clear All</button>
                </div>
                <div id="history-entries"></div>
                <div id="history-detail-panel" style="display: none;">
                    <button id="close-detail-btn">Close</button>
                    <div id="history-detail-content"></div>
                </div>
            </div>
        `;
    };
    
    // Helper to create mock Eel
    const createMockEel = () => {
        return {
            get_history: jest.fn(() => () => Promise.resolve(mockHistoryEntries)),
            get_history_entry: jest.fn((id) => () => {
                const entry = mockHistoryEntries.find(e => e.entry_id === id);
                return Promise.resolve(entry);
            }),
            delete_history_entry: jest.fn(() => () => Promise.resolve({ 
                success: true, 
                message: 'Entry deleted' 
            })),
            clear_all_history: jest.fn(() => () => Promise.resolve({ 
                success: true, 
                message: 'All history cleared' 
            })),
            export_history: jest.fn((format, filename) => () => Promise.resolve({ 
                success: true, 
                filepath: `/home/user/${filename}` 
            }))
        };
    };
    
    // Helper to create mock StateManager
    const createMockStateManager = () => {
        return {
            set: jest.fn(),
            get: jest.fn((key) => {
                if (key === 'eelConnected') return true;
                if (key === 'currentView') return 'history';
                return null;
            }),
            subscribe: jest.fn()
        };
    };
    
    beforeEach(async () => {
        setupDOM();
        mockEel = createMockEel();
        mockStateManager = createMockStateManager();
        mockNavigateToView = jest.fn();
        
        global.eel = mockEel;
        global.stateManager = mockStateManager;
        global.navigateToView = mockNavigateToView;
        global.confirm = jest.fn(() => true);
        global.prompt = jest.fn();
        
        historyView = new HistoryView();
        await historyView.init();
    });
    
    afterEach(() => {
        document.body.innerHTML = '';
        delete global.eel;
        delete global.stateManager;
        delete global.navigateToView;
        jest.clearAllMocks();
    });
    
    /**
     * Requirement 5.1: Display list of executed tasks with timestamps
     */
    describe('History Display', () => {
        test('should load history from backend on init', () => {
            expect(mockEel.get_history).toHaveBeenCalled();
        });
        
        test('should display list of history entries', async () => {
            const entriesContainer = document.getElementById('history-entries');
            const entries = entriesContainer.querySelectorAll('.history-entry');
            
            expect(entries.length).toBe(4);
        });
        
        test('should display task description for each entry', () => {
            const firstEntry = document.querySelector('.history-entry');
            
            expect(firstEntry.textContent).toContain('Create a calculator module');
        });
        
        test('should display timestamp for each entry', () => {
            const entries = document.querySelectorAll('.history-entry');
            
            entries.forEach(entry => {
                const timestamp = entry.querySelector('.entry-time');
                expect(timestamp).toBeTruthy();
            });
        });
    });
    
    /**
     * Requirement 5.2: Show task description, execution time, and status
     */
    describe('Entry Information Display', () => {
        test('should show execution duration for each entry', () => {
            const entries = document.querySelectorAll('.history-entry');
            
            const firstEntry = entries[0];
            expect(firstEntry.textContent).toContain('2m 26s'); // 145.5 seconds
        });
        
        test('should show status icon for each entry', () => {
            const entries = document.querySelectorAll('.history-entry');
            
            const successEntry = entries[0];
            expect(successEntry.classList.contains('status-success')).toBe(true);
            
            const failedEntry = entries[2];
            expect(failedEntry.classList.contains('status-failed')).toBe(true);
        });
        
        test('should display correct status indicator', () => {
            const entries = document.querySelectorAll('.history-entry');
            
            // Success entry should have checkmark
            const successStatus = entries[0].querySelector('.entry-status');
            expect(successStatus.textContent).toContain('✓');
            
            // Failed entry should have X
            const failedStatus = entries[2].querySelector('.entry-status');
            expect(failedStatus.textContent).toContain('✗');
        });
    });
    
    /**
     * Requirement 5.3: Store at least 100 most recent tasks
     */
    describe('History Storage', () => {
        test('should request up to 100 entries from backend', () => {
            expect(mockEel.get_history).toHaveBeenCalledWith(100, null);
        });
    });
    
    /**
     * Requirement 5.4: Display full task description and output when clicked
     */
    describe('Entry Details View', () => {
        test('should show detail panel when entry is clicked', async () => {
            const firstEntry = document.querySelector('.history-entry');
            const detailPanel = document.getElementById('history-detail-panel');
            
            firstEntry.click();
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(detailPanel.style.display).toBe('block');
        });
        
        test('should display full task description in detail view', async () => {
            const firstEntry = document.querySelector('.history-entry');
            const detailContent = document.getElementById('history-detail-content');
            
            firstEntry.click();
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(detailContent.textContent).toContain('Create a calculator module with unit tests');
        });
        
        test('should display output in detail view', async () => {
            const firstEntry = document.querySelector('.history-entry');
            const detailContent = document.getElementById('history-detail-content');
            
            firstEntry.click();
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(detailContent.textContent).toContain('Task completed successfully');
        });
        
        test('should show error message for failed tasks', async () => {
            const entries = document.querySelectorAll('.history-entry');
            const failedEntry = entries[2]; // Third entry is failed
            
            failedEntry.click();
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            const detailContent = document.getElementById('history-detail-content');
            expect(detailContent.textContent).toContain('Validation logic incomplete');
        });
        
        test('should highlight selected entry', async () => {
            const firstEntry = document.querySelector('.history-entry');
            
            firstEntry.click();
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(firstEntry.classList.contains('selected')).toBe(true);
        });
        
        test('should close detail panel when close button clicked', async () => {
            const firstEntry = document.querySelector('.history-entry');
            const detailPanel = document.getElementById('history-detail-panel');
            const closeButton = document.getElementById('close-detail-btn');
            
            firstEntry.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            closeButton.click();
            
            expect(detailPanel.style.display).toBe('none');
        });
    });
    
    /**
     * Requirement 5.5: Provide re-run button to execute same task again
     */
    describe('Re-run Task Functionality', () => {
        test('should provide re-run button for each entry', () => {
            const entries = document.querySelectorAll('.history-entry');
            
            entries.forEach(entry => {
                const rerunButton = entry.querySelector('[data-action="rerun"]');
                expect(rerunButton).toBeTruthy();
            });
        });
        
        test('should navigate to task view and populate input when re-run clicked', async () => {
            const firstEntry = document.querySelector('.history-entry');
            const rerunButton = firstEntry.querySelector('[data-action="rerun"]');
            
            const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
            
            await rerunButton.click();
            await new Promise(resolve => setTimeout(resolve, 200));
            
            expect(confirmSpy).toHaveBeenCalled();
            expect(mockNavigateToView).toHaveBeenCalledWith('task');
            
            confirmSpy.mockRestore();
        });
        
        test('should populate task description when re-running', async () => {
            const firstEntry = document.querySelector('.history-entry');
            const rerunButton = firstEntry.querySelector('[data-action="rerun"]');
            
            // Add task description input to DOM
            const taskInput = document.createElement('textarea');
            taskInput.id = 'task-description';
            document.body.appendChild(taskInput);
            
            const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
            
            await rerunButton.click();
            await new Promise(resolve => setTimeout(resolve, 200));
            
            expect(taskInput.value).toBe('Create a calculator module with unit tests');
            
            confirmSpy.mockRestore();
        });
    });
    
    /**
     * Requirement 5.6: Provide delete button to remove individual entries
     */
    describe('Delete Entry Functionality', () => {
        test('should provide delete button for each entry', () => {
            const entries = document.querySelectorAll('.history-entry');
            
            entries.forEach(entry => {
                const deleteButton = entry.querySelector('[data-action="delete"]');
                expect(deleteButton).toBeTruthy();
            });
        });
        
        test('should call backend to delete entry when button clicked', async () => {
            const firstEntry = document.querySelector('.history-entry');
            const deleteButton = firstEntry.querySelector('[data-action="delete"]');
            
            const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
            
            await deleteButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(confirmSpy).toHaveBeenCalled();
            expect(mockEel.delete_history_entry).toHaveBeenCalledWith('entry-1');
            
            confirmSpy.mockRestore();
        });
        
        test('should remove entry from display after deletion', async () => {
            const entriesContainer = document.getElementById('history-entries');
            const initialCount = entriesContainer.querySelectorAll('.history-entry').length;
            
            const firstEntry = document.querySelector('.history-entry');
            const deleteButton = firstEntry.querySelector('[data-action="delete"]');
            
            const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
            
            await deleteButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            const newCount = entriesContainer.querySelectorAll('.history-entry').length;
            expect(newCount).toBe(initialCount - 1);
            
            confirmSpy.mockRestore();
        });
        
        test('should not delete if user cancels confirmation', async () => {
            const firstEntry = document.querySelector('.history-entry');
            const deleteButton = firstEntry.querySelector('[data-action="delete"]');
            
            const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(false);
            
            await deleteButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(mockEel.delete_history_entry).not.toHaveBeenCalled();
            
            confirmSpy.mockRestore();
        });
    });
    
    /**
     * Requirement 5.7: Provide clear-all button to remove all entries
     */
    describe('Clear All History Functionality', () => {
        test('should provide clear all button', () => {
            const clearAllButton = document.getElementById('clear-history-btn');
            expect(clearAllButton).toBeTruthy();
        });
        
        test('should call backend to clear all history', async () => {
            const clearAllButton = document.getElementById('clear-history-btn');
            
            const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
            
            await clearAllButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(confirmSpy).toHaveBeenCalled();
            expect(mockEel.clear_all_history).toHaveBeenCalled();
            
            confirmSpy.mockRestore();
        });
        
        test('should show empty state after clearing all', async () => {
            const clearAllButton = document.getElementById('clear-history-btn');
            const entriesContainer = document.getElementById('history-entries');
            
            const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
            
            await clearAllButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(entriesContainer.querySelector('.empty-state')).toBeTruthy();
            
            confirmSpy.mockRestore();
        });
    });
    
    /**
     * Requirement 5.8: Provide search box to filter history by task description
     */
    describe('Search Functionality', () => {
        test('should provide search input', () => {
            const searchInput = document.getElementById('history-search');
            expect(searchInput).toBeTruthy();
        });
        
        test('should filter entries based on search query', async () => {
            const searchInput = document.getElementById('history-search');
            const entriesContainer = document.getElementById('history-entries');
            
            // Search for "calculator"
            searchInput.value = 'calculator';
            searchInput.dispatchEvent(new Event('input'));
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            const visibleEntries = entriesContainer.querySelectorAll('.history-entry');
            expect(visibleEntries.length).toBe(1);
            expect(visibleEntries[0].textContent).toContain('calculator');
        });
        
        test('should show all entries when search is cleared', async () => {
            const searchInput = document.getElementById('history-search');
            const entriesContainer = document.getElementById('history-entries');
            
            // Search and then clear
            searchInput.value = 'calculator';
            searchInput.dispatchEvent(new Event('input'));
            await new Promise(resolve => setTimeout(resolve, 0));
            
            searchInput.value = '';
            searchInput.dispatchEvent(new Event('input'));
            await new Promise(resolve => setTimeout(resolve, 0));
            
            const entries = entriesContainer.querySelectorAll('.history-entry');
            expect(entries.length).toBe(4);
        });
        
        test('should show empty state when no matches', async () => {
            const searchInput = document.getElementById('history-search');
            const entriesContainer = document.getElementById('history-entries');
            
            searchInput.value = 'nonexistent-task-xyz';
            searchInput.dispatchEvent(new Event('input'));
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(entriesContainer.querySelector('.empty-state')).toBeTruthy();
        });
        
        test('should perform case-insensitive search', async () => {
            const searchInput = document.getElementById('history-search');
            const entriesContainer = document.getElementById('history-entries');
            
            searchInput.value = 'CALCULATOR'; // Uppercase
            searchInput.dispatchEvent(new Event('input'));
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            const entries = entriesContainer.querySelectorAll('.history-entry');
            expect(entries.length).toBe(1);
        });
    });
    
    /**
     * Additional: Status filter functionality
     */
    describe('Status Filter Functionality', () => {
        test('should provide status filter dropdown', () => {
            const statusFilter = document.getElementById('status-filter');
            expect(statusFilter).toBeTruthy();
        });
        
        test('should filter entries by success status', async () => {
            const statusFilter = document.getElementById('status-filter');
            const entriesContainer = document.getElementById('history-entries');
            
            statusFilter.value = 'success';
            statusFilter.dispatchEvent(new Event('change'));
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            const entries = entriesContainer.querySelectorAll('.history-entry');
            expect(entries.length).toBe(3); // 3 successful entries
        });
        
        test('should filter entries by failed status', async () => {
            const statusFilter = document.getElementById('status-filter');
            const entriesContainer = document.getElementById('history-entries');
            
            statusFilter.value = 'failed';
            statusFilter.dispatchEvent(new Event('change'));
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            const entries = entriesContainer.querySelectorAll('.history-entry');
            expect(entries.length).toBe(1); // 1 failed entry
        });
        
        test('should combine search and status filters', async () => {
            const searchInput = document.getElementById('history-search');
            const statusFilter = document.getElementById('status-filter');
            const entriesContainer = document.getElementById('history-entries');
            
            searchInput.value = 'user';
            statusFilter.value = 'success';
            
            searchInput.dispatchEvent(new Event('input'));
            statusFilter.dispatchEvent(new Event('change'));
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            const entries = entriesContainer.querySelectorAll('.history-entry');
            expect(entries.length).toBe(1); // Only successful entries with "user"
        });
    });
    
    /**
     * Additional: Sort order functionality
     */
    describe('Sort Order Functionality', () => {
        test('should provide sort order dropdown', () => {
            const sortOrder = document.getElementById('sort-order');
            expect(sortOrder).toBeTruthy();
        });
        
        test('should sort by newest first by default', () => {
            const entries = document.querySelectorAll('.history-entry');
            
            // First entry should be most recent (2 hours ago)
            expect(entries[0].textContent).toContain('calculator');
        });
        
        test('should sort by oldest first when selected', async () => {
            const sortOrder = document.getElementById('sort-order');
            const entriesContainer = document.getElementById('history-entries');
            
            sortOrder.value = 'oldest';
            sortOrder.dispatchEvent(new Event('change'));
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            const entries = entriesContainer.querySelectorAll('.history-entry');
            
            // First entry should be oldest (7 days ago)
            expect(entries[0].textContent).toContain('REST API endpoint');
        });
    });
    
    /**
     * Requirement 5.9: Provide export button to save history to JSON or CSV
     */
    describe('Export Functionality', () => {
        test('should provide export button', () => {
            const exportButton = document.getElementById('export-history-btn');
            expect(exportButton).toBeTruthy();
        });
        
        test('should show format selection when export button clicked', async () => {
            const exportButton = document.getElementById('export-history-btn');
            
            const promptSpy = jest.spyOn(window, 'prompt')
                .mockReturnValueOnce('1') // Format selection
                .mockReturnValueOnce('history.json'); // Filename
            
            await exportButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(promptSpy).toHaveBeenCalled();
            
            promptSpy.mockRestore();
        });
        
        test('should call backend with correct format and filename', async () => {
            const exportButton = document.getElementById('export-history-btn');
            
            const promptSpy = jest.spyOn(window, 'prompt')
                .mockReturnValueOnce('1') // JSON format
                .mockReturnValueOnce('history.json');
            
            await exportButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(mockEel.export_history).toHaveBeenCalledWith('json', 'history.json');
            
            promptSpy.mockRestore();
        });
        
        test('should export as CSV when format 2 selected', async () => {
            const exportButton = document.getElementById('export-history-btn');
            
            const promptSpy = jest.spyOn(window, 'prompt')
                .mockReturnValueOnce('2') // CSV format
                .mockReturnValueOnce('history.csv');
            
            await exportButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(mockEel.export_history).toHaveBeenCalledWith('csv', 'history.csv');
            
            promptSpy.mockRestore();
        });
    });
    
    /**
     * Integration: Auto-refresh on task completion
     */
    describe('Auto-refresh Functionality', () => {
        test('should listen for task completion events', () => {
            const loadHistorySpy = jest.spyOn(historyView, 'loadHistory');
            
            // Simulate task completion
            window.dispatchEvent(new CustomEvent('task-completed', {
                detail: { task_id: 'new-task' }
            }));
            
            expect(loadHistorySpy).toHaveBeenCalled();
        });
    });
    
    /**
     * Complete workflow test
     */
    describe('Complete Workflow', () => {
        test('should handle complete history management workflow', async () => {
            const entriesContainer = document.getElementById('history-entries');
            const searchInput = document.getElementById('history-search');
            const statusFilter = document.getElementById('status-filter');
            
            // Step 1: Initial load shows all entries
            expect(entriesContainer.querySelectorAll('.history-entry').length).toBe(4);
            
            // Step 2: Search filters entries
            searchInput.value = 'authentication';
            searchInput.dispatchEvent(new Event('input'));
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(entriesContainer.querySelectorAll('.history-entry').length).toBe(1);
            
            // Step 3: Clear search, apply status filter
            searchInput.value = '';
            searchInput.dispatchEvent(new Event('input'));
            statusFilter.value = 'success';
            statusFilter.dispatchEvent(new Event('change'));
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(entriesContainer.querySelectorAll('.history-entry').length).toBe(3);
            
            // Step 4: View entry details
            const firstEntry = entriesContainer.querySelector('.history-entry');
            firstEntry.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            const detailPanel = document.getElementById('history-detail-panel');
            expect(detailPanel.style.display).toBe('block');
            
            // Step 5: Delete an entry
            const deleteButton = firstEntry.querySelector('[data-action="delete"]');
            const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
            
            await deleteButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(mockEel.delete_history_entry).toHaveBeenCalled();
            
            confirmSpy.mockRestore();
        });
    });
});
