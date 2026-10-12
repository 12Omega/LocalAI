/**
 * Integration Tests for Settings Manager Component
 * 
 * Tests configuration loading, field validation, saving, external change detection,
 * and interaction with backend via Eel.
 * 
 * Requirements tested: 4.1-4.11, 12.3-12.4
 */

describe('SettingsManager - Integration Tests', () => {
    let settingsManager;
    let mockEel;
    
    // Mock configuration data
    const mockConfig = {
        llm: {
            endpoint: 'http://localhost:11434',
            model: 'codellama:13b',
            temperature: 0.5,
            max_tokens: 4096,
            context_length: 16384,
            backend_type: 'ollama'
        },
        project_root: '/home/user/projects/myproject',
        log_level: 'info',
        web_research_enabled: true,
        self_improvement_enabled: false,
        gui: {
            theme: 'light',
            minimize_to_tray: false,
            auto_save_history: true,
            history_retention_days: 90
        }
    };
    
    // Helper to set up DOM
    const setupDOM = () => {
        document.body.innerHTML = `
            <div id="settings-panel">
                <form id="settings-form">
                    <!-- LLM Settings -->
                    <div class="form-section">
                        <h3>LLM Settings</h3>
                        <div class="form-group">
                            <label for="llm-endpoint">Endpoint</label>
                            <input type="text" id="llm-endpoint" />
                            <div id="llm-endpoint-error" class="error-message" style="display: none;"></div>
                        </div>
                        <div class="form-group">
                            <label for="llm-model">Model Name</label>
                            <input type="text" id="llm-model" />
                            <div id="llm-model-error" class="error-message" style="display: none;"></div>
                        </div>
                        <div class="form-group">
                            <label for="llm-temperature">Temperature</label>
                            <input type="range" id="llm-temperature" min="0" max="1" step="0.1" />
                            <span id="temperature-value">0.5</span>
                            <div id="llm-temperature-error" class="error-message" style="display: none;"></div>
                        </div>
                        <div class="form-group">
                            <label for="llm-max-tokens">Max Tokens</label>
                            <input type="number" id="llm-max-tokens" />
                            <div id="llm-max-tokens-error" class="error-message" style="display: none;"></div>
                        </div>
                        <div class="form-group">
                            <label for="llm-context-length">Context Length</label>
                            <input type="number" id="llm-context-length" />
                            <div id="llm-context-length-error" class="error-message" style="display: none;"></div>
                        </div>
                        <div class="form-group">
                            <label for="llm-backend-type">Backend Type</label>
                            <select id="llm-backend-type">
                                <option value="ollama">Ollama</option>
                                <option value="llamacpp">LlamaCpp</option>
                                <option value="openai-compatible">OpenAI Compatible</option>
                            </select>
                            <div id="llm-backend-type-error" class="error-message" style="display: none;"></div>
                        </div>
                    </div>
                    
                    <!-- Project Settings -->
                    <div class="form-section">
                        <h3>Project Settings</h3>
                        <div class="form-group">
                            <label for="project-root">Project Root</label>
                            <input type="text" id="project-root" />
                            <button type="button" id="browse-project-root">Browse</button>
                            <div id="project-root-error" class="error-message" style="display: none;"></div>
                        </div>
                        <div class="form-group">
                            <label for="log-level">Log Level</label>
                            <select id="log-level">
                                <option value="debug">Debug</option>
                                <option value="info">Info</option>
                                <option value="warning">Warning</option>
                                <option value="error">Error</option>
                            </select>
                            <div id="log-level-error" class="error-message" style="display: none;"></div>
                        </div>
                    </div>
                    
                    <!-- Feature Flags -->
                    <div class="form-section">
                        <h3>Feature Flags</h3>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" id="web-research-enabled" />
                                Enable web research
                            </label>
                        </div>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" id="self-improvement-enabled" />
                                Enable self-improvement
                            </label>
                        </div>
                    </div>
                    
                    <!-- GUI Settings -->
                    <div class="form-section">
                        <h3>GUI Settings</h3>
                        <div class="form-group">
                            <label for="gui-theme">Theme</label>
                            <select id="gui-theme">
                                <option value="light">Light</option>
                                <option value="dark">Dark</option>
                                <option value="auto">Auto (System)</option>
                            </select>
                            <div id="gui-theme-error" class="error-message" style="display: none;"></div>
                        </div>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" id="gui-minimize-to-tray" />
                                Minimize to system tray
                            </label>
                        </div>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" id="gui-auto-save-history" />
                                Auto-save task history
                            </label>
                        </div>
                        <div class="form-group">
                            <label for="gui-history-retention-days">History Retention (days)</label>
                            <input type="number" id="gui-history-retention-days" min="1" max="365" />
                            <div id="gui-history-retention-days-error" class="error-message" style="display: none;"></div>
                        </div>
                    </div>
                    
                    <div class="form-actions">
                        <button type="button" id="save-config-btn" class="btn btn-primary">Save Changes</button>
                        <button type="button" id="reset-config-btn" class="btn btn-secondary">Reset to Defaults</button>
                    </div>
                </form>
            </div>
        `;
    };
    
    // Helper to create mock Eel
    const createMockEel = () => {
        return {
            get_config: jest.fn(() => () => Promise.resolve(mockConfig)),
            save_config: jest.fn(() => () => Promise.resolve({ 
                success: true, 
                message: 'Configuration saved successfully' 
            })),
            validate_config_field: jest.fn((field, value) => () => {
                // Simple validation for testing
                if (field === 'llm.endpoint' && !value) {
                    return Promise.resolve({ valid: false, error: 'Endpoint is required' });
                }
                if (field === 'llm.temperature' && (value < 0 || value > 1)) {
                    return Promise.resolve({ valid: false, error: 'Must be between 0 and 1' });
                }
                return Promise.resolve({ valid: true });
            }),
            browse_directory: jest.fn(() => () => Promise.resolve({ 
                success: true, 
                path: '/home/user/selected/path' 
            }))
        };
    };
    
    beforeEach(async () => {
        setupDOM();
        mockEel = createMockEel();
        global.eel = mockEel;
        
        settingsManager = new SettingsManager();
        await settingsManager.initialize();
    });
    
    afterEach(() => {
        document.body.innerHTML = '';
        delete global.eel;
        jest.clearAllMocks();
    });
    
    /**
     * Requirement 4.1: Provide input fields for all configuration parameters
     */
    describe('Configuration Fields', () => {
        test('should provide input fields for all config parameters', () => {
            expect(document.getElementById('llm-endpoint')).toBeTruthy();
            expect(document.getElementById('llm-model')).toBeTruthy();
            expect(document.getElementById('llm-temperature')).toBeTruthy();
            expect(document.getElementById('llm-max-tokens')).toBeTruthy();
            expect(document.getElementById('llm-context-length')).toBeTruthy();
            expect(document.getElementById('llm-backend-type')).toBeTruthy();
            expect(document.getElementById('project-root')).toBeTruthy();
            expect(document.getElementById('log-level')).toBeTruthy();
            expect(document.getElementById('web-research-enabled')).toBeTruthy();
            expect(document.getElementById('self-improvement-enabled')).toBeTruthy();
            expect(document.getElementById('gui-theme')).toBeTruthy();
            expect(document.getElementById('gui-minimize-to-tray')).toBeTruthy();
            expect(document.getElementById('gui-auto-save-history')).toBeTruthy();
            expect(document.getElementById('gui-history-retention-days')).toBeTruthy();
        });
    });
    
    /**
     * Requirement 4.2: Display current configuration values
     */
    describe('Configuration Loading', () => {
        test('should load configuration from backend on init', () => {
            expect(mockEel.get_config).toHaveBeenCalled();
        });
        
        test('should populate form fields with current values', async () => {
            // Fields should be populated after initialization
            expect(document.getElementById('llm-endpoint').value).toBe('http://localhost:11434');
            expect(document.getElementById('llm-model').value).toBe('codellama:13b');
            expect(document.getElementById('llm-temperature').value).toBe('0.5');
            expect(document.getElementById('llm-max-tokens').value).toBe('4096');
            expect(document.getElementById('project-root').value).toBe('/home/user/projects/myproject');
            expect(document.getElementById('log-level').value).toBe('info');
            expect(document.getElementById('web-research-enabled').checked).toBe(true);
            expect(document.getElementById('self-improvement-enabled').checked).toBe(false);
            expect(document.getElementById('gui-theme').value).toBe('light');
            expect(document.getElementById('gui-history-retention-days').value).toBe('90');
        });
        
        test('should update temperature display value', () => {
            const temperatureDisplay = document.getElementById('temperature-value');
            expect(temperatureDisplay.textContent).toBe('0.5');
        });
    });
    
    /**
     * Requirements 4.3, 4.4: Validate input and display errors
     */
    describe('Field Validation', () => {
        test('should validate URL format for endpoint', async () => {
            const endpointInput = document.getElementById('llm-endpoint');
            const errorDiv = document.getElementById('llm-endpoint-error');
            
            // Set invalid URL
            endpointInput.value = 'not-a-url';
            endpointInput.dispatchEvent(new Event('blur'));
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(errorDiv.style.display).toBe('block');
            expect(errorDiv.textContent).toContain('Invalid URL');
        });
        
        test('should validate temperature range', async () => {
            const tempInput = document.getElementById('llm-temperature');
            const errorDiv = document.getElementById('llm-temperature-error');
            
            mockEel.validate_config_field = jest.fn(() => () => Promise.resolve({
                valid: false,
                error: 'Must be between 0.0 and 1.0'
            }));
            
            // Set invalid temperature
            tempInput.value = '1.5';
            tempInput.dispatchEvent(new Event('change'));
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(errorDiv.style.display).toBe('block');
        });
        
        test('should clear error when field value becomes valid', async () => {
            const endpointInput = document.getElementById('llm-endpoint');
            const errorDiv = document.getElementById('llm-endpoint-error');
            
            // Set invalid, then valid value
            endpointInput.value = 'invalid';
            endpointInput.dispatchEvent(new Event('blur'));
            await new Promise(resolve => setTimeout(resolve, 0));
            
            endpointInput.value = 'http://localhost:8080';
            endpointInput.dispatchEvent(new Event('input'));
            
            expect(errorDiv.style.display).toBe('none');
        });
        
        test('should validate positive integers for max_tokens', async () => {
            const maxTokensInput = document.getElementById('llm-max-tokens');
            const errorDiv = document.getElementById('llm-max-tokens-error');
            
            // Set invalid value
            maxTokensInput.value = '-100';
            maxTokensInput.dispatchEvent(new Event('blur'));
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(errorDiv.textContent).toContain('positive integer');
        });
        
        test('should validate required fields', async () => {
            const endpointInput = document.getElementById('llm-endpoint');
            const errorDiv = document.getElementById('llm-endpoint-error');
            
            mockEel.validate_config_field = jest.fn(() => () => Promise.resolve({
                valid: false,
                error: 'Endpoint is required'
            }));
            
            // Clear required field
            endpointInput.value = '';
            endpointInput.dispatchEvent(new Event('blur'));
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(errorDiv.style.display).toBe('block');
            expect(errorDiv.textContent).toContain('required');
        });
    });
    
    /**
     * Requirements 4.5, 4.6: Save button to persist changes
     */
    describe('Configuration Saving', () => {
        test('should provide save button', () => {
            const saveButton = document.getElementById('save-config-btn');
            expect(saveButton).toBeTruthy();
        });
        
        test('should save configuration when save button clicked', async () => {
            const saveButton = document.getElementById('save-config-btn');
            
            // Modify a field
            const endpointInput = document.getElementById('llm-endpoint');
            endpointInput.value = 'http://localhost:8080';
            endpointInput.dispatchEvent(new Event('blur'));
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            // Enable save button
            settingsManager.hasChanges = true;
            settingsManager.updateSaveButtonState();
            
            // Click save
            saveButton.click();
            
            await new Promise(resolve => setTimeout(resolve, 100));
            
            expect(mockEel.save_config).toHaveBeenCalled();
        });
        
        test('should validate all fields before saving', async () => {
            const saveButton = document.getElementById('save-config-btn');
            const endpointInput = document.getElementById('llm-endpoint');
            
            // Set invalid endpoint
            mockEel.validate_config_field = jest.fn(() => () => Promise.resolve({
                valid: false,
                error: 'Invalid URL'
            }));
            
            endpointInput.value = 'invalid-url';
            endpointInput.dispatchEvent(new Event('blur'));
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            settingsManager.hasChanges = true;
            settingsManager.updateSaveButtonState();
            
            // Try to save
            saveButton.click();
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            // Should not call save with invalid data
            expect(mockEel.save_config).not.toHaveBeenCalled();
        });
        
        test('should show success message after successful save', async () => {
            const saveButton = document.getElementById('save-config-btn');
            const showSuccessSpy = jest.spyOn(settingsManager, 'showSuccess');
            
            settingsManager.hasChanges = true;
            settingsManager.updateSaveButtonState();
            
            await saveButton.click();
            await new Promise(resolve => setTimeout(resolve, 100));
            
            expect(showSuccessSpy).toHaveBeenCalledWith(expect.stringContaining('saved'));
        });
        
        test('should disable save button when no changes', () => {
            const saveButton = document.getElementById('save-config-btn');
            
            settingsManager.hasChanges = false;
            settingsManager.updateSaveButtonState();
            
            expect(saveButton.disabled).toBe(true);
        });
        
        test('should enable save button when changes are made', async () => {
            const saveButton = document.getElementById('save-config-btn');
            const endpointInput = document.getElementById('llm-endpoint');
            
            // Make a change
            endpointInput.value = 'http://localhost:9999';
            endpointInput.dispatchEvent(new Event('blur'));
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(saveButton.disabled).toBe(false);
        });
    });
    
    /**
     * Requirement 4.7: Reset button to restore defaults
     */
    describe('Reset to Defaults', () => {
        test('should provide reset button', () => {
            const resetButton = document.getElementById('reset-config-btn');
            expect(resetButton).toBeTruthy();
        });
        
        test('should show confirmation dialog before resetting', () => {
            const resetButton = document.getElementById('reset-config-btn');
            const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(false);
            
            resetButton.click();
            
            expect(confirmSpy).toHaveBeenCalled();
            confirmSpy.mockRestore();
        });
        
        test('should reload config when user confirms reset', async () => {
            const resetButton = document.getElementById('reset-config-btn');
            const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
            const loadConfigSpy = jest.spyOn(settingsManager, 'loadConfig');
            
            await resetButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(loadConfigSpy).toHaveBeenCalled();
            
            confirmSpy.mockRestore();
        });
    });
    
    /**
     * Requirement 4.8: Browse button for file path selections
     */
    describe('Directory Browser', () => {
        test('should provide browse button for project root', () => {
            const browseButton = document.getElementById('browse-project-root');
            expect(browseButton).toBeTruthy();
        });
        
        test('should open directory browser when browse button clicked', async () => {
            const browseButton = document.getElementById('browse-project-root');
            
            await browseButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(mockEel.browse_directory).toHaveBeenCalled();
        });
        
        test('should update field with selected path', async () => {
            const browseButton = document.getElementById('browse-project-root');
            const projectRootInput = document.getElementById('project-root');
            
            await browseButton.click();
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(projectRootInput.value).toBe('/home/user/selected/path');
        });
    });
    
    /**
     * Requirements 12.3, 12.4: External config change detection
     */
    describe('External Configuration Changes', () => {
        test('should have function exposed for Python to call', () => {
            expect(typeof window.eel_config_external_change).toBe('function');
        });
        
        test('should show prompt when external change detected', () => {
            const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(false);
            
            // Simulate external change notification
            window.eel_config_external_change({
                message: 'Configuration file was modified externally'
            });
            
            expect(confirmSpy).toHaveBeenCalledWith(expect.stringContaining('modified externally'));
            
            confirmSpy.mockRestore();
        });
        
        test('should reload config when user confirms', async () => {
            const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
            const loadConfigSpy = jest.spyOn(settingsManager, 'loadConfig');
            
            window.eel_config_external_change({
                message: 'Configuration file was modified externally'
            });
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(loadConfigSpy).toHaveBeenCalled();
            
            confirmSpy.mockRestore();
        });
        
        test('should keep current settings when user cancels', async () => {
            const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(false);
            const loadConfigSpy = jest.spyOn(settingsManager, 'loadConfig');
            
            const originalEndpoint = document.getElementById('llm-endpoint').value;
            
            window.eel_config_external_change({
                message: 'Configuration file was modified externally'
            });
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            expect(loadConfigSpy).not.toHaveBeenCalled();
            expect(document.getElementById('llm-endpoint').value).toBe(originalEndpoint);
            
            confirmSpy.mockRestore();
        });
    });
    
    /**
     * Complete save/load cycle test
     */
    describe('Complete Save/Load Cycle', () => {
        test('should handle complete configuration modification workflow', async () => {
            // Step 1: Load initial config
            expect(mockEel.get_config).toHaveBeenCalled();
            expect(document.getElementById('llm-endpoint').value).toBe('http://localhost:11434');
            
            // Step 2: Modify multiple fields
            const endpointInput = document.getElementById('llm-endpoint');
            const tempInput = document.getElementById('llm-temperature');
            const webResearchCheckbox = document.getElementById('web-research-enabled');
            
            endpointInput.value = 'http://localhost:8080';
            endpointInput.dispatchEvent(new Event('blur'));
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            tempInput.value = '0.7';
            tempInput.dispatchEvent(new Event('change'));
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            webResearchCheckbox.checked = false;
            webResearchCheckbox.dispatchEvent(new Event('change'));
            
            await new Promise(resolve => setTimeout(resolve, 0));
            
            // Step 3: Save changes
            const saveButton = document.getElementById('save-config-btn');
            settingsManager.hasChanges = true;
            settingsManager.updateSaveButtonState();
            
            await saveButton.click();
            await new Promise(resolve => setTimeout(resolve, 100));
            
            expect(mockEel.save_config).toHaveBeenCalled();
            
            const savedConfig = mockEel.save_config.mock.calls[0][0];
            expect(savedConfig.llm.endpoint).toBe('http://localhost:8080');
            expect(savedConfig.llm.temperature).toBe(0.7);
            expect(savedConfig.web_research_enabled).toBe(false);
            
            // Step 4: Verify save button disabled after save
            expect(settingsManager.hasChanges).toBe(false);
        });
    });
});
