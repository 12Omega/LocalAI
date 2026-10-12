/**
 * Help System Module
 * 
 * Provides help menu, about dialog, bug reporting, and tooltips
 */

const helpSystem = {
    initialized: false,
    appVersion: '1.0.0',
    appName: 'Local AI Development Environment'
};

/**
 * Initialize help system
 */
function initHelpSystem() {
    setupHelpMenu();
    setupTooltips();
    helpSystem.initialized = true;
    console.log('Help system initialized');
}

/**
 * Setup help menu
 */
function setupHelpMenu() {
    // Create help button if it doesn't exist
    let helpButton = document.getElementById('help-menu-button');
    
    if (!helpButton) {
        // Add help button to header
        const headerActions = document.querySelector('.header-actions');
        if (headerActions) {
            helpButton = document.createElement('button');
            helpButton.id = 'help-menu-button';
            helpButton.className = 'icon-button';
            helpButton.setAttribute('aria-label', 'Help menu');
            helpButton.setAttribute('title', 'Help');
            helpButton.innerHTML = `
                <svg class="icon" viewBox="0 0 24 24" width="24" height="24">
                    <path d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                </svg>
            `;
            
            // Insert before theme toggle
            const themeToggle = document.getElementById('theme-toggle');
            if (themeToggle) {
                headerActions.insertBefore(helpButton, themeToggle);
            } else {
                headerActions.appendChild(helpButton);
            }
        }
    }
    
    // Add click handler
    if (helpButton) {
        helpButton.addEventListener('click', showHelpMenu);
    }
}

/**
 * Show help menu
 */
function showHelpMenu() {
    const menuContent = `
        <div class="help-menu">
            <button class="help-menu-item" onclick="showKeyboardShortcutsHelp()">
                <svg class="menu-icon" viewBox="0 0 24 24" width="20" height="20">
                    <path d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                </svg>
                <span>Keyboard Shortcuts</span>
            </button>
            <button class="help-menu-item" onclick="showUserGuide()">
                <svg class="menu-icon" viewBox="0 0 24 24" width="20" height="20">
                    <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                </svg>
                <span>User Guide</span>
            </button>
            <button class="help-menu-item" onclick="showDocumentation()">
                <svg class="menu-icon" viewBox="0 0 24 24" width="20" height="20">
                    <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                </svg>
                <span>Documentation</span>
            </button>
            <hr class="menu-divider">
            <button class="help-menu-item" onclick="showBugReportDialog()">
                <svg class="menu-icon" viewBox="0 0 24 24" width="20" height="20">
                    <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                </svg>
                <span>Report a Bug</span>
            </button>
            <button class="help-menu-item" onclick="checkForUpdates()">
                <svg class="menu-icon" viewBox="0 0 24 24" width="20" height="20">
                    <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                </svg>
                <span>Check for Updates</span>
            </button>
            <button class="help-menu-item" onclick="showAboutDialog()">
                <svg class="menu-icon" viewBox="0 0 24 24" width="20" height="20">
                    <path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                </svg>
                <span>About</span>
            </button>
        </div>
    `;
    
    if (typeof showDialog !== 'undefined') {
        showDialog('Help & Support', menuContent, 'info');
    }
}

/**
 * Show user guide
 */
function showUserGuide() {
    const guideContent = `
        <div class="user-guide">
            <h3>Getting Started</h3>
            <p>The Local AI Development Environment helps you leverage AI for software development tasks.</p>
            
            <h4>1. Configure Your LLM</h4>
            <p>Go to the <strong>Settings</strong> tab and configure your LLM endpoint, model name, and parameters.</p>
            
            <h4>2. Describe Your Task</h4>
            <p>In the <strong>Task</strong> tab, describe what you want the AI to do. Be specific and clear.</p>
            
            <h4>3. Run the Task</h4>
            <p>Click <strong>Run Task</strong> or press <kbd>Ctrl+Enter</kbd> to start execution.</p>
            
            <h4>4. Monitor Progress</h4>
            <p>Watch the progress output as the AI works on your task. You can stop it anytime.</p>
            
            <h4>5. Review History</h4>
            <p>Check the <strong>History</strong> tab to review past tasks and results.</p>
            
            <h3>Tips for Best Results</h3>
            <ul>
                <li>Be specific about what you want to accomplish</li>
                <li>Provide context about your project structure</li>
                <li>Break complex tasks into smaller steps</li>
                <li>Review and validate AI-generated code</li>
            </ul>
            
            <h3>Need More Help?</h3>
            <p>Visit the full documentation for detailed guides and examples.</p>
        </div>
    `;
    
    if (typeof showDialog !== 'undefined') {
        closeDialog(); // Close help menu first
        setTimeout(() => showDialog('User Guide', guideContent, 'info'), 100);
    }
}

/**
 * Show documentation links
 */
