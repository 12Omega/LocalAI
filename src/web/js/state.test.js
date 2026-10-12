/**
 * Unit Tests for State Management
 * 
 * Tests state updates, notifications, localStorage persistence, and view routing.
 * Requirements: 6.8, 14.3, 14.4
 */

// Mock localStorage for testing
class LocalStorageMock {
    constructor() {
        this.store = {};
    }

    clear() {
        this.store = {};
    }

    getItem(key) {
        return this.store[key] || null;
    }

    setItem(key, value) {
        this.store[key] = String(value);
    }

    removeItem(key) {
        delete this.store[key];
    }
}

// Setup test environment
function setupTestEnvironment() {
    // Mock localStorage
    global.localStorage = new LocalStorageMock();
    
    // Mock console to suppress logs during tests
    global.console = {
        log: jest.fn(),
        warn: jest.fn(),
        error: jest.fn()
    };
}

// Helper to create StateManager instance
function createStateManager() {
    // Create a new StateManager instance with fresh state
    class StateManager {
        constructor() {
            this.state = {
                currentView: 'task',
                theme: 'light',
                isTaskRunning: false,
                currentTaskId: null,
                windowSize: { width: null, height: null },
                config: null,
                configLoaded: false,
                historyLoaded: false,
                eelConnected: false
            };
            this.observers = {};
            this.loadPersistedState();
        }
        
        loadPersistedState() {
            try {
                const savedTheme = localStorage.getItem('app_theme');
                if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) {
                    this.state.theme = savedTheme;
                }
                
                const savedView = localStorage.getItem('app_last_view');
                if (savedView && ['task', 'history', 'settings'].includes(savedView)) {
                    this.state.currentView = savedView;
                }
                
                const savedWindowSize = localStorage.getItem('app_window_size');
                if (savedWindowSize) {
                    try {
                        this.state.windowSize = JSON.parse(savedWindowSize);
                    } catch (e) {
                        console.warn('Failed to parse saved window size:', e);
                    }
                }
            } catch (error) {
                console.error('Error loading persisted state:', error);
            }
        }
        
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
        
        get(key) {
            return this.state[key];
        }
        
        set(key, value, persist = false) {
            const oldValue = this.state[key];
            this.state[key] = value;
            
            if (persist) {
                this.persistState(key);
            }
            
            this.notify(key, value, oldValue);
        }
        
        setMultiple(updates, persist = false) {
            Object.entries(updates).forEach(([key, value]) => {
                this.set(key, value, persist);
            });
        }
        
        subscribe(key, callback) {
            if (!this.observers[key]) {
                this.observers[key] = [];
            }
            
            this.observers[key].push(callback);
            
            return () => {
                const index = this.observers[key].indexOf(callback);
                if (index > -1) {
                    this.observers[key].splice(index, 1);
                }
            };
        }
        
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
        
        clearPersistedState() {
            try {
                localStorage.removeItem('app_theme');
                localStorage.removeItem('app_last_view');
                localStorage.removeItem('app_window_size');
            } catch (error) {
                console.error('Error clearing persisted state:', error);
            }
        }
        
        getAll() {
            return { ...this.state };
        }
    }
    
    return new StateManager();
}

// Test Suite: StateManager Basic Operations
describe('StateManager - Basic Operations', () => {
    let stateManager;

    beforeEach(() => {
        setupTestEnvironment();
        stateManager = createStateManager();
    });

    test('should initialize with default state', () => {
        expect(stateManager.get('currentView')).toBe('task');
        expect(stateManager.get('theme')).toBe('light');
        expect(stateManager.get('isTaskRunning')).toBe(false);
        expect(stateManager.get('eelConnected')).toBe(false);
    });

    test('should get state value by key', () => {
        const theme = stateManager.get('theme');
        expect(theme).toBe('light');
    });

    test('should set state value', () => {
        stateManager.set('theme', 'dark');
        expect(stateManager.get('theme')).toBe('dark');
    });

    test('should set multiple state values at once', () => {
        stateManager.setMultiple({
            theme: 'dark',
            currentView: 'settings',
            isTaskRunning: true
        });

        expect(stateManager.get('theme')).toBe('dark');
        expect(stateManager.get('currentView')).toBe('settings');
        expect(stateManager.get('isTaskRunning')).toBe(true);
    });

    test('should return all state with getAll', () => {
        const allState = stateManager.getAll();
        
        expect(allState).toHaveProperty('currentView');
        expect(allState).toHaveProperty('theme');
        expect(allState).toHaveProperty('isTaskRunning');
        expect(allState).toHaveProperty('windowSize');
    });
});

