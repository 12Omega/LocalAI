/**
 * Theme Management Module
 * Handles light/dark theme switching with localStorage persistence
 */

(function() {
    'use strict';
    
    const THEME_STORAGE_KEY = 'app-theme';
    const THEME_ATTR = 'data-theme';
    const THEME_LIGHT = 'light';
    const THEME_DARK = 'dark';
    
    /**
     * ThemeManager class
     * Manages theme state and provides methods to toggle between light and dark themes
     */
    class ThemeManager {
        constructor() {
            this.currentTheme = this.getStoredTheme() || this.getSystemTheme();
            this.themeToggleButton = null;
            this.themeStylesheet = null;
        }
        
        /**
         * Initialize the theme manager
         * Sets up the initial theme and event listeners
         */
        init() {
            // Apply the theme immediately to prevent flash
            this.applyTheme(this.currentTheme);
            
            // Wait for DOM to be ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.setupEventListeners());
            } else {
                this.setupEventListeners();
            }
            
            // Listen for system theme changes
            this.watchSystemTheme();
        }
        
        /**
         * Set up event listeners for theme toggle button
         */
        setupEventListeners() {
            this.themeToggleButton = document.getElementById('theme-toggle');
            this.themeStylesheet = document.getElementById('theme-stylesheet');
            
            if (this.themeToggleButton) {
                this.themeToggleButton.addEventListener('click', () => this.toggleTheme());
                
                // Update button aria-label
                this.updateToggleButton();
            }
            
            // Keyboard shortcut: Alt+T to toggle theme
            document.addEventListener('keydown', (event) => {
                if (event.altKey && event.key.toLowerCase() === 't') {
                    event.preventDefault();
                    this.toggleTheme();
                }
            });
        }
        
        /**
         * Get the currently stored theme from localStorage
         * @returns {string|null} The stored theme or null if not set
         */
        getStoredTheme() {
            try {
                return localStorage.getItem(THEME_STORAGE_KEY);
            } catch (error) {
                console.warn('Failed to read theme from localStorage:', error);
                return null;
            }
        }
        
        /**
         * Get the system preferred color scheme
         * @returns {string} 'light' or 'dark'
         */
        getSystemTheme() {
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                return THEME_DARK;
            }
            return THEME_LIGHT;
        }
        
        /**
         * Store the theme preference in localStorage
         * @param {string} theme - The theme to store
         */
        storeTheme(theme) {
            try {
                localStorage.setItem(THEME_STORAGE_KEY, theme);
            } catch (error) {
                console.warn('Failed to save theme to localStorage:', error);
            }
        }
        
        /**
         * Apply the specified theme
         * @param {string} theme - The theme to apply ('light' or 'dark')
         */
        applyTheme(theme) {
            // Add transition class for smooth theme change
            document.body.classList.add('theme-transitioning');
            
            // Set the theme attribute on both html and body
            document.documentElement.setAttribute(THEME_ATTR, theme);
            document.body.setAttribute(THEME_ATTR, theme);
            
            // Update the theme stylesheet link
            if (this.themeStylesheet) {
                this.themeStylesheet.href = `css/themes/${theme}.css`;
            }
            
            // Store the preference
            this.storeTheme(theme);
            this.currentTheme = theme;
            
            // Update UI elements
            this.updateToggleButton();
            
            // Remove transition class after animation completes
            setTimeout(() => {
                document.body.classList.remove('theme-transitioning');
            }, 300);
            
            // Dispatch custom event for other components to react
            this.dispatchThemeChangeEvent(theme);
        }
        
        /**
         * Toggle between light and dark themes
         */
        toggleTheme() {
            const newTheme = this.currentTheme === THEME_LIGHT ? THEME_DARK : THEME_LIGHT;
            this.applyTheme(newTheme);
        }
        
        /**
         * Set a specific theme
         * @param {string} theme - The theme to set ('light' or 'dark')
         */
        setTheme(theme) {
            if (theme !== THEME_LIGHT && theme !== THEME_DARK) {
                console.warn(`Invalid theme: ${theme}. Using light theme.`);
                theme = THEME_LIGHT;
            }
            this.applyTheme(theme);
        }
        
        /**
         * Get the current active theme
         * @returns {string} The current theme ('light' or 'dark')
         */
        getTheme() {
            return this.currentTheme;
        }
        
        /**
         * Update the theme toggle button appearance and aria-label
         */
        updateToggleButton() {
            if (!this.themeToggleButton) return;
            
            const isDark = this.currentTheme === THEME_DARK;
            const label = isDark ? 'Switch to light theme' : 'Switch to dark theme';
            
            this.themeToggleButton.setAttribute('aria-label', label);
            this.themeToggleButton.setAttribute('title', label);
            
            // Update icon (if needed - can be done with CSS or JS)
            // Currently using CSS-only icon, so no JS update needed
        }
        
        /**
         * Watch for system theme preference changes
         */
        watchSystemTheme() {
            if (!window.matchMedia) return;
            
            const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
            
            // Modern browsers
            if (darkModeQuery.addEventListener) {
                darkModeQuery.addEventListener('change', (event) => {
                    // Only auto-switch if user hasn't set a preference
                    if (!this.getStoredTheme()) {
                        const newTheme = event.matches ? THEME_DARK : THEME_LIGHT;
                        this.applyTheme(newTheme);
                    }
                });
            }
            // Fallback for older browsers
            else if (darkModeQuery.addListener) {
                darkModeQuery.addListener((event) => {
                    if (!this.getStoredTheme()) {
                        const newTheme = event.matches ? THEME_DARK : THEME_LIGHT;
                        this.applyTheme(newTheme);
                    }
                });
            }
        }
        
        /**
         * Dispatch a custom event when theme changes
         * @param {string} theme - The new theme
         */
        dispatchThemeChangeEvent(theme) {
            const event = new CustomEvent('themechange', {
                detail: { theme },
                bubbles: true,
                cancelable: false
            });
            document.dispatchEvent(event);
        }
        
        /**
         * Reset theme to system preference
         */
        resetToSystemTheme() {
            try {
                localStorage.removeItem(THEME_STORAGE_KEY);
            } catch (error) {
                console.warn('Failed to remove theme from localStorage:', error);
            }
            const systemTheme = this.getSystemTheme();
            this.applyTheme(systemTheme);
        }
    }
    
    // Create and initialize the theme manager
    const themeManager = new ThemeManager();
    themeManager.init();
    
    // Expose theme manager to global scope for other scripts to use
    window.themeManager = themeManager;
    
    // Example usage from console or other scripts:
    // themeManager.setTheme('dark')
    // themeManager.toggleTheme()
    // themeManager.getTheme()
    // themeManager.resetToSystemTheme()
    
    // Listen for theme change events (example for other components)
    // document.addEventListener('themechange', (event) => {
    //     console.log('Theme changed to:', event.detail.theme);
    // });
    
})();
