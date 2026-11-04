/**
 * Main Application Entry Point - VS Code Style
 * 
 * Initializes the Desktop GUI Application with VS Code layout:
 * - Activity bar + sidebar navigation
 * - Resizable panels
 * - View routing
 * - Component initialization
 */

// Global application object
const app = {
    initialized: false,
    version: '1.0.0',
    currentView: 'task'
};

/**
 * Initialize all UI components
 */
function initializeComponents() {
    console.log('Initializing components...');
    
    // Initialize Accessibility utilities
    if (typeof Accessibility !== 'undefined' && Accessibility.init) {
        Accessibility.init();
        console.log('Accessibility utilities initialized');
    }
    
    // Initialize Setup Wizard
    if (typeof window.setupWizard !== 'undefined' && window.setupWizard.init) {
        window.setupWizard.init();
        console.log('Setup Wizard initialized');
    }
    
    // Initialize Task Input Panel
    if (typeof taskInputPanel !== 'undefined' && taskInputPanel.init) {
        taskInputPanel.init();
        console.log('Task Input Panel initialized');
    }
    
    // Initialize Settings Manager
    if (typeof SettingsManager !== 'undefined') {
        app.settingsManager = new SettingsManager();
        console.log('Settings Manager initialized');
    }
    
    // Initialize Progress Display
    if (typeof progressDisplay !== 'undefined') {
        console.log('Progress Display initialized');
    }
}

/**
 * Initialize the application
 */
async function initializeApp() {
    console.log('Initializing Desktop GUI Application with VS Code layout...');
    
    try {
        // 1. Setup Eel connection
        setupEelConnection();
        
        // 2. Initialize platform detection (must be after Eel setup)
        if (typeof Platform !== 'undefined') {
            await Platform.init();
        }
        
        // 3. Setup activity bar navigation
        setupActivityBar();
        
        // 4. Setup resizable sidebar
        setupSidebarResize();
        
        // 5. Setup resizable panels
        setupPanelResizers();
        
        // 6. Setup keyboard shortcuts
        setupKeyboardShortcuts();
        
        // 7. Initialize components
        initializeComponents();
        
        // 8. Check for first run and show setup wizard if needed
        if (typeof window.setupWizard !== 'undefined') {
            try {
                await window.setupWizard.show();
            } catch (error) {
                console.warn('Error showing setup wizard:', error);
            }
        }
        
        // 9. Navigate to initial view
        navigateToView('task');
        
        // Mark as initialized
        app.initialized = true;
        
        console.log('Application initialized successfully');
        
        // Dispatch initialization event
        window.dispatchEvent(new Event('app-initialized'));
        
    } catch (error) {
        console.error('Error initializing application:', error);
        showError('Failed to initialize application', error.message);
    }
}

/**
 * Setup Eel connection and verify backend connectivity
 */
function setupEelConnection() {
    console.log('Setting up Eel connection...');
    
    // Check if eel is available
    if (typeof eel === 'undefined') {
        console.warn('Eel is not available. Running in development mode without backend.');
        updateLLMStatus('Disconnected', false);
        return;
    }
    
    // Configure Eel
    eel.set_host('ws://localhost:8080');
    
    // Test connection
    if (typeof eel.ping !== 'undefined') {
        eel.ping()().then(response => {
            console.log('Backend connection verified:', response);
            updateLLMStatus('Connected', true);
        }).catch(error => {
            console.warn('Backend not ready yet:', error);
            updateLLMStatus('Disconnected', false);
        });
    }
}

/**
 * Setup activity bar navigation
 */
function setupActivityBar() {
    const activityItems = document.querySelectorAll('.activity-item');
    
    activityItems.forEach(item => {
        item.addEventListener('click', () => {
            const view = item.dataset.view;
            navigateToView(view);
        });
    });
}

/**
 * Navigate to a specific view
 * @param {string} viewName - The view to navigate to ('task', 'history', 'settings')
 */