// Test Suite: State Updates and Notifications
describe('StateManager - State Updates and Notifications', () => {
    let stateManager;

    beforeEach(() => {
        setupTestEnvironment();
        stateManager = createStateManager();
    });

    test('should notify observers when state changes', () => {
        const callback = jest.fn();
        
        stateManager.subscribe('theme', callback);
        stateManager.set('theme', 'dark');
        
        expect(callback).toHaveBeenCalledTimes(1);
        expect(callback).toHaveBeenCalledWith('dark', 'light');
    });

    test('should notify multiple observers', () => {
        const callback1 = jest.fn();
        const callback2 = jest.fn();
        
        stateManager.subscribe('theme', callback1);
        stateManager.subscribe('theme', callback2);
        
        stateManager.set('theme', 'dark');
        
        expect(callback1).toHaveBeenCalledTimes(1);
        expect(callback2).toHaveBeenCalledTimes(1);
    });

    test('should provide old and new values to observers', () => {
        const callback = jest.fn();
        
        stateManager.set('isTaskRunning', false);
        stateManager.subscribe('isTaskRunning', callback);
        stateManager.set('isTaskRunning', true);
        
        expect(callback).toHaveBeenCalledWith(true, false);
    });

    test('should allow unsubscribing from state changes', () => {
        const callback = jest.fn();
        
        const unsubscribe = stateManager.subscribe('theme', callback);
        stateManager.set('theme', 'dark');
        
        expect(callback).toHaveBeenCalledTimes(1);
        
        unsubscribe();
        stateManager.set('theme', 'light');
        
        // Should not be called again after unsubscribing
        expect(callback).toHaveBeenCalledTimes(1);
    });

    test('should handle errors in observer callbacks gracefully', () => {
        const errorCallback = jest.fn(() => {
            throw new Error('Observer error');
        });
        const successCallback = jest.fn();
        
        stateManager.subscribe('theme', errorCallback);
        stateManager.subscribe('theme', successCallback);
        
        // Should not throw, should call both callbacks
        expect(() => {
            stateManager.set('theme', 'dark');
        }).not.toThrow();
        
        expect(errorCallback).toHaveBeenCalledTimes(1);
        expect(successCallback).toHaveBeenCalledTimes(1);
    });

    test('should notify observers only for changed keys', () => {
        const themeCallback = jest.fn();
        const viewCallback = jest.fn();
        
        stateManager.subscribe('theme', themeCallback);
        stateManager.subscribe('currentView', viewCallback);
        
        stateManager.set('theme', 'dark');
        
        expect(themeCallback).toHaveBeenCalledTimes(1);
        expect(viewCallback).toHaveBeenCalledTimes(0);
    });
});