function showDocumentation() {
    const docContent = `
        <div class="documentation-links">
            <h3>Documentation</h3>
            <p>Access comprehensive documentation and guides:</p>
            
            <div class="doc-link-list">
                <a href="#" class="doc-link" onclick="openExternal('docs/README.md'); return false;">
                    <strong>Overview</strong>
                    <span>Introduction to the Local AI Development Environment</span>
                </a>
                
                <a href="#" class="doc-link" onclick="openExternal('docs/configuration.md'); return false;">
                    <strong>Configuration Guide</strong>
                    <span>How to configure LLM settings and preferences</span>
                </a>
                
                <a href="#" class="doc-link" onclick="openExternal('docs/workflows.md'); return false;">
                    <strong>Workflows</strong>
                    <span>Common workflows and usage patterns</span>
                </a>
                
                <a href="#" class="doc-link" onclick="openExternal('docs/architecture.md'); return false;">
                    <strong>Architecture</strong>
                    <span>System architecture and design</span>
                </a>
                
                <a href="#" class="doc-link" onclick="openExternal('docs/developer_guide.md'); return false;">
                    <strong>Developer Guide</strong>
                    <span>Contributing and extending the application</span>
                </a>
            </div>
        </div>
    `;
    
    if (typeof showDialog !== 'undefined') {
        closeDialog();
        setTimeout(() => showDialog('Documentation', docContent, 'info'), 100);
    }
}

/**
 * Show about dialog
 */
function showAboutDialog() {
    const aboutContent = `
        <div class="about-dialog">
            <div class="about-header">
                <img src="assets/app-icon.png" alt="Application Icon" class="about-icon">
                <h2>${helpSystem.appName}</h2>
                <p class="about-version">Version ${helpSystem.appVersion}</p>
            </div>
            
            <div class="about-description">
                <p>A desktop application for leveraging AI in software development, 
                providing an intelligent coding assistant powered by local or remote LLMs.</p>
            </div>
            
            <div class="about-info">
                <div class="about-info-item">
                    <strong>License:</strong> MIT License
                </div>
                <div class="about-info-item">
                    <strong>Platform:</strong> ${navigator.platform}
                </div>
                <div class="about-info-item">
                    <strong>User Agent:</strong> ${navigator.userAgent.substring(0, 50)}...
                </div>
            </div>
            
            <div class="about-links">
                <button class="btn btn-secondary" onclick="openExternal('https://github.com'); return false;">
                    View on GitHub
                </button>
                <button class="btn btn-secondary" onclick="openExternal('LICENSE'); return false;">
                    View License
                </button>
            </div>
            
            <div class="about-footer">
                <p>&copy; 2024 Local AI Development Environment Contributors</p>
            </div>
        </div>
    `;
    
    if (typeof showDialog !== 'undefined') {
        closeDialog();
        setTimeout(() => showDialog('About', aboutContent, 'info'), 100);
    }
}

/**
 * Show bug report dialog
 */
function showBugReportDialog() {
    const bugReportContent = `
        <div class="bug-report-dialog">
            <p>Help us improve by reporting bugs. Your report will include diagnostic information 
            (errors, system info) but will exclude sensitive data like API keys.</p>
            
            <form id="bug-report-form" onsubmit="submitBugReport(event)">
                <div class="form-group">
                    <label for="bug-title">Bug Title *</label>
                    <input type="text" id="bug-title" class="form-input" 
                           placeholder="Brief description of the issue" required>
                </div>
                
                <div class="form-group">
                    <label for="bug-description">Description *</label>
                    <textarea id="bug-description" class="form-input" rows="6"
                              placeholder="Detailed description of what happened..." required></textarea>
                </div>
                
                <div class="form-group">
                    <label for="bug-steps">Steps to Reproduce</label>
                    <textarea id="bug-steps" class="form-input" rows="4"
                              placeholder="1. Go to...\n2. Click on...\n3. See error..."></textarea>
                </div>
                
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="include-diagnostics" checked>
                        Include diagnostic information (recommended)
                    </label>
                    <small class="form-help">
                        Includes error logs, system info, and app version. Sensitive data is excluded.
                    </small>
                </div>
                
                <div class="bug-report-actions">
                    <button type="button" class="btn btn-secondary" onclick="closeDialog()">Cancel</button>
                    <button type="submit" class="btn btn-primary">Generate Report</button>
                </div>
            </form>
        </div>
    `;
    
    if (typeof showDialog !== 'undefined') {
        closeDialog();
        setTimeout(() => showDialog('Report a Bug', bugReportContent, 'info'), 100);
    }
}

/**
 * Submit bug report
 * @param {Event} event - Form submit event
 */