function navigateToView(viewName) {
    if (!['task', 'history', 'settings'].includes(viewName)) {
        console.warn(`Invalid view name: ${viewName}`);
        return;
    }
    
    console.log(`Navigating to view: ${viewName}`);
    app.currentView = viewName;
    
    // Update activity bar
    document.querySelectorAll('.activity-item').forEach(item => {
        const isActive = item.dataset.view === viewName;
        item.classList.toggle('active', isActive);
        item.setAttribute('aria-pressed', isActive.toString());
    });
    
    // Update editor tabs
    document.querySelectorAll('.editor-tab').forEach(tab => {
        const isActive = tab.dataset.view === viewName;
        tab.classList.toggle('active', isActive);
        tab.setAttribute('aria-selected', isActive.toString());
    });
    
    // Update editor panels
    document.querySelectorAll('.editor-panel').forEach(panel => {
        const isActive = panel.dataset.view === viewName;
        if (isActive) {
            panel.classList.add('active');
            panel.removeAttribute('hidden');
        } else {
            panel.classList.remove('active');
            panel.setAttribute('hidden', '');
        }
    });
    
    // Update sidebar title and content
    updateSidebar(viewName);
    
    // Update status bar
    updateTaskStatus('Idle');
    
    // Announce view change to screen readers
    announceToScreenReader(`Switched to ${viewName} view`);
    
    // Dispatch view change event
    window.dispatchEvent(new CustomEvent('view-changed', { 
        detail: { view: viewName } 
    }));
}

/**
 * Update sidebar based on active view
 * @param {string} viewName - Current view name
 */
function updateSidebar(viewName) {
    const sidebarTitle = document.getElementById('sidebar-title');
    const sidebarContent = document.getElementById('sidebar-content');
    
    const sidebarConfig = {
        task: {
            title: 'TASK',
            content: '<div class="sidebar-info"><p>Run AI-powered tasks to generate code, documentation, and more.</p></div>'
        },
        history: {
            title: 'HISTORY',
            content: '<div class="sidebar-info"><p>View and manage your task execution history.</p></div>'
        },
        settings: {
            title: 'SETTINGS',
            content: '<div class="sidebar-info"><p>Configure LLM connection, project settings, and preferences.</p></div>'
        }
    };
    
    const config = sidebarConfig[viewName] || sidebarConfig.task;
    sidebarTitle.textContent = config.title;
    sidebarContent.innerHTML = config.content;
}

/**
 * Setup resizable sidebar
 */
function setupSidebarResize() {
    const splitter = document.getElementById('splitter');
    const sidebar = document.getElementById('sidebar');
    let isResizing = false;
    let startX = 0;
    let startWidth = 0;
    
    // Restore saved width
    const savedWidth = localStorage.getItem('vscode-sidebar-width');
    if (savedWidth) {
        sidebar.style.width = savedWidth + 'px';
    }
    
    splitter.addEventListener('mousedown', (e) => {
        isResizing = true;
        startX = e.clientX;
        startWidth = sidebar.offsetWidth;
        document.body.classList.add('resizing');
        e.preventDefault();
    });
    
    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        
        const delta = e.clientX - startX;
        const newWidth = Math.max(200, Math.min(500, startWidth + delta));
        sidebar.style.width = newWidth + 'px';
    });
    
    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            document.body.classList.remove('resizing');
            // Save width
            localStorage.setItem('vscode-sidebar-width', sidebar.offsetWidth);
        }
    });
}

/**
 * Setup resizable panels (horizontal and vertical splitters)
 */
function setupPanelResizers() {
    // Horizontal splitter for Task view
    const hSplitter = document.getElementById('h-splitter');
    if (hSplitter) {
        setupHorizontalResize(hSplitter);
    }
    
    // Vertical splitter for History view
    const vSplitter = document.getElementById('v-splitter');
    if (vSplitter) {
        setupVerticalResize(vSplitter);
    }
}

/**
 * Setup horizontal resizer
 * @param {HTMLElement} splitter - Splitter element
 */
function setupHorizontalResize(splitter) {
    const taskLayout = splitter.parentElement;
    let isResizing = false;
    let startY = 0;
    
    splitter.addEventListener('mousedown', (e) => {
        isResizing = true;
        startY = e.clientY;
        document.body.classList.add('resizing');
        e.preventDefault();
    });
    
    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        
        const container = taskLayout;
        const containerRect = container.getBoundingClientRect();
        const percentage = ((e.clientY - containerRect.top) / containerRect.height) * 100;
        const clampedPercentage = Math.max(20, Math.min(80, percentage));
        
        container.style.gridTemplateRows = `${clampedPercentage}% 1px 1fr`;
    });
    
    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            document.body.classList.remove('resizing');
        }
    });
}

