/**
 * Setup Wizard Component
 * 
 * Handles first-run setup experience for the Desktop GUI Application.
 * Guides users through essential configuration: LLM endpoint, working directory.
 * 
 * Requirements:
 * - 19.2: First-run experience with setup dialog
 */

class SetupWizard {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 4;
        this.config = {
            llm: {
                endpoint: '',
                model_name: '',
                backend_type: 'ollama',
                temperature: 0.7,
                max_tokens: 4096,
                context_length: 8192
            },
            project_root: '',
            log_level: 'info',
            web_research_enabled: false,
            self_improvement_enabled: false,
            excluded_directories: [
                'node_modules', '.git', '__pycache__', 'venv', '.venv',
                'dist', 'build', '.pytest_cache', '.tox'
            ]
        };
        this.isValidating = false;
        this.isUrlValidated = false;
    }
    
    /**
     * Initialize the setup wizard
     */
    init() {
        console.log('Setup Wizard initialized');
        
        // Setup event listeners
        this.setupEventListeners();
    }
    
    /**
     * Show the setup wizard dialog
     */
    async show() {
        console.log('Showing setup wizard');
        
        // Check if this is actually first run
        try {
            const isFirstRun = await eel.is_first_run()();
            if (!isFirstRun) {
                console.log('Not first run, skipping setup wizard');
                return;
            }
        } catch (error) {
            console.error('Error checking first run status:', error);
            // If we can't check, assume it's not first run
            return;
        }
        
        // Show the dialog
        const dialog = document.getElementById('setup-dialog');
        if (dialog) {
            dialog.classList.remove('hidden');
            this.goToStep(1);
            
            // Focus on first input
            setTimeout(() => {
                const firstInput = dialog.querySelector('input:not([type="hidden"])');
                if (firstInput) {
                    firstInput.focus();
                }
            }, 100);
        }
    }
    
    /**
     * Hide the setup wizard dialog
     */
    hide() {
        const dialog = document.getElementById('setup-dialog');
        if (dialog) {
            dialog.classList.add('hidden');
        }
    }
    
    /**
     * Navigate to a specific step
     */
    goToStep(stepNumber) {
        if (stepNumber < 1 || stepNumber > this.totalSteps) {
            return;
        }
        
        this.currentStep = stepNumber;
        
        // Hide all steps
        document.querySelectorAll('.setup-step').forEach(step => {
            step.classList.remove('active');
            step.setAttribute('hidden', '');
        });
        
        // Show current step
        const currentStepEl = document.getElementById(`setup-step-${stepNumber}`);
        if (currentStepEl) {
            currentStepEl.classList.add('active');
            currentStepEl.removeAttribute('hidden');
        }
        
        // Update progress dots
        this.updateProgressDots();
        
        // Update navigation buttons
        this.updateNavigationButtons();
        
        // Focus on first input in step
        setTimeout(() => {
            const firstInput = currentStepEl?.querySelector('input:not([type="hidden"]), select');
            if (firstInput) {
                firstInput.focus();
            }
        }, 100);
    }
    
    /**
     * Update progress dots to reflect current step
     */
    updateProgressDots() {
        document.querySelectorAll('.setup-progress-dot').forEach((dot, index) => {
            const stepNum = index + 1;
            if (stepNum < this.currentStep) {
                dot.classList.add('completed');
                dot.classList.remove('active');
            } else if (stepNum === this.currentStep) {
                dot.classList.add('active');
                dot.classList.remove('completed');
            } else {
                dot.classList.remove('active', 'completed');
            }
        });
    }
    
    /**
     * Update navigation button states
     */
    updateNavigationButtons() {
        const backBtn = document.getElementById('setup-back-btn');
        const nextBtn = document.getElementById('setup-next-btn');
        const finishBtn = document.getElementById('setup-finish-btn');
        
        if (backBtn) {
            backBtn.disabled = this.currentStep === 1;
        }
        
        if (nextBtn) {
            nextBtn.style.display = this.currentStep < this.totalSteps ? 'inline-flex' : 'none';
            
            // Disable next button on step 2 if URL not validated
            if (this.currentStep === 2) {
                nextBtn.disabled = !this.isUrlValidated;
            } else {
                nextBtn.disabled = false;
            }
        }
        
        if (finishBtn) {
            finishBtn.style.display = this.currentStep === this.totalSteps ? 'inline-flex' : 'none';
        }
    }
    
    /**
     * Setup event listeners for wizard controls
     */
    setupEventListeners() {
        // Back button
        const backBtn = document.getElementById('setup-back-btn');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                this.goToStep(this.currentStep - 1);
            });
        }
        
        // Next button
        const nextBtn = document.getElementById('setup-next-btn');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                if (this.validateCurrentStep()) {
                    this.goToStep(this.currentStep + 1);
                }
            });
        }
        
        // Finish button
        const finishBtn = document.getElementById('setup-finish-btn');
        if (finishBtn) {
            finishBtn.addEventListener('click', () => {
                this.completeSetup();
            });
        }
        
        // Test Connection button
        const testBtn = document.getElementById('setup-test-connection');
        if (testBtn) {
            testBtn.addEventListener('click', () => {
                this.testConnection();
            });
        }
        
        // Browse directory button
        const browseBtn = document.getElementById('setup-browse-directory');
        if (browseBtn) {
            browseBtn.addEventListener('click', () => {
                this.browseDirectory();
            });
        }
        
        // LLM endpoint input - clear validation when changed
        const endpointInput = document.getElementById('setup-llm-endpoint');
        if (endpointInput) {
            endpointInput.addEventListener('input', () => {
                this.isUrlValidated = false;
                this.updateNavigationButtons();
                this.clearValidationMessage('setup-endpoint-validation');
            });
        }
        
        // Backend type selector
        const backendSelect = document.getElementById('setup-backend-type');
        if (backendSelect) {
            backendSelect.addEventListener('change', (e) => {
                this.showBackendHelp(e.target.value);
            });
        }
    }
    
    /**
     * Show helpful information based on selected backend type
     */
    showBackendHelp(backendType) {
        const helpEl = document.getElementById('setup-backend-help');
        if (!helpEl) return;
        
        const helpText = {
            'ollama': 'Ollama typically runs on http://localhost:11434',
            'llamacpp': 'llama.cpp server typically runs on http://localhost:8080',
            'openai-compatible': 'Enter the base URL of your OpenAI-compatible API server'
        };
        
        helpEl.textContent = helpText[backendType] || '';
    }
    
    /**
     * Validate current step before allowing navigation
     */
    validateCurrentStep() {
        switch (this.currentStep) {
            case 1:
                // Welcome step - no validation needed
                return true;
                
            case 2:
                // LLM endpoint - must be validated
                if (!this.isUrlValidated) {
                    this.showValidationMessage('setup-endpoint-validation', 
                        'Please test the connection before continuing', 'error');
                    return false;
                }
                
                // Get and save values
                this.config.llm.endpoint = document.getElementById('setup-llm-endpoint')?.value || '';
                this.config.llm.model_name = document.getElementById('setup-model-name')?.value || '';
                this.config.llm.backend_type = document.getElementById('setup-backend-type')?.value || 'ollama';
                return true;
                
            case 3:
                // API key - optional, no validation
                const apiKey = document.getElementById('setup-api-key')?.value || '';
                if (apiKey) {
                    // Store encrypted API key if provided
                    // For now, we'll just note that it's optional
                }
                return true;
                
            case 4:
                // Working directory - must be non-empty
                const projectRoot = document.getElementById('setup-project-root')?.value || '';
                if (!projectRoot.trim()) {
                    this.showValidationMessage('setup-directory-validation',
                        'Please select a working directory', 'error');
                    return false;
                }
                this.config.project_root = projectRoot;
                return true;
                
            default:
                return true;
        }
    }
    
    /**
     * Test LLM endpoint connection
     */
    async testConnection() {
        if (this.isValidating) {
            return;
        }
        
        const endpointInput = document.getElementById('setup-llm-endpoint');
        const testBtn = document.getElementById('setup-test-connection');
        const validationEl = document.getElementById('setup-endpoint-validation');
        
        if (!endpointInput) return;
        
        const url = endpointInput.value.trim();
        
        if (!url) {
            this.showValidationMessage('setup-endpoint-validation', 
                'Please enter an endpoint URL', 'error');
            return;
        }
        
        // Show loading state
        this.isValidating = true;
        if (testBtn) {
            testBtn.disabled = true;
            testBtn.textContent = 'Testing...';
        }
        this.showValidationMessage('setup-endpoint-validation', 
            'Testing connection...', 'info');
        
        try {
            const result = await eel.validate_llm_endpoint(url)();
            
            if (result.reachable) {
                this.isUrlValidated = true;
                this.showValidationMessage('setup-endpoint-validation',
                    '✓ Connection successful', 'success');
                this.updateNavigationButtons();
            } else {
                this.isUrlValidated = false;
                this.showValidationMessage('setup-endpoint-validation',
                    `✗ Connection failed: ${result.error}`, 'error');
                this.updateNavigationButtons();
            }
        } catch (error) {
            console.error('Error testing connection:', error);
            this.isUrlValidated = false;
            this.showValidationMessage('setup-endpoint-validation',
                '✗ Connection test failed', 'error');
            this.updateNavigationButtons();
        } finally {
            this.isValidating = false;
            if (testBtn) {
                testBtn.disabled = false;
                testBtn.textContent = 'Test Connection';
            }
        }
    }
    
    /**
     * Browse for working directory
     */
    async browseDirectory() {
        const directoryInput = document.getElementById('setup-project-root');
        const currentPath = directoryInput?.value || '';
        
        // Check if Eel is connected
        if (typeof eel === 'undefined') {
            console.error('Eel not connected');
            this.showValidationMessage('setup-directory-validation',
                'Backend not connected', 'error');
            return;
        }
        
        try {
            const result = await eel.browse_directory(currentPath)();
            
            if (result.success && result.path) {
                if (directoryInput) {
                    directoryInput.value = result.path;
                }
                this.clearValidationMessage('setup-directory-validation');
            }
        } catch (error) {
            console.error('Error browsing directory:', error);
            this.showValidationMessage('setup-directory-validation',
                'Error opening directory browser', 'error');
        }
    }
    
    /**
     * Complete setup and save configuration
     */
    async completeSetup() {
        console.log('Completing setup...');
        
        // Final validation
        if (!this.validateCurrentStep()) {
            return;
        }
        
        // Show loading state
        const finishBtn = document.getElementById('setup-finish-btn');
        if (finishBtn) {
            finishBtn.disabled = true;
            finishBtn.textContent = 'Saving...';
        }
        
        // Check if Eel is connected
        if (typeof eel === 'undefined') {
            console.error('Eel not connected');
            this.showValidationMessage('setup-finish-error',
                'Backend not connected', 'error');
            if (finishBtn) {
                finishBtn.disabled = false;
                finishBtn.textContent = 'Finish';
            }
            return;
        }
        
        try {
            // Call backend to save config and create sentinel file
            const result = await eel.complete_first_run_setup(this.config)();
            
            if (result.success) {
                console.log('Setup completed successfully');
                
                // Hide wizard
                this.hide();
                
                // Reload settings in main app
                if (typeof window.app !== 'undefined' && 
                    window.app.settingsManager && 
                    window.app.settingsManager.loadSettings) {
                    await window.app.settingsManager.loadSettings();
                }
                
                // Show success notification
                if (typeof window.showNotification === 'function') {
                    window.showNotification('Setup complete! You can now start using the application.', 'success');
                }
            } else {
                console.error('Setup failed:', result.error);
                this.showValidationMessage('setup-finish-error',
                    `Setup failed: ${result.error}`, 'error');
                
                if (finishBtn) {
                    finishBtn.disabled = false;
                    finishBtn.textContent = 'Finish';
                }
            }
        } catch (error) {
            console.error('Error completing setup:', error);
            this.showValidationMessage('setup-finish-error',
                'Error saving configuration', 'error');
            
            if (finishBtn) {
                finishBtn.disabled = false;
                finishBtn.textContent = 'Finish';
            }
        }
    }
    
    /**
     * Show validation message
     */
    showValidationMessage(elementId, message, type = 'info') {
        const el = document.getElementById(elementId);
        if (el) {
            el.textContent = message;
            el.className = `setup-validation setup-validation-${type}`;
            el.removeAttribute('hidden');
        }
    }
    
    /**
     * Clear validation message
     */
    clearValidationMessage(elementId) {
        const el = document.getElementById(elementId);
        if (el) {
            el.textContent = '';
            el.setAttribute('hidden', '');
        }
    }
}

// Create singleton instance
const setupWizard = new SetupWizard();

// Export for use in main.js
if (typeof window !== 'undefined') {
    window.setupWizard = setupWizard;
}