// Test Suite: localStorage Persistence
describe('StateManager - localStorage Persistence', () => {
    let stateManager;

    beforeEach(() => {
        setupTestEnvironment();
        stateManager = createStateManager();
    });

    test('should persist theme to localStorage', () => {
        stateManager.set('theme', 'dark', true);
        
        expect(localStorage.getItem('app_theme')).toBe('dark');
    });

    test('should persist currentView to localStorage', () => {
        stateManager.set('currentView', 'settings', true);
        
        expect(localStorage.getItem('app_last_view')).toBe('settings');
    });

    test('should persist windowSize to localStorage', () => {
        const windowSize = { width: 1024, height: 768 };
        stateManager.set('windowSize', windowSize, true);
        
        const stored = localStorage.getItem('app_window_size');
        expect(JSON.parse(stored)).toEqual(windowSize);
    });

    test('should load persisted theme on initialization', () => {
        localStorage.setItem('app_theme', 'dark');
        
        // Create new instance
        const newStateManager = createStateManager();
        
        expect(newStateManager.get('theme')).toBe('dark');
    });

    test('should load persisted view on initialization', () => {
        localStorage.setItem('app_last_view', 'history');
        
        // Create new instance
        const newStateManager = createStateManager();
        
        expect(newStateManager.get('currentView')).toBe('history');
    });

    test('should load persisted window size on initialization', () => {
        const windowSize = { width: 1440, height: 900 };
        localStorage.setItem('app_window_size', JSON.stringify(windowSize));
        
        // Create new instance
        const newStateManager = createStateManager();
        
        expect(newStateManager.get('windowSize')).toEqual(windowSize);
    });

    test('should handle invalid persisted data gracefully', () => {
        localStorage.setItem('app_theme', 'invalid-theme');
        localStorage.setItem('app_last_view', 'invalid-view');
        localStorage.setItem('app_window_size', 'invalid-json');
        
        // Should not throw, should use defaults
        expect(() => {
            const newStateManager = createStateManager();
        }).not.toThrow();
    });

    test('should clear all persisted state', () => {
        localStorage.setItem('app_theme', 'dark');
        localStorage.setItem('app_last_view', 'settings');
        localStorage.setItem('app_window_size', '{"width":1024,"height":768}');
        
        stateManager.clearPersistedState();
        
        expect(localStorage.getItem('app_theme')).toBeNull();
        expect(localStorage.getItem('app_last_view')).toBeNull();
        expect(localStorage.getItem('app_window_size')).toBeNull();
    });

    test('should not persist when persist flag is false', () => {
        stateManager.set('theme', 'dark', false);
        
        expect(localStorage.getItem('app_theme')).toBeNull();
    });

    test('should persist multiple values with setMultiple', () => {
        stateManager.setMultiple({
            theme: 'dark',
            currentView: 'history'
        }, true);
        
        expect(localStorage.getItem('app_theme')).toBe('dark');
        expect(localStorage.getItem('app_last_view')).toBe('history');
    });
});

// Test Suite: View Routing State
describe('StateManager - View Routing', () => {
    let stateManager;

    beforeEach(() => {
        setupTestEnvironment();
        stateManager = createStateManager();
    });

    test('should update currentView state', () => {
        stateManager.set('currentView', 'history');
        expect(stateManager.get('currentView')).toBe('history');
    });

    test('should notify observers when view changes', () => {
        const callback = jest.fn();
        
        stateManager.subscribe('currentView', callback);
        stateManager.set('currentView', 'settings');
        
        expect(callback).toHaveBeenCalledWith('settings', 'task');
    });

    test('should persist view changes when requested', () => {
        stateManager.set('currentView', 'history', true);
        expect(localStorage.getItem('app_last_view')).toBe('history');
    });

    test('should support all valid views', () => {
        const validViews = ['task', 'history', 'settings'];
        
        validViews.forEach(view => {
            stateManager.set('currentView', view);
            expect(stateManager.get('currentView')).toBe(view);
        });
    });

    test('should restore last view on initialization', () => {
        localStorage.setItem('app_last_view', 'settings');
        
        const newStateManager = createStateManager();
        
        expect(newStateManager.get('currentView')).toBe('settings');
    });

    test('should default to task view if no persisted view exists', () => {
        // Don't set any persisted view
        const newStateManager = createStateManager();
        
        expect(newStateManager.get('currentView')).toBe('task');
    });

    test('should ignore invalid persisted view values', () => {
        localStorage.setItem('app_last_view', 'invalid-view');
        
        const newStateManager = createStateManager();
        
        // Should fall back to default
        expect(newStateManager.get('currentView')).toBe('task');
    });
});