/**
 * Setup vertical resizer
 * @param {HTMLElement} splitter - Splitter element
 */
function setupVerticalResize(splitter) {
    const historyLayout = splitter.parentElement;
    let isResizing = false;
    let startX = 0;
    
    splitter.addEventListener('mousedown', (e) => {
        isResizing = true;
        startX = e.clientX;
        document.body.classList.add('resizing');
        e.preventDefault();
    });
    
    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        
        const container = historyLayout;
        const containerRect = container.getBoundingClientRect();
        const percentage = ((e.clientX - containerRect.left) / containerRect.width) * 100;
        const clampedPercentage = Math.max(20, Math.min(80, percentage));
        
        container.style.gridTemplateColumns = `${clampedPercentage}% 1px 1fr`;
    });
    
    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            document.body.classList.remove('resizing');
        }
    });
}

/**
 * Update LLM connection status in status bar
 * @param {string} status - Status text
 * @param {boolean} connected - Connection state
 */
function updateLLMStatus(status, connected) {
    const llmStatus = document.getElementById('llm-status');
    if (llmStatus) {
        const icon = llmStatus.querySelector('svg circle');
        if (icon) {
            icon.style.fill = connected ? var(--success, '#89d185') : var(--error, '#f48771');
        }
        const text = llmStatus.querySelector('span:last-child');
        if (text) {
            text.textContent = `LLM: ${status}`;
        }
    }
}

/**
 * Update task status in status bar
 * @param {string} status - Status text
 */
function updateTaskStatus(status) {
    const taskStatus = document.getElementById('task-status');
    if (taskStatus) {
        taskStatus.textContent = `Task: ${status}`;
    }
    
    const statusIndicator = document.getElementById('task-status-indicator');
    if (statusIndicator) {
        statusIndicator.textContent = status;
    }
}

/**
 * Keyboard shortcut handler
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Don't trigger shortcuts if user is typing in an input field
        const isInputField = ['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName);
        
        const isModifierPressed = e.ctrlKey || e.metaKey;
        
        // Ctrl/Cmd + Enter: Run task (works in textarea)
        if (isModifierPressed && e.key === 'Enter' && isInputField) {
            e.preventDefault();
            const runButton = document.getElementById('btn-run');
            if (runButton && !runButton.disabled) {
                runButton.click();
            }
            return;
        }
        
        // Esc: Close dialogs or stop task
        if (e.key === 'Escape') {
            const stopButton = document.getElementById('btn-stop');
            if (stopButton && !stopButton.disabled) {
                e.preventDefault();
                stopButton.click();
            }
            return;
        }
        
        // Don't trigger navigation shortcuts in input fields
        if (isInputField) {
            return;
        }
        
        // Ctrl/Cmd shortcuts
        if (isModifierPressed && !e.shiftKey && !e.altKey) {
            switch (e.key) {
                case '1':
                    e.preventDefault();
                    navigateToView('task');
                    break;
                case '2':
                    e.preventDefault();
                    navigateToView('history');
                    break;
                case '3':
                    e.preventDefault();
                    navigateToView('settings');
                    break;
            }
        }
    });
    
    console.log('Keyboard shortcuts initialized');
}

/**
 * Show error message to user
 * @param {string} title - Error title
 * @param {string} message - Error message
 */
function showError(title, message) {
    console.error(`${title}: ${message}`);
    announceToScreenReader(`Error: ${message}`);
}

/**
 * Announce message to screen readers
 * @param {string} message - Message to announce
 */
function announceToScreenReader(message) {
    const announcements = document.getElementById('sr-announcements');
    if (announcements) {
        announcements.textContent = message;
        // Clear after a delay to allow screen reader to announce
        setTimeout(() => {
            announcements.textContent = '';
        }, 1000);
    }
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initializeApp();
    });
} else {
    // DOM already loaded
    initializeApp();
}

// Export for debugging and testing
if (typeof window !== 'undefined') {
    window.app = app;
    window.navigateToView = navigateToView;
    window.updateLLMStatus = updateLLMStatus;
    window.updateTaskStatus = updateTaskStatus;
    window.showError = showError;
}
