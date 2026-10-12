/**
 * Main Application Entry Point
 * 
 * Initializes the Desktop GUI Application:
 * - Sets up Eel connection
 * - Initializes view routing
 * - Applies theme preferences
 * - Restores window state
 * - Coordinates all components
 */

// Global application object
const app = {
    initialized: false,
    version: '1.0.0'
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
    // Note: Progress Display initializes itself on creation as a singleton,
    // but we verify it's ready here
    if (typeof progressDisplay !== 'undefined') {
        console.log('Progress Display initialized');
    }
    
    // TODO: Initialize other components as they are implemented
    // - History View
}
}

/**
 * Initialize the application
 */
async function initializeApp() {
    console.log('Initializing Desktop GUI Application...');
    
    try {
        // 1. Setup Eel connection
        setupEelConnection();
        
        // 2. Initialize platform detection (must be after Eel setup)
        if (typeof Platform !== 'undefined') {
            await Platform.init();
        }
        
        // 3. Apply theme from state
        applyTheme();
        
        // 4. Setup view routing
        setupViewRouting();
        
        // 5. Setup theme toggle
        setupThemeToggle();
        
        // 6. Setup window state tracking
        setupWindowStateTracking();
        
        // 7. Restore window size/position if available
        restoreWindowState();
        
        // 8. Initialize components
        initializeComponents();
        
        // 9. Check for first run and show setup wizard if needed
        if (typeof window.setupWizard !== 'undefined') {
            try {
                await window.setupWizard.show();
            } catch (error) {
                console.warn('Error showing setup wizard:', error);
            }
        }
        
        // 10. Navigate to initial view
        navigateToView(stateManager.get('currentView'));
        
        // Mark as initialized
        app.initialized = true;
        stateManager.set('eelConnected', true);
        
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
        stateManager.set('eelConnected', false);
        return;
    }
    
    // Configure Eel
    eel.set_host('ws://localhost:8080');
    
    // Test connection by calling a simple backend function
    // This will be handled gracefully if backend is not ready
    if (typeof eel.ping !== 'undefined') {
        eel.ping()().then(response => {
            console.log('Backend connection verified:', response);
            stateManager.set('eelConnected', true);
        }).catch(error => {
            console.warn('Backend not ready yet:', error);
            stateManager.set('eelConnected', false);
        });
    }
}

/**
 * Setup view routing (tab switching)
 */
function setupViewRouting() {
    console.log('Setting up view routing...');
    
    // Get all navigation tabs
    const navTabs = document.querySelectorAll('.nav-tab');
    
    navTabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            const viewName = tab.dataset.view;
            navigateToView(viewName);
        });
    });
    
    // Subscribe to view changes in state
    stateManager.subscribe('currentView', (newView) => {
        updateViewUI(newView);
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
    
    // Update state (this will trigger observers)
    stateManager.set('currentView', viewName, true);
}

/**
 * Update UI to reflect current view
 * @param {string} viewName - The active view name
 */
function updateViewUI(viewName) {
    // Get current active view
    const currentView = document.querySelector('.view-container.active');
    const nextView = document.querySelector(`.view-container[data-view="${viewName}"]`);
    
    if (!nextView) {
        console.warn(`View not found: ${viewName}`);
        return;
    }
    
    // Skip transition if already on this view
    if (currentView === nextView) {
        return;
    }
    
    // Smooth transition: fade out current view
    if (currentView) {
        currentView.classList.add('transitioning-out');
        
        setTimeout(() => {
            // Hide current view
            currentView.classList.remove('active', 'transitioning-out');
            currentView.setAttribute('hidden', '');
            
            // Show next view with fade-in animation
            nextView.removeAttribute('hidden');
            nextView.classList.add('transitioning-in');
            
            // Force reflow to ensure animation plays
            void nextView.offsetWidth;
            
            setTimeout(() => {
                nextView.classList.remove('transitioning-in');
                nextView.classList.add('active');
                nextView.focus();
            }, 10);
        }, 150); // Match CSS transition duration
    } else {
        // No current view, just show next view
        nextView.removeAttribute('hidden');
        nextView.classList.add('active');
        nextView.focus();
    }
    
    // Update navigation tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        const isActive = tab.dataset.view === viewName;
        tab.classList.toggle('active', isActive);
        tab.setAttribute('aria-selected', isActive.toString());
    });
    
    // Announce view change to screen readers
    if (typeof window.accessibility !== 'undefined' && window.accessibility.announceViewChange) {
        window.accessibility.announceViewChange(viewName);
    }
    
    // Dispatch view change event
    window.dispatchEvent(new CustomEvent('view-changed', { 
        detail: { view: viewName } 
    }));
}