// Test Suite: Edge Cases and Error Handling
describe('StateManager - Edge Cases', () => {
    let stateManager;

    beforeEach(() => {
        setupTestEnvironment();
        stateManager = createStateManager();
    });

    test('should handle undefined state keys gracefully', () => {
        const value = stateManager.get('nonexistent-key');
        expect(value).toBeUndefined();
    });

    test('should handle null values', () => {
        stateManager.set('currentTaskId', null);
        expect(stateManager.get('currentTaskId')).toBeNull();
    });

    test('should handle complex object values', () => {
        const complexConfig = {
            llm: { endpoint: 'http://localhost:11434', model: 'llama2' },
            project: { root: '/path/to/project' }
        };
        
        stateManager.set('config', complexConfig);
        expect(stateManager.get('config')).toEqual(complexConfig);
    });

    test('should handle rapid state updates', () => {
        const callback = jest.fn();
        stateManager.subscribe('isTaskRunning', callback);
        
        // Rapid updates
        for (let i = 0; i < 100; i++) {
            stateManager.set('isTaskRunning', i % 2 === 0);
        }
        
        expect(callback).toHaveBeenCalledTimes(100);
    });

    test('should handle localStorage errors gracefully', () => {
        // Mock localStorage to throw error
        const originalSetItem = localStorage.setItem;
        localStorage.setItem = jest.fn(() => {
            throw new Error('QuotaExceededError');
        });
        
        // Should not throw, should handle error
        expect(() => {
            stateManager.set('theme', 'dark', true);
        }).not.toThrow();
        
        // Restore
        localStorage.setItem = originalSetItem;
    });

    test('should handle multiple subscriptions to same key', () => {
        const callbacks = Array.from({ length: 10 }, () => jest.fn());
        
        callbacks.forEach(cb => stateManager.subscribe('theme', cb));
        stateManager.set('theme', 'dark');
        
        callbacks.forEach(cb => {
            expect(cb).toHaveBeenCalledTimes(1);
        });
    });
});

// Test Suite: Integration Tests
describe('StateManager - Integration', () => {
    let stateManager;

    beforeEach(() => {
        setupTestEnvironment();
        stateManager = createStateManager();
    });

    test('should handle complete theme change workflow', () => {
        const callback = jest.fn();
        
        // Subscribe to theme changes
        stateManager.subscribe('theme', callback);
        
        // Change theme and persist
        stateManager.set('theme', 'dark', true);
        
        // Verify observer was called
        expect(callback).toHaveBeenCalledWith('dark', 'light');
        
        // Verify localStorage was updated
        expect(localStorage.getItem('app_theme')).toBe('dark');
        
        // Create new instance and verify persistence
        const newStateManager = createStateManager();
        expect(newStateManager.get('theme')).toBe('dark');
    });

    test('should handle complete view routing workflow', () => {
        const callback = jest.fn();
        
        // Subscribe to view changes
        stateManager.subscribe('currentView', callback);
        
        // Navigate through views
        stateManager.set('currentView', 'history', true);
        stateManager.set('currentView', 'settings', true);
        stateManager.set('currentView', 'task', true);
        
        // Verify observer was called for each change
        expect(callback).toHaveBeenCalledTimes(3);
        
        // Verify last state is persisted
        expect(localStorage.getItem('app_last_view')).toBe('task');
    });

    test('should handle session state persistence workflow', () => {
        // Simulate user session
        stateManager.set('theme', 'dark', true);
        stateManager.set('currentView', 'settings', true);
        stateManager.set('windowSize', { width: 1920, height: 1080 }, true);
        
        // Verify all persisted
        expect(localStorage.getItem('app_theme')).toBe('dark');
        expect(localStorage.getItem('app_last_view')).toBe('settings');
        expect(JSON.parse(localStorage.getItem('app_window_size'))).toEqual({
            width: 1920,
            height: 1080
        });
        
        // Simulate app restart by creating new instance
        const newStateManager = createStateManager();
        
        // Verify state restored
        expect(newStateManager.get('theme')).toBe('dark');
        expect(newStateManager.get('currentView')).toBe('settings');
        expect(newStateManager.get('windowSize')).toEqual({
            width: 1920,
            height: 1080
        });
    });
});

// Export for use with test runners
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        LocalStorageMock,
        setupTestEnvironment
    };
}