function submitBugReport(event) {
    event.preventDefault();
    
    const title = document.getElementById('bug-title').value;
    const description = document.getElementById('bug-description').value;
    const steps = document.getElementById('bug-steps').value;
    const includeDiagnostics = document.getElementById('include-diagnostics').checked;
    
    const report = {
        title,
        description,
        steps,
        timestamp: new Date().toISOString(),
        version: helpSystem.appVersion
    };
    
    if (includeDiagnostics) {
        report.diagnostics = collectDiagnosticInfo();
    }
    
    // Create downloadable bug report
    const reportText = formatBugReport(report);
    downloadBugReport(reportText);
    
    // Show success message
    closeDialog();
    setTimeout(() => {
        showDialog(
            'Bug Report Created',
            `<p>Your bug report has been generated and downloaded.</p>
             <p>You can submit it on GitHub or send it to the maintainers.</p>`,
            'success'
        );
    }, 100);
}

/**
 * Collect diagnostic information (excluding sensitive data)
 * @returns {Object} Diagnostic information
 */
function collectDiagnosticInfo() {
    const diagnostics = {
        platform: navigator.platform,
        userAgent: navigator.userAgent,
        language: navigator.language,
        screenResolution: `${window.screen.width}x${window.screen.height}`,
        windowSize: `${window.innerWidth}x${window.innerHeight}`,
        timestamp: new Date().toISOString()
    };
    
    // Add error statistics if available
    if (typeof window.errorHandler !== 'undefined') {
        diagnostics.errorStatistics = window.errorHandler.getErrorStatistics();
    }
    
    // Add recent errors (excluding sensitive context)
    if (typeof window.errorHandler !== 'undefined') {
        const recentErrors = window.errorHandler.getErrorStatistics().recent.map(error => ({
            timestamp: error.timestamp,
            message: error.message,
            category: error.category,
            severity: error.severity
            // Exclude context which may contain sensitive data
        }));
        diagnostics.recentErrors = recentErrors;
    }
    
    return diagnostics;
}

/**
 * Format bug report as text
 * @param {Object} report - Bug report object
 * @returns {string} Formatted report text
 */
function formatBugReport(report) {
    let text = `Bug Report\n`;
    text += `==========\n\n`;
    text += `Title: ${report.title}\n\n`;
    text += `Description:\n${report.description}\n\n`;
    
    if (report.steps) {
        text += `Steps to Reproduce:\n${report.steps}\n\n`;
    }
    
    text += `---\n\n`;
    text += `Generated: ${report.timestamp}\n`;
    text += `Version: ${report.version}\n\n`;
    
    if (report.diagnostics) {
        text += `Diagnostic Information:\n`;
        text += `----------------------\n`;
        text += JSON.stringify(report.diagnostics, null, 2);
    }
    
    return text;
}

/**
 * Download bug report as a file
 * @param {string} content - Report content
 */
function downloadBugReport(content) {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bug-report-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Check for updates
 */
function checkForUpdates() {
    closeDialog();
    
    setTimeout(() => {
        showDialog(
            'Check for Updates',
            `<p>Current version: ${helpSystem.appVersion}</p>
             <p>Update checking is not yet implemented in this version.</p>
             <p>Visit the GitHub repository to check for new releases manually.</p>`,
            'info'
        );
    }, 100);
}

/**
 * Open external link (will be handled by Eel/Python)
 * @param {string} url - URL to open
 */
function openExternal(url) {
    console.log('Opening external URL:', url);
    
    // Try to use Eel if available
    if (typeof eel !== 'undefined' && eel.open_external) {
        eel.open_external(url)();
    } else {
        // Fallback: just log (in Electron/desktop app, this would open system browser)
        console.warn('Cannot open external URL: Eel not available');
    }
}

/**
 * Setup tooltips for elements with data-tooltip attribute
 */
function setupTooltips() {
    // Find all elements with data-tooltip attribute
    document.querySelectorAll('[data-tooltip]').forEach(element => {
        const tooltipText = element.getAttribute('data-tooltip');
        
        if (typeof window.accessibility !== 'undefined' && 
            typeof window.accessibility.createAccessibleTooltip === 'function') {
            // Use accessible tooltip if available
            window.accessibility.createAccessibleTooltip(element, tooltipText);
        } else {
            // Fallback: use title attribute
            element.setAttribute('title', tooltipText);
        }
    });
}

// Initialize help system when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHelpSystem);
} else {
    initHelpSystem();
}

// Export functions
if (typeof window !== 'undefined') {
    window.helpSystem = helpSystem;
    window.showHelpMenu = showHelpMenu;
    window.showUserGuide = showUserGuide;
    window.showDocumentation = showDocumentation;
    window.showAboutDialog = showAboutDialog;
    window.showBugReportDialog = showBugReportDialog;
    window.submitBugReport = submitBugReport;
    window.checkForUpdates = checkForUpdates;
    window.openExternal = openExternal;
}