/**
 * Apply theme from state
 */
function applyTheme() {
    const theme = stateManager.get('theme');
    console.log(`Applying theme: ${theme}`);
    
    const themeStylesheet = document.getElementById('theme-stylesheet');
    if (themeStylesheet) {
        themeStylesheet.href = `css/themes/${theme}.css`;
    }
    
    // Update body data attribute for CSS
    document.body.dataset.theme = theme;
}

/**
 * Setup theme toggle button
 */
function setupThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            toggleTheme();
        });
    }
    
    // Subscribe to theme changes
    stateManager.subscribe('theme', (newTheme) => {
        applyTheme();
    });
}

/**
 * Toggle between light and dark theme
 */
function toggleTheme() {
    const currentTheme = stateManager.get('theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    console.log(`Toggling theme: ${currentTheme} -> ${newTheme}`);
    stateManager.set('theme', newTheme, true);
}

/**
 * Setup window state tracking
 */
function setupWindowStateTracking() {
    // Track window resize
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            const windowSize = {
                width: window.innerWidth,
                height: window.innerHeight
            };
            stateManager.set('windowSize', windowSize, true);
        }, 500); // Debounce resize events
    });
    
    // Track window close
    window.addEventListener('beforeunload', () => {
        // Persist final state before closing
        const windowSize = {
            width: window.innerWidth,
            height: window.innerHeight
        };
        stateManager.set('windowSize', windowSize, true);
    });
}

/**
 * Restore window size/position from persisted state
 */
function restoreWindowState() {
    const windowSize = stateManager.get('windowSize');
    
    if (windowSize && windowSize.width && windowSize.height) {
        console.log('Restoring window size:', windowSize);
        
        // If running in Eel, try to resize window via backend
        if (typeof eel !== 'undefined' && typeof eel.resize_window !== 'undefined') {
            eel.resize_window(windowSize.width, windowSize.height)()
                .then(() => {
                    console.log('Window size restored');
                })
                .catch(error => {
                    console.warn('Could not resize window:', error);
                });
        }
    }
}

/**
 * Show error message to user
 * @param {string} title - Error title
 * @param {string} message - Error message
 */
function showError(title, message) {
    console.error(`${title}: ${message}`);
    showDialog(title, `<p class="error-message">${escapeHtml(message)}</p>`, 'error');
}

/**
 * Show a generic dialog
 * @param {string} title - Dialog title
 * @param {string} content - Dialog content (HTML)
 * @param {string} type - Dialog type ('info', 'error', 'warning', 'success')
 */
