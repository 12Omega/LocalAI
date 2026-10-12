/**
 * Centralized State Management
 * 
 * Manages application state with observer pattern for reactive updates.
 * Handles persistence to localStorage for theme, window preferences, and session state.
 */

class StateManager {
    constructor() {
        // Application state
        this.state = {
            // UI State
            currentView: 'task',
            theme: 'light',
            
            // Task State
            isTaskRunning: false,
            currentTaskId: null,
            
            // Window State
            windowSize: {
                width: null,
                height: null
            },
            
            // Configuration State
            config: null,
            configLoaded: false,
            
            // History State
            historyLoaded: false,
            
            // Connection State
            eelConnected: false
        };
        
        // Observers for state changes
        this.observers = {};
        
        // Initialize state from localStorage
        this.loadPersistedState();
    }
    
    /**
     * Load persisted state from localStorage
     */
    loadPersistedState() {
        try {
            // Load theme preference
            const savedTheme = localStorage.getItem('app_theme');
            if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) {
                this.state.theme = savedTheme;
            }
            
            // Load last view
            const savedView = localStorage.getItem('app_last_view');
            if (savedView && ['task', 'history', 'settings'].includes(savedView)) {
                this.state.currentView = savedView;
            }
            
            // Load window size
            const savedWindowSize = localStorage.getItem('app_window_size');
            if (savedWindowSize) {
                try {
                    this.state.windowSize = JSON.parse(savedWindowSize);
                } catch (e) {
                    console.warn('Failed to parse saved window size:', e);
                }
            }
            
            console.log('Persisted state loaded:', {
                theme: this.state.theme,
                currentView: this.state.currentView,
                windowSize: this.state.windowSize
            });
        } catch (error) {
            console.error('Error loading persisted state:', error);
        }
    }
    
    /**
     * Persist state to localStorage
     * @param {string} key - The state key to persist
     */
    persistState(key) {
        try {
            switch (key) {
                case 'theme':
                    localStorage.setItem('app_theme', this.state.theme);
                    break;
                case 'currentView':
                    localStorage.setItem('app_last_view', this.state.currentView);
                    break;
                case 'windowSize':
                    localStorage.setItem('app_window_size', JSON.stringify(this.state.windowSize));
                    break;
            }
        } catch (error) {
            console.error(`Error persisting state for ${key}:`, error);
        }
    }
    
    /**
     * Get current state value
     * @param {string} key - The state key
     * @returns {*} The state value
     */
    get(key) {
        return this.state[key];
    }
    
    /**
     * Set state value and notify observers
     * @param {string} key - The state key
     * @param {*} value - The new value
     * @param {boolean} persist - Whether to persist to localStorage
     */
    set(key, value, persist = false) {
        const oldValue = this.state[key];
        this.state[key] = value;
        
        // Persist if requested
        if (persist) {
            this.persistState(key);
        }
        
        // Notify observers
        this.notify(key, value, oldValue);
    }
    
    /**
     * Update multiple state values at once
     * @param {Object} updates - Object with key-value pairs to update
     * @param {boolean} persist - Whether to persist to localStorage
     */
    setMultiple(updates, persist = false) {
        Object.entries(updates).forEach(([key, value]) => {
            this.set(key, value, persist);
        });
    }
    
    /**
     * Subscribe to state changes
     * @param {string} key - The state key to observe
     * @param {Function} callback - Function to call when state changes
     * @returns {Function} Unsubscribe function
     */
    subscribe(key, callback) {
        if (!this.observers[key]) {
            this.observers[key] = [];
        }
        
        this.observers[key].push(callback);
        
        // Return unsubscribe function
        return () => {
            const index = this.observers[key].indexOf(callback);
            if (index > -1) {
                this.observers[key].splice(index, 1);
            }
        };
    }
    
    /**
     * Notify observers of state change
     * @param {string} key - The state key that changed
     * @param {*} newValue - The new value
     * @param {*} oldValue - The old value
     */
    notify(key, newValue, oldValue) {
        if (this.observers[key]) {
            this.observers[key].forEach(callback => {
                try {
                    callback(newValue, oldValue);
                } catch (error) {
                    console.error(`Error in state observer for ${key}:`, error);
                }
            });
        }
    }
    
    /**
     * Clear all persisted state
     */
    clearPersistedState() {
        try {
            localStorage.removeItem('app_theme');
            localStorage.removeItem('app_last_view');
            localStorage.removeItem('app_window_size');
            console.log('Persisted state cleared');
        } catch (error) {
            console.error('Error clearing persisted state:', error);
        }
    }
    
    /**
     * Get all state for debugging
     * @returns {Object} Complete state object
     */
    getAll() {
        return { ...this.state };
    }
}

// Create singleton instance
const stateManager = new StateManager();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = stateManager;
}
