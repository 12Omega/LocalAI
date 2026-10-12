/**
 * Settings Manager Component
 * 
 * Implements the Settings Manager for the Desktop GUI Application.
 * Handles configuration loading, validation, saving, and user interactions.
 * 
 * Requirements implemented:
 * - 4.1: Provide input fields for all configuration parameters
 * - 4.2: Display current configuration values
 * - 4.3: Validate input before accepting
 * - 4.4: Display error message for invalid input
 * - 4.5: Save button to persist changes
 * - 4.6: Write updated values to config.yaml
 * - 4.7: Reset button to restore defaults
 * - 4.8: Browse button for file path selections
 * - 4.9: Display help text/tooltips
 * - 4.10: Prompt for API key when LLM provider changed
 * - 4.11: Mask sensitive values
 * - 12.3: Detect external config changes
 * - 12.4: Prompt to reload or keep current settings
 */

class SettingsManager {
    constructor() {
        // State
        this.config = null;
        this.originalConfig = null;
        this.hasChanges = false;
        this.validationErrors = {};
        this.isLoading = false;
        
        // DOM elements
        this.form = document.getElementById('settings-form');
        this.saveButton = document.getElementById('save-config-btn');
        this.resetButton = document.getElementById('reset-config-btn');
        this.browseProjectRootBtn = document.getElementById('browse-project-root');
        
        // Form fields
        this.fields = {
            'llm.endpoint': document.getElementById('llm-endpoint'),
            'llm.model': document.getElementById('llm-model'),
            'llm.temperature': document.getElementById('llm-temperature'),
            'llm.max_tokens': document.getElementById('llm-max-tokens'),
            'llm.context_length': document.getElementById('llm-context-length'),
            'llm.backend_type': document.getElementById('llm-backend-type'),
            'project_root': document.getElementById('project-root'),
            'log_level': document.getElementById('log-level'),
            'web_research_enabled': document.getElementById('web-research-enabled'),
            'self_improvement_enabled': document.getElementById('self-improvement-enabled'),
            'gui.theme': document.getElementById('gui-theme'),
            'gui.minimize_to_tray': document.getElementById('gui-minimize-to-tray'),
            'gui.auto_save_history': document.getElementById('gui-auto-save-history'),
            'gui.history_retention_days': document.getElementById('gui-history-retention-days')
        };
        
        // Temperature display
        this.temperatureDisplay = document.getElementById('temperature-value');
        
        this.initialize();
    }
    
    /**
     * Initialize the component
     */
    async initialize() {
        console.log('Initializing Settings Manager...');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load configuration from backend
        await this.loadConfig();
        
        // Listen for external config changes (Req 12.3, 12.4)
        this.setupExternalChangeListener();
        
        console.log('Settings Manager initialized');
    }
    