function showDialog(title, content, type = 'info') {
    let dialog = document.getElementById('app-dialog');
    
    // Create dialog if it doesn't exist
    if (!dialog) {
        dialog = document.createElement('div');
        dialog.id = 'app-dialog';
        dialog.className = 'dialog-overlay';
        dialog.innerHTML = `
            <div class="dialog-box" role="dialog" aria-modal="true">
                <div class="dialog-header">
                    <h3 class="dialog-title"></h3>
                    <button class="dialog-close" aria-label="Close dialog">&times;</button>
                </div>
                <div class="dialog-content"></div>
                <div class="dialog-footer">
                    <button class="btn btn-primary dialog-ok">OK</button>
                </div>
            </div>
        `;
        document.body.appendChild(dialog);
        
        // Setup close handlers
        dialog.querySelector('.dialog-close').addEventListener('click', closeDialog);
        dialog.querySelector('.dialog-ok').addEventListener('click', closeDialog);
        dialog.addEventListener('click', (e) => {
            if (e.target === dialog) {
                closeDialog();
            }
        });
    }
    
    // Update dialog content
    dialog.querySelector('.dialog-title').textContent = title;
    dialog.querySelector('.dialog-content').innerHTML = content;
    dialog.dataset.type = type;
    
    // Show dialog
    dialog.removeAttribute('hidden');
    dialog.querySelector('.dialog-ok').focus();
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

/**
 * Keyboard shortcut handler
 * Implements keyboard shortcuts for navigation and common actions
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Don't trigger shortcuts if user is typing in an input field
        const isInputField = ['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName);
        
        // Use platform-aware modifier key check
        const isModifierPressed = (typeof Platform !== 'undefined' && Platform.isModifierPressed) 
            ? Platform.isModifierPressed(e)
            : (e.ctrlKey || e.metaKey);
        
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
            // Check for open dialogs first
            const openDialog = document.querySelector('.dialog-overlay:not([hidden])');
            if (openDialog) {
                e.preventDefault();
                closeDialog();
                return;
            }
            
            // If no dialog, stop running task
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
                case 'h':
                case 'H':
                    e.preventDefault();
                    navigateToView('history');
                    break;
                case ',':
                    e.preventDefault();
                    navigateToView('settings');
                    break;
                case 'c':
                case 'C':
                    // Ctrl+C: Copy output (only if not in input field)
                    const progressView = document.querySelector('[data-view="task"]');
                    if (progressView && !progressView.hasAttribute('hidden')) {
                        const copyButton = document.getElementById('btn-copy-output');
                        if (copyButton) {
                            e.preventDefault();
                            copyButton.click();
                        }
                    }
                    break;
            }
        }
    });
    
    console.log('Keyboard shortcuts initialized');
}

/**
 * Close any open dialog
 */
function closeDialog() {
    const openDialog = document.querySelector('.dialog-overlay:not([hidden])');
    if (openDialog) {
        openDialog.setAttribute('hidden', '');
    }
}

/**
 * Show keyboard shortcuts help
 */
function showKeyboardShortcutsHelp() {
    // Get platform-appropriate modifier key display
    const modKey = (typeof Platform !== 'undefined' && Platform.modifierKey) 
        ? Platform.modifierKey 
        : 'Ctrl/Cmd';
    
    const shortcuts = [
        { keys: `${modKey} + Enter`, action: 'Run task' },
        { keys: `${modKey} + 1`, action: 'Switch to Task view' },
        { keys: `${modKey} + 2`, action: 'Switch to History view' },
        { keys: `${modKey} + 3`, action: 'Switch to Settings view' },
        { keys: `${modKey} + H`, action: 'Open History view' },
        { keys: `${modKey} + ,`, action: 'Open Settings view' },
        { keys: `${modKey} + C`, action: 'Copy output (in Task view)' },
        { keys: 'Esc', action: 'Close dialog or stop task' }
    ];
    
    let content = '<h2>Keyboard Shortcuts</h2><ul class="shortcuts-list">';
    shortcuts.forEach(shortcut => {
        content += `<li><kbd>${shortcut.keys}</kbd> <span>${shortcut.action}</span></li>`;
    });
    content += '</ul>';
    
    showDialog('Keyboard Shortcuts', content);
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initializeApp();
        setupKeyboardShortcuts();
    });
} else {
    // DOM already loaded
    initializeApp();
    setupKeyboardShortcuts();
}

// Export for debugging and testing
if (typeof window !== 'undefined') {
    window.app = app;
    window.navigateToView = navigateToView;
    window.toggleTheme = toggleTheme;
    window.showDialog = showDialog;
    window.showError = showError;
    window.closeDialog = closeDialog;
    window.showKeyboardShortcutsHelp = showKeyboardShortcutsHelp;
}
