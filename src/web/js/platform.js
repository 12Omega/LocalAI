/**
 * Platform Detection and Platform-Specific UI Conventions
 * 
 * This module detects the current platform (Windows, macOS, Linux) and provides
 * utilities for platform-specific UI adjustments:
 * - Keyboard shortcut modifiers (Cmd on macOS, Ctrl elsewhere)
 * - CSS classes for platform-specific styling
 * - Platform-specific behavior handling
 * 
 * Requirements: 15.5, 15.6, 17.2
 */

/**
 * Platform information object
 */
const Platform = {
    // Platform identifiers
    name: null,           // 'win32', 'darwin', 'linux', etc.
    isMac: false,
    isWindows: false,
    isLinux: false,
    
    // UI convention properties
    modifierKey: 'Ctrl',  // 'Cmd' on Mac, 'Ctrl' elsewhere
    modifierSymbol: '⌃',  // Visual symbol for shortcuts
    
    /**
     * Initialize platform detection
     * Must be called after Eel is ready
     */
    async init() {
        console.log('Initializing platform detection...');
        
        try {
            // Try to get platform from backend via Eel
            if (typeof eel !== 'undefined' && typeof eel.get_platform === 'function') {
                this.name = await eel.get_platform()();
                console.log('Platform detected from backend:', this.name);
            } else {
                // Fallback to browser detection
                this.name = this.detectPlatformFromBrowser();
                console.log('Platform detected from browser:', this.name);
            }
            
            // Set platform flags
            this.isMac = this.name === 'darwin';
            this.isWindows = this.name === 'win32';
            this.isLinux = this.name === 'linux' || this.name.startsWith('linux');
            
            // Set modifier key convention
            if (this.isMac) {
                this.modifierKey = 'Cmd';
                this.modifierSymbol = '⌘';
            } else {
                this.modifierKey = 'Ctrl';
                this.modifierSymbol = '⌃';
            }
            
            // Apply platform-specific CSS
            this.applyPlatformCSS();
            
            // Update UI labels with correct shortcuts
            this.updateShortcutLabels();
            
            console.log('Platform initialization complete:', {
                name: this.name,
                isMac: this.isMac,
                isWindows: this.isWindows,
                isLinux: this.isLinux,
                modifierKey: this.modifierKey
            });
            
        } catch (error) {
            console.error('Error initializing platform detection:', error);
            // Use browser fallback
            this.name = this.detectPlatformFromBrowser();
            this.isMac = this.name === 'darwin';
            this.isWindows = this.name === 'win32';
            this.isLinux = !this.isMac && !this.isWindows;
            this.modifierKey = this.isMac ? 'Cmd' : 'Ctrl';
            this.modifierSymbol = this.isMac ? '⌘' : '⌃';
        }
    },
    
    /**
     * Detect platform from browser user agent (fallback)
     * @returns {string} Platform identifier
     */
    detectPlatformFromBrowser() {
        const platform = navigator.platform.toUpperCase();
        const userAgent = navigator.userAgent.toUpperCase();
        
        if (platform.indexOf('MAC') >= 0 || userAgent.indexOf('MAC') >= 0) {
            return 'darwin';
        } else if (platform.indexOf('WIN') >= 0 || userAgent.indexOf('WIN') >= 0) {
            return 'win32';
        } else if (platform.indexOf('LINUX') >= 0 || userAgent.indexOf('LINUX') >= 0) {
            return 'linux';
        }
        
        // Default to generic unix-like
        return 'linux';
    },
    
    /**
     * Apply platform-specific CSS classes to body
     * Requirements: 17.2
     */
    applyPlatformCSS() {
        const body = document.body;
        
        // Remove any existing platform classes
        body.classList.remove('platform-mac', 'platform-windows', 'platform-linux');
        
        // Add current platform class
        if (this.isMac) {
            body.classList.add('platform-mac');
        } else if (this.isWindows) {
            body.classList.add('platform-windows');
        } else if (this.isLinux) {
            body.classList.add('platform-linux');
        }
        
        console.log('Applied platform CSS class:', body.className);
    },
    
    /**
     * Update all keyboard shortcut hints in the UI
     * Requirements: 17.2
     */
    updateShortcutLabels() {
        // Find all elements with data-shortcut attribute
        const shortcutElements = document.querySelectorAll('[data-shortcut]');
        
        shortcutElements.forEach(element => {
            const shortcut = element.getAttribute('data-shortcut');
            
            // Replace 'Ctrl' with appropriate modifier for platform
            let displayShortcut = shortcut;
            if (this.isMac) {
                displayShortcut = shortcut.replace(/Ctrl/g, '⌘');
            } else {
                displayShortcut = shortcut.replace(/Ctrl/g, 'Ctrl');
            }
            
            // Update element text or title
            if (element.hasAttribute('data-shortcut-target')) {
                const target = element.getAttribute('data-shortcut-target');
                const targetElement = document.querySelector(target);
                if (targetElement) {
                    targetElement.textContent = displayShortcut;
                }
            } else {
                // Update title/tooltip
                const currentTitle = element.getAttribute('title') || '';
                if (currentTitle && currentTitle.includes('Ctrl')) {
                    const newTitle = currentTitle.replace(/Ctrl/g, this.modifierKey);
                    element.setAttribute('title', newTitle);
                }
            }
        });
        
        console.log(`Updated ${shortcutElements.length} shortcut labels`);
    },
    
    /**
     * Check if event matches platform modifier key
     * @param {KeyboardEvent} event - Keyboard event
     * @returns {boolean} True if modifier key is pressed
     */
    isModifierPressed(event) {
        if (this.isMac) {
            return event.metaKey;
        } else {
            return event.ctrlKey;
        }
    },
    
    /**
     * Get the display string for a keyboard shortcut
     * @param {string} keys - Key combination (e.g., 'Ctrl+Enter', 'Ctrl+S')
     * @returns {string} Platform-appropriate display string
     */
    getShortcutDisplay(keys) {
        if (this.isMac) {
            return keys.replace(/Ctrl/g, '⌘');
        }
        return keys;
    },
    
    /**
     * Check if the current platform is Unix-like (macOS or Linux)
     * @returns {boolean}
     */
    isUnixLike() {
        return this.isMac || this.isLinux;
    }
};

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.Platform = Platform;
}

// Make available as module if using module system
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Platform;
}