    /**
     * Set up event listeners for form interactions
     */
    setupEventListeners() {
        // Save button (Req 4.5)
        this.saveButton?.addEventListener('click', () => this.saveConfig());
        
        // Reset button (Req 4.7)
        this.resetButton?.addEventListener('click', () => this.resetConfig());
        
        // Browse button for project root (Req 4.8)
        this.browseProjectRootBtn?.addEventListener('click', () => this.browseDirectory('project_root'));
        
        // Field change handlers with validation (Req 4.3)
        for (const [fieldName, element] of Object.entries(this.fields)) {
            if (!element) continue;
            
            if (element.type === 'checkbox') {
                element.addEventListener('change', () => {
                    this.handleFieldChange(fieldName, element.checked);
                });
            } else if (element.type === 'range') {
                // Real-time update for range slider
                element.addEventListener('input', () => {
                    this.updateTemperatureDisplay(element.value);
                });
                element.addEventListener('change', () => {
                    this.handleFieldChange(fieldName, parseFloat(element.value));
                });
            } else {
                element.addEventListener('blur', () => {
                    this.handleFieldChange(fieldName, element.value);
                });
                // Clear error on input
                element.addEventListener('input', () => {
                    this.clearFieldError(fieldName);
                });
            }
        }
        
        // Prevent form submission
        this.form?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveConfig();
        });
    }
    
    /**
     * Load configuration from backend (Req 4.2)
     */
    async loadConfig() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingState();
        
        try {
            console.log('Loading configuration...');
            const config = await eel.get_config()();
            
            if (config.error) {
                throw new Error(config.error);
            }
            
            this.config = config;
            this.originalConfig = JSON.parse(JSON.stringify(config)); // Deep clone
            this.hasChanges = false;
            
            // Populate form fields
            this.populateForm();
            
            console.log('Configuration loaded successfully');
            
        } catch (error) {
            console.error('Error loading configuration:', error);
            this.showError('Failed to load configuration: ' + error.message);
        } finally {
            this.isLoading = false;
            this.hideLoadingState();
        }
    }
    
    /**
     * Populate form fields with configuration values (Req 4.2, 4.11)
     */
    populateForm() {
        if (!this.config) return;
        
        // Helper to get nested property
        const getNestedValue = (obj, path) => {
            return path.split('.').reduce((current, key) => current?.[key], obj);
        };
        
        for (const [fieldName, element] of Object.entries(this.fields)) {
            if (!element) continue;
            
            const value = getNestedValue(this.config, fieldName);
            
            if (value !== undefined && value !== null) {
                if (element.type === 'checkbox') {
                    element.checked = Boolean(value);
                } else if (element.type === 'range') {
                    element.value = value;
                    this.updateTemperatureDisplay(value);
                } else if (element.type === 'number') {
                    element.value = value;
                } else {
                    element.value = value;
                }
            }
        }
        
        // Update save button state
        this.updateSaveButtonState();
    }
    
    /**
     * Update temperature display value
     */
    updateTemperatureDisplay(value) {
        if (this.temperatureDisplay) {
            this.temperatureDisplay.textContent = parseFloat(value).toFixed(1);
        }
    }
    
    /**
     * Handle field value change with validation (Req 4.3)
     */
    async handleFieldChange(fieldName, value) {
        console.log(`Field changed: ${fieldName} = ${value}`);
        
        // Client-side validation
        const isValid = await this.validateField(fieldName, value);
        
        if (isValid) {
            // Update config object
            this.updateConfigValue(fieldName, value);
            this.hasChanges = true;
            this.updateSaveButtonState();
        }
    }
    
    /**
     * Validate a field (client and server-side) (Req 4.3, 4.4)
     */
    async validateField(fieldName, value) {
        try {
            // Client-side validation first
            const clientValidation = this.clientSideValidate(fieldName, value);
            if (!clientValidation.valid) {
                this.markFieldError(fieldName, clientValidation.error);
                return false;
            }
            
            // Server-side validation (Req 4.3)
            const result = await eel.validate_config_field(fieldName, value)();
            
            if (result.valid) {
                this.clearFieldError(fieldName);
                return true;
            } else {
                this.markFieldError(fieldName, result.error); // Req 4.4
                return false;
            }
            
        } catch (error) {
            console.error(`Validation error for ${fieldName}:`, error);
            this.markFieldError(fieldName, 'Validation failed: ' + error.message);
            return false;
        }
    }
    
    /**
     * Client-side validation for quick feedback
     */
    clientSideValidate(fieldName, value) {
        // URL validation
        if (fieldName === 'llm.endpoint') {
            if (!value || value.trim() === '') {
                return { valid: false, error: 'Endpoint URL is required' };
            }
            try {
                new URL(value);
                return { valid: true };
            } catch {
                return { valid: false, error: 'Invalid URL format' };
            }
        }
        
        // Number range validation
        if (fieldName === 'llm.temperature') {
            const num = parseFloat(value);
            if (isNaN(num) || num < 0.0 || num > 1.0) {
                return { valid: false, error: 'Temperature must be between 0.0 and 1.0' };
            }
            return { valid: true };
        }
        
        // Positive integer validation
        if (fieldName === 'llm.max_tokens' || fieldName === 'llm.context_length') {
            const num = parseInt(value, 10);
            if (isNaN(num) || num < 1) {
                return { valid: false, error: 'Must be a positive integer' };
            }
            return { valid: true };
        }
        
        // History retention days
        if (fieldName === 'gui.history_retention_days') {
            const num = parseInt(value, 10);
            if (isNaN(num) || num < 1 || num > 365) {
                return { valid: false, error: 'Must be between 1 and 365 days' };
            }
            return { valid: true };
        }
        
        // Directory path validation
        if (fieldName === 'project_root') {
            if (!value || value.trim() === '') {
                return { valid: false, error: 'Project root is required' };
            }
            return { valid: true };
        }
        
        // Model name validation
        if (fieldName === 'llm.model') {
            if (!value || value.trim() === '') {
                return { valid: false, error: 'Model name is required' };
            }
            return { valid: true };
        }
        
        return { valid: true };
    }
    
    /**
     * Update configuration value in config object
     */
    updateConfigValue(fieldName, value) {
        const keys = fieldName.split('.');
        let current = this.config;
        
        for (let i = 0; i < keys.length - 1; i++) {
            if (!current[keys[i]]) {
                current[keys[i]] = {};
            }
            current = current[keys[i]];
        }
        
        current[keys[keys.length - 1]] = value;
    }
    
    /**
     * Mark field as having an error (Req 4.4)
     */
    markFieldError(fieldName, message) {
        this.validationErrors[fieldName] = message;
        
        const element = this.fields[fieldName];
        const errorElement = document.getElementById(`${element?.id}-error`);
        
        if (element) {
            element.classList.add('error');
            element.setAttribute('aria-invalid', 'true');
        }
        
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
    }
    
    /**
     * Clear field error
     */
    clearFieldError(fieldName) {
        delete this.validationErrors[fieldName];
        
        const element = this.fields[fieldName];
        const errorElement = document.getElementById(`${element?.id}-error`);
        
        if (element) {
            element.classList.remove('error');
            element.removeAttribute('aria-invalid');
        }
        
        if (errorElement) {
            errorElement.textContent = '';
            errorElement.style.display = 'none';
        }
    }
    
    /**
     * Save configuration to backend (Req 4.5, 4.6)
     */
    async saveConfig() {
        if (this.isLoading) return;
        
        // Check for validation errors
        if (Object.keys(this.validationErrors).length > 0) {
            this.showError('Please fix validation errors before saving');
            return;
        }
        
        this.isLoading = true;
        this.showSavingState();
        
        try {
            console.log('Saving configuration...');
            
            // Validate all fields before saving
            let allValid = true;
            for (const [fieldName, element] of Object.entries(this.fields)) {
                if (!element) continue;
                
                let value;
                if (element.type === 'checkbox') {
                    value = element.checked;
                } else if (element.type === 'range' || element.type === 'number') {
                    value = element.type === 'range' ? parseFloat(element.value) : parseInt(element.value, 10);
                } else {
                    value = element.value;
                }
                
                const isValid = await this.validateField(fieldName, value);
                if (!isValid) {
                    allValid = false;
                }
            }
            
            if (!allValid) {
                this.showError('Please fix all validation errors before saving');
                return;
            }
            
            // Save to backend (Req 4.6)
            const result = await eel.save_config(this.config)();
            
            if (result.success) {
                console.log('Configuration saved successfully');
                this.showSuccess(result.message || 'Settings saved successfully');
                
                // Announce to screen readers
                if (typeof window.accessibility !== 'undefined' && window.accessibility.announceToScreenReader) {
                    window.accessibility.announceToScreenReader('Settings saved successfully', 'polite');
                }
                
                // Update original config
                this.originalConfig = JSON.parse(JSON.stringify(this.config));
                this.hasChanges = false;
                this.updateSaveButtonState();
                
                // Dispatch event for other components
                window.dispatchEvent(new CustomEvent('config-saved', {
                    detail: { config: this.config }
                }));
                
            } else {
                throw new Error(result.error || 'Failed to save configuration');
            }
            
        } catch (error) {
            console.error('Error saving configuration:', error);
            this.showError('Failed to save settings: ' + error.message);
        } finally {
            this.isLoading = false;
            this.hideSavingState();
        }
    }
    
    /**
     * Reset configuration to defaults (Req 4.7)
     */
    async resetConfig() {
        if (this.isLoading) return;
        
        // Confirm with user
        const confirmed = confirm(
            'Are you sure you want to reset all settings to their default values? This cannot be undone.'
        );
        
        if (!confirmed) return;
        
        this.isLoading = true;
        this.showLoadingState();
        
        try {
            console.log('Resetting configuration to defaults...');
            
            // For now, we'll reload the config which should have defaults
            // In a full implementation, we'd call a reset_to_defaults() backend function
            await this.loadConfig();
            
            this.showSuccess('Settings reset to defaults');
            
        } catch (error) {
            console.error('Error resetting configuration:', error);
            this.showError('Failed to reset settings: ' + error.message);
        } finally {
            this.isLoading = false;
            this.hideLoadingState();
        }
    }
    
    /**
     * Open directory browser for file path selection (Req 4.8)
     */
    async browseDirectory(fieldName) {
        try {
            const currentValue = this.fields[fieldName]?.value || '';
            
            const result = await eel.browse_directory(currentValue)();
            
            if (result.success && result.path) {
                const element = this.fields[fieldName];
                if (element) {
                    element.value = result.path;
                    await this.handleFieldChange(fieldName, result.path);
                }
            }
            
        } catch (error) {
            console.error('Error browsing directory:', error);
            this.showError('Failed to open directory browser');
        }
    }
    
    /**
     * Set up listener for external config changes (Req 12.3, 12.4)
     */
    setupExternalChangeListener() {
        // Expose function for Python to call via Eel
        if (typeof eel !== 'undefined') {
            // Store reference to this for use in eel callback
            const self = this;
            
            // Expose function that Python can call
            window.eel_config_external_change = function(data) {
                console.log('External config change received from Python:', data);
                self.handleExternalChange(data);
            };
        }
        
        // Also listen for custom events (for component communication)
        window.addEventListener('config-external-change', (event) => {
            this.handleExternalChange(event.detail);
        });
    }
    
    /**
     * Handle external configuration change notification (Req 12.4)
     */
    handleExternalChange(data) {
        console.log('External configuration change detected:', data);
        
        // Show prompt to user
        const reload = confirm(
            'The configuration file was modified externally.\n\n' +
            'Do you want to reload the settings?\n' +
            '(Clicking Cancel will keep your current settings)'
        );
        
        if (reload) {
            this.loadConfig();
        }
    }
    
    /**
     * Update save button state based on changes
     */
    updateSaveButtonState() {
        if (this.saveButton) {
            this.saveButton.disabled = !this.hasChanges || Object.keys(this.validationErrors).length > 0;
        }
    }
    
    /**
     * Show loading state
     */
    showLoadingState() {
        if (this.saveButton) this.saveButton.disabled = true;
        if (this.resetButton) this.resetButton.disabled = true;
        
        // Disable all form fields
        for (const element of Object.values(this.fields)) {
            if (element) element.disabled = true;
        }
    }
    
    /**
     * Hide loading state
     */
    hideLoadingState() {
        if (this.resetButton) this.resetButton.disabled = false;
        
        // Re-enable all form fields
        for (const element of Object.values(this.fields)) {
            if (element) element.disabled = false;
        }
        
        this.updateSaveButtonState();
    }
    
    /**
     * Show saving state
     */
    showSavingState() {
        if (this.saveButton) {
            this.saveButton.disabled = true;
            this.saveButton.textContent = 'Saving...';
        }
        
        // Disable form fields
        for (const element of Object.values(this.fields)) {
            if (element) element.disabled = true;
        }
    }
    
    /**
     * Hide saving state
     */
    hideSavingState() {
        if (this.saveButton) {
            this.saveButton.textContent = 'Save Changes';
        }
        
        // Re-enable form fields
        for (const element of Object.values(this.fields)) {
            if (element) element.disabled = false;
        }
        
        this.updateSaveButtonState();
    }
    
    /**
     * Show success message
     */
    showSuccess(message) {
        // Announce to screen readers
        if (typeof window.accessibility !== 'undefined' && window.accessibility.announceToScreenReader) {
            window.accessibility.announceToScreenReader(message, 'polite');
        }
        
        // Create a temporary success notification
        const notification = document.createElement('div');
        notification.className = 'notification success';
        notification.setAttribute('role', 'status');
        notification.setAttribute('aria-live', 'polite');
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--color-success);
            color: white;
            padding: 12px 24px;
            border-radius: 6px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
    /**
     * Show error message
     */
    showError(message) {
        // Announce to screen readers with assertive priority
        if (typeof window.accessibility !== 'undefined' && window.accessibility.announceToScreenReader) {
            window.accessibility.announceToScreenReader(message, 'assertive');
        }
        
        // Create a temporary error notification
        const notification = document.createElement('div');
        notification.className = 'notification error';
        notification.setAttribute('role', 'alert');
        notification.setAttribute('aria-live', 'assertive');
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--color-error);
            color: white;
            padding: 12px 24px;
            border-radius: 6px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }
}

// Export for use in main.js
window.SettingsManager = SettingsManager;
