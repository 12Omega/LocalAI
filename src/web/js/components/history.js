/**
 * History View Component
 * 
 * Manages the task execution history interface:
 * - Loads and displays history entries
 * - Provides search and filter functionality
 * - Handles entry selection and detail display
 * - Manages re-run, delete, and export actions
 * - Auto-refreshes when new tasks complete
 */

class HistoryView {
    constructor() {
        this.entries = [];
        this.filteredEntries = [];
        this.selectedEntryId = null;
        this.searchQuery = '';
        this.statusFilter = 'all';
        this.sortOrder = 'newest';
        
        // Virtual scrolling (Task 18.1)
        this.ENTRY_HEIGHT = 100; // Approximate height of entry in pixels
        this.BUFFER_SIZE = 10; // Number of entries to render above/below viewport
        this.visibleStartIndex = 0;
        this.visibleEndIndex = 20;
        this.scrollDebounceTimer = null;
        
        // Lazy loading (Task 18.1)
        this.BATCH_SIZE = 50; // Load 50 entries at a time
        this.currentOffset = 0;
        this.hasMoreEntries = true;
        this.isLoading = false;
        
        // DOM elements
        this.entriesContainer = null;
        this.scrollContainer = null; // Virtual scroll container
        this.searchInput = null;
        this.statusFilterSelect = null;
        this.sortOrderSelect = null;
        this.detailPanel = null;
        this.detailContent = null;
        
        this.initialized = false;
    }
    
    /**
     * Initialize the history view component
     */
    async init() {
        if (this.initialized) return;
        
        console.log('Initializing History View component...');
        
        // Get DOM elements
        this.entriesContainer = document.getElementById('history-entries');
        this.searchInput = document.getElementById('history-search');
        this.statusFilterSelect = document.getElementById('status-filter');
        this.sortOrderSelect = document.getElementById('sort-order');
        this.detailPanel = document.getElementById('history-detail-panel');
        this.detailContent = document.getElementById('history-detail-content');
        
        if (!this.entriesContainer) {
            console.error('History entries container not found');
            return;
        }
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Setup virtual scroll listener (Req 18.1)
        const scrollParent = this.entriesContainer.parentElement;
        if (scrollParent) {
            scrollParent.addEventListener('scroll', () => {
                this.handleVirtualScroll();
            });
        }
        
        // Load initial history (first batch)
        await this.loadHistory();
        
        // Listen for view changes to refresh when history view is shown
        window.addEventListener('view-changed', (e) => {
            if (e.detail.view === 'history') {
                // Reset and reload on view switch
                this.currentOffset = 0;
                this.hasMoreEntries = true;
                this.loadHistory();
            }
        });
        
        // Listen for task completion to auto-refresh
        window.addEventListener('task-completed', () => {
            if (stateManager.get('currentView') === 'history') {
                // Reset and reload when task completes
                this.currentOffset = 0;
                this.hasMoreEntries = true;
                this.loadHistory();
            }
        });
        
        this.initialized = true;
        console.log('History View component initialized');
    }
    
    /**
     * Setup event listeners for UI controls
     */
    setupEventListeners() {
        // Search input
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                this.searchQuery = e.target.value.toLowerCase();
                this.filterAndRenderEntries();
            });
        }
        
        // Status filter
        if (this.statusFilterSelect) {
            this.statusFilterSelect.addEventListener('change', (e) => {
                this.statusFilter = e.target.value;
                this.filterAndRenderEntries();
            });
        }
        
        // Sort order
        if (this.sortOrderSelect) {
            this.sortOrderSelect.addEventListener('change', (e) => {
                this.sortOrder = e.target.value;
                this.filterAndRenderEntries();
            });
        }
        
        // Export button
        const exportBtn = document.getElementById('export-history-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.showExportDialog());
        }
        
        // Clear all button
        const clearAllBtn = document.getElementById('clear-history-btn');
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => this.clearAllHistory());
        }
        
        // Close detail button
        const closeDetailBtn = document.getElementById('close-detail-btn');
        if (closeDetailBtn) {
            closeDetailBtn.addEventListener('click', () => this.closeDetailPanel());
        }
    }
    
    /**
     * Load history entries from backend with lazy loading support
     * 
     * @param {boolean} append - If true, append to existing entries (lazy load)
     * 
     * Requirements: 5.1, 18.1
     */
    async loadHistory(append = false) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        console.log(`Loading history (offset: ${this.currentOffset}, limit: ${this.BATCH_SIZE})...`);
        
        try {
            // Check if eel is available
            if (typeof eel === 'undefined' || !stateManager.get('eelConnected')) {
                console.warn('Backend not connected, showing mock data');
                this.showMockData();
                this.isLoading = false;
                return;
            }
            
            // Call backend with limit and offset for lazy loading (Req 18.1)
            const result = await eel.get_history(this.BATCH_SIZE, this.currentOffset)();
            
            if (result && Array.isArray(result)) {
                if (append) {
                    // Append to existing entries (lazy load)
                    this.entries.push(...result);
                } else {
                    // Replace entries (initial load or refresh)
                    this.entries = result;
                    this.currentOffset = 0;
                }
                
                // Check if there are more entries to load
                this.hasMoreEntries = result.length === this.BATCH_SIZE;
                this.currentOffset += result.length;
                
                console.log(`Loaded ${result.length} history entries (total: ${this.entries.length})`);
                this.filterAndRenderEntries();
            } else {
                console.error('Invalid history data received:', result);
                this.showError('Failed to load history: Invalid data format');
            }
            
        } catch (error) {
            console.error('Error loading history:', error);
            this.showError('Failed to load history: ' + error.message);
        } finally {
            this.isLoading = false;
        }
    }
    
    /**
     * Filter entries based on search and filters, then render
     */
    filterAndRenderEntries() {
        // Start with all entries
        this.filteredEntries = [...this.entries];
        
        // Reset offset and loading state when filter changes
        this.currentOffset = this.entries.length;
        this.hasMoreEntries = true;
        
        // Apply search filter
        if (this.searchQuery) {
            this.filteredEntries = this.filteredEntries.filter(entry => 
                entry.task_description.toLowerCase().includes(this.searchQuery)
            );
        }
        
        // Apply status filter
        if (this.statusFilter !== 'all') {
            this.filteredEntries = this.filteredEntries.filter(entry => 
                entry.status === this.statusFilter
            );
        }
        
        // Apply sort order
        this.sortEntries();
        
        // Render the filtered entries
        this.renderEntries();
    }
    
    /**
     * Sort filtered entries based on sort order
     */
    sortEntries() {
        this.filteredEntries.sort((a, b) => {
            const dateA = new Date(a.timestamp);
            const dateB = new Date(b.timestamp);
            
            if (this.sortOrder === 'newest') {
                return dateB - dateA; // Newest first
            } else {
                return dateA - dateB; // Oldest first
            }
        });
    }
    
    /**
     * Render history entries to the DOM with virtual scrolling
     * 
     * Requirements: 5.1, 18.1
     */
    renderEntries() {
        if (!this.entriesContainer) return;
        
        // Show empty state if no entries
        if (this.filteredEntries.length === 0) {
            this.showEmptyState();
            return;
        }
        
        // For small lists (< 20 entries), render all without virtual scrolling
        if (this.filteredEntries.length < 20) {
            this.renderEntriesDirect();
            return;
        }
        
        // Use virtual scrolling for large lists (Req 18.1)
        this.renderEntriesVirtual();
    }
    
    /**
     * Direct rendering for small lists (no virtual scrolling)
     */
    renderEntriesDirect() {
        // Clear existing entries
        this.entriesContainer.innerHTML = '';
        this.entriesContainer.style.height = 'auto';
        
        // Create entry elements
        this.filteredEntries.forEach(entry => {
            const entryElement = this.createEntryElement(entry);
            this.entriesContainer.appendChild(entryElement);
        });
    }
    
    /**
     * Virtual scrolling rendering for large lists
     * 
     * Only renders visible entries + buffer to improve performance
     * 
     * Requirements: 18.1
     */
    renderEntriesVirtual() {
        // Calculate total height for scroll container
        const totalHeight = this.filteredEntries.length * this.ENTRY_HEIGHT;
        
        // Set container height to enable scrolling
        this.entriesContainer.style.height = `${totalHeight}px`;
        this.entriesContainer.style.position = 'relative';
        
        // Clear existing entries
        this.entriesContainer.innerHTML = '';
        
        // Calculate visible range with buffer
        const startIndex = Math.max(0, this.visibleStartIndex - this.BUFFER_SIZE);
        const endIndex = Math.min(
            this.filteredEntries.length,
            this.visibleEndIndex + this.BUFFER_SIZE
        );
        
        // Create document fragment for batch DOM insertion
        const fragment = document.createDocumentFragment();
        
        // Render only visible entries
        for (let i = startIndex; i < endIndex; i++) {
            const entry = this.filteredEntries[i];
            const entryElement = this.createEntryElement(entry);
            
            // Position absolutely within the scroll container
            entryElement.style.position = 'absolute';
            entryElement.style.top = `${i * this.ENTRY_HEIGHT}px`;
            entryElement.style.left = '0';
            entryElement.style.right = '0';
            
            fragment.appendChild(entryElement);
        }
        
        // Batch append all entries
        this.entriesContainer.appendChild(fragment);
        
        // Show "Load More" button if there are more entries to load
        if (this.hasMoreEntries && endIndex >= this.filteredEntries.length - 5) {
            this.showLoadMoreButton();
        }
    }
    
    /**
     * Handle scroll event for virtual scrolling
     * 
     * Requirements: 18.1
     */
    handleVirtualScroll() {
        // Get parent scroll container (panel-content)
        const scrollParent = this.entriesContainer.parentElement;
        if (!scrollParent) return;
        
        // Debounce scroll events (16ms = 60fps)
        if (this.scrollDebounceTimer) {
            return;
        }
        
        this.scrollDebounceTimer = setTimeout(() => {
            const scrollTop = scrollParent.scrollTop;
            const containerHeight = scrollParent.clientHeight;
            
            // Calculate visible range
            const newStartIndex = Math.floor(scrollTop / this.ENTRY_HEIGHT);
            const newEndIndex = Math.ceil((scrollTop + containerHeight) / this.ENTRY_HEIGHT);
            
            // Only re-render if visible range changed significantly
            if (Math.abs(newStartIndex - this.visibleStartIndex) > 5 ||
                Math.abs(newEndIndex - this.visibleEndIndex) > 5) {
                
                this.visibleStartIndex = newStartIndex;
                this.visibleEndIndex = newEndIndex;
                this.renderEntriesVirtual();
            }
            
            // Check if near bottom for lazy loading
            const scrollBottom = scrollTop + containerHeight;
            const totalHeight = this.filteredEntries.length * this.ENTRY_HEIGHT;
            
            if (scrollBottom > totalHeight - 200 && this.hasMoreEntries && !this.isLoading) {
                console.log('Near bottom, loading more entries...');
                this.loadHistory(true); // Lazy load more entries
            }
            
            this.scrollDebounceTimer = null;
        }, 16); // 60fps
    }
    
    /**
     * Show "Load More" button at the bottom
     * 
     * Requirements: 18.1
     */
    showLoadMoreButton() {
        // Check if button already exists
        let loadMoreBtn = document.getElementById('load-more-history-btn');
        
        if (!loadMoreBtn) {
            loadMoreBtn = document.createElement('button');
            loadMoreBtn.id = 'load-more-history-btn';
            loadMoreBtn.className = 'btn btn-secondary';
            loadMoreBtn.style.position = 'absolute';
            loadMoreBtn.style.left = '50%';
            loadMoreBtn.style.transform = 'translateX(-50%)';
            loadMoreBtn.textContent = this.isLoading ? 'Loading...' : 'Load More';
            loadMoreBtn.disabled = this.isLoading;
            
            loadMoreBtn.addEventListener('click', () => {
                this.loadHistory(true);
            });
            
            this.entriesContainer.appendChild(loadMoreBtn);
        }
        
        // Position at bottom
        const totalHeight = this.filteredEntries.length * this.ENTRY_HEIGHT;
        loadMoreBtn.style.top = `${totalHeight + 10}px`;
        loadMoreBtn.textContent = this.isLoading ? 'Loading...' : 'Load More';
        loadMoreBtn.disabled = this.isLoading;
    }
    
    /**
     * Create HTML element for a history entry
     */
    createEntryElement(entry) {
        const entryDiv = document.createElement('div');
        entryDiv.className = 'history-entry';
        entryDiv.dataset.entryId = entry.entry_id;
        entryDiv.setAttribute('role', 'listitem');
        entryDiv.setAttribute('tabindex', '0');
        
        // Add status class
        entryDiv.classList.add(`status-${entry.status}`);
        
        // Format timestamp
        const timestamp = new Date(entry.timestamp);
        const formattedDate = this.formatTimestamp(timestamp);
        
        // Format duration
        const duration = this.formatDuration(entry.duration_seconds);
        
        // Get status icon and color
        const statusInfo = this.getStatusInfo(entry.status);
        
        // Truncate description if too long
        const description = this.truncateText(entry.task_description, 80);
        
        entryDiv.innerHTML = `
            <div class="entry-status" title="${statusInfo.label}">
                ${statusInfo.icon}
            </div>
            <div class="entry-content">
                <div class="entry-description">${this.escapeHtml(description)}</div>
                <div class="entry-meta">
                    <span class="entry-time" title="${timestamp.toLocaleString()}">${formattedDate}</span>
                    <span class="entry-separator">•</span>
                    <span class="entry-duration">${duration}</span>
                </div>
            </div>
            <div class="entry-actions">
                <button class="icon-button entry-action-btn" data-action="view" title="View details" aria-label="View details">
                    <svg class="icon" viewBox="0 0 24 24" width="18" height="18">
                        <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" fill="currentColor"/>
                        <path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                    </svg>
                </button>
                <button class="icon-button entry-action-btn" data-action="rerun" title="Re-run task" aria-label="Re-run task">
                    <svg class="icon" viewBox="0 0 24 24" width="18" height="18">
                        <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                    </svg>
                </button>
                <button class="icon-button entry-action-btn" data-action="delete" title="Delete entry" aria-label="Delete entry">
                    <svg class="icon" viewBox="0 0 24 24" width="18" height="18">
                        <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                    </svg>
                </button>
            </div>
        `;
        
        // Add click handlers
        const viewBtn = entryDiv.querySelector('[data-action="view"]');
        const rerunBtn = entryDiv.querySelector('[data-action="rerun"]');
        const deleteBtn = entryDiv.querySelector('[data-action="delete"]');
        
        viewBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.viewEntryDetails(entry.entry_id);
        });
        
        rerunBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.rerunTask(entry);
        });
        
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.deleteEntry(entry.entry_id);
        });
        
        // Click on entry itself also shows details
        entryDiv.addEventListener('click', () => {
            this.viewEntryDetails(entry.entry_id);
        });
        
        // Keyboard navigation support
        entryDiv.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.viewEntryDetails(entry.entry_id);
            }
        });
        
        return entryDiv;
    }
    
    /**
     * Get status icon and label
     */
    getStatusInfo(status) {
        const statusMap = {
            'success': {
                icon: '✓',
                label: 'Success',
                color: '#10b981'
            },
            'failed': {
                icon: '✗',
                label: 'Failed',
                color: '#ef4444'
            },
            'cancelled': {
                icon: '⊘',
                label: 'Cancelled',
                color: '#f59e0b'
            }
        };
        
        return statusMap[status] || {
            icon: '?',
            label: 'Unknown',
            color: '#6b7280'
        };
    }
    
    /**
     * Format timestamp to relative time (e.g., "2 hours ago")
     */
    formatTimestamp(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffSec = Math.floor(diffMs / 1000);
        const diffMin = Math.floor(diffSec / 60);
        const diffHour = Math.floor(diffMin / 60);
        const diffDay = Math.floor(diffHour / 24);
        
        if (diffSec < 60) return 'Just now';
        if (diffMin < 60) return `${diffMin} minute${diffMin > 1 ? 's' : ''} ago`;
        if (diffHour < 24) return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`;
        if (diffDay < 7) return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`;
        
        // For older entries, show date
        return date.toLocaleDateString();
    }
    
    /**
     * Format duration in seconds to readable string
     */
    formatDuration(seconds) {
        if (seconds < 1) return '< 1s';
        if (seconds < 60) return `${Math.round(seconds)}s`;
        
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.round(seconds % 60);
        
        if (minutes < 60) {
            return remainingSeconds > 0 
                ? `${minutes}m ${remainingSeconds}s` 
                : `${minutes}m`;
        }
        
        const hours = Math.floor(minutes / 60);
        const remainingMinutes = minutes % 60;
        
        return remainingMinutes > 0
            ? `${hours}h ${remainingMinutes}m`
            : `${hours}h`;
    }
    
    /**
     * Truncate text to specified length
     */
    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength - 3) + '...';
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Show empty state when no entries match filters
     */
    showEmptyState() {
        const hasFilters = this.searchQuery || this.statusFilter !== 'all';
        
        const message = hasFilters 
            ? 'No tasks match your filters'
            : 'No task history yet';
        
        const subMessage = hasFilters
            ? 'Try adjusting your search or filters'
            : 'Completed tasks will appear here';
        
        this.entriesContainer.innerHTML = `
            <div class="empty-state">
                <svg class="empty-icon" viewBox="0 0 24 24" width="48" height="48">
                    <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                </svg>
                <p>${message}</p>
                <p class="empty-subtext">${subMessage}</p>
            </div>
        `;
    }
    
    /**
     * View detailed information for a history entry
     */
    async viewEntryDetails(entryId) {
        console.log('Viewing entry details:', entryId);
        
        try {
            // Highlight selected entry
            document.querySelectorAll('.history-entry').forEach(el => {
                el.classList.toggle('selected', el.dataset.entryId === entryId);
            });
            
            this.selectedEntryId = entryId;
            
            // Get full entry details from backend
            if (typeof eel !== 'undefined' && stateManager.get('eelConnected')) {
                const entry = await eel.get_history_entry(entryId)();
                
                if (entry) {
                    this.renderDetailPanel(entry);
                } else {
                    this.showError('Entry not found');
                }
            } else {
                // Use local data if backend not available
                const entry = this.entries.find(e => e.entry_id === entryId);
                if (entry) {
                    this.renderDetailPanel(entry);
                }
            }
            
        } catch (error) {
            console.error('Error viewing entry details:', error);
            this.showError('Failed to load entry details: ' + error.message);
        }
    }
    
    /**
     * Render the detail panel with entry information
     */
    renderDetailPanel(entry) {
        if (!this.detailPanel || !this.detailContent) return;
        
        const timestamp = new Date(entry.timestamp);
        const statusInfo = this.getStatusInfo(entry.status);
        const duration = this.formatDuration(entry.duration_seconds);
        
        // Build detail HTML
        let detailHtml = `
            <div class="detail-header">
                <div class="detail-status status-${entry.status}">
                    <span class="status-icon">${statusInfo.icon}</span>
                    <span class="status-label">${statusInfo.label}</span>
                </div>
                <div class="detail-meta">
                    <div class="meta-item">
                        <span class="meta-label">Started:</span>
                        <span class="meta-value">${timestamp.toLocaleString()}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Duration:</span>
                        <span class="meta-value">${duration}</span>
                    </div>
                </div>
            </div>
            
            <div class="detail-section">
                <h3 class="section-title">Task Description</h3>
                <div class="task-description-full">
                    ${this.escapeHtml(entry.task_description)}
                </div>
            </div>
        `;
        
        // Add error message if failed
        if (entry.status === 'failed' && entry.error_message) {
            detailHtml += `
                <div class="detail-section">
                    <h3 class="section-title">Error Message</h3>
                    <div class="error-output">
                        ${this.escapeHtml(entry.error_message)}
                    </div>
                </div>
            `;
        }
        
        // Add output
        if (entry.output) {
            detailHtml += `
                <div class="detail-section">
                    <h3 class="section-title">Output</h3>
                    <div class="task-output">
                        <pre>${this.escapeHtml(entry.output)}</pre>
                    </div>
                </div>
            `;
        }
        
        // Add action buttons
        detailHtml += `
            <div class="detail-actions">
                <button id="detail-rerun-btn" class="btn btn-primary">
                    <svg class="btn-icon" viewBox="0 0 24 24" width="18" height="18">
                        <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                    </svg>
                    <span>Re-run Task</span>
                </button>
                <button id="detail-copy-btn" class="btn btn-secondary">
                    <svg class="btn-icon" viewBox="0 0 24 24" width="18" height="18">
                        <path d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                    </svg>
                    <span>Copy Output</span>
                </button>
                <button id="detail-delete-btn" class="btn btn-danger">
                    <svg class="btn-icon" viewBox="0 0 24 24" width="18" height="18">
                        <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                    </svg>
                    <span>Delete</span>
                </button>
            </div>
        `;
        
        this.detailContent.innerHTML = detailHtml;
        
        // Show panel
        this.detailPanel.style.display = 'block';
        
        // Add event listeners for detail actions
        const rerunBtn = document.getElementById('detail-rerun-btn');
        const copyBtn = document.getElementById('detail-copy-btn');
        const deleteBtn = document.getElementById('detail-delete-btn');
        
        if (rerunBtn) {
            rerunBtn.addEventListener('click', () => this.rerunTask(entry));
        }
        
        if (copyBtn) {
            copyBtn.addEventListener('click', () => this.copyOutput(entry.output));
        }
        
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => {
                this.deleteEntry(entry.entry_id);
                this.closeDetailPanel();
            });
        }
    }
    
    /**
     * Close the detail panel
     */
    closeDetailPanel() {
        if (this.detailPanel) {
            this.detailPanel.style.display = 'none';
        }
        
        // Clear selection
        document.querySelectorAll('.history-entry').forEach(el => {
            el.classList.remove('selected');
        });
        
        this.selectedEntryId = null;
    }
    
    /**
     * Re-run a task from history
     */
    async rerunTask(entry) {
        console.log('Re-running task:', entry.entry_id);
        
        // Confirm with user
        const confirmed = confirm(`Re-run this task?\n\n"${this.truncateText(entry.task_description, 100)}"`);
        if (!confirmed) return;
        
        // Announce to screen readers
        if (typeof window.accessibility !== 'undefined' && window.accessibility.announceToScreenReader) {
            window.accessibility.announceToScreenReader('Switching to task view to re-run task', 'polite');
        }
        
        // Switch to task view and populate the task description
        navigateToView('task');
        
        // Wait a bit for view to switch
        setTimeout(() => {
            const taskInput = document.getElementById('task-description');
            if (taskInput) {
                taskInput.value = entry.task_description;
                taskInput.dispatchEvent(new Event('input')); // Trigger character counter
                
                // Focus the run button
                const runBtn = document.getElementById('run-task-btn');
                if (runBtn) {
                    runBtn.focus();
                }
            }
        }, 100);
    }
    
    /**
     * Delete a history entry
     */
    async deleteEntry(entryId) {
        console.log('Deleting entry:', entryId);
        
        // Confirm with user
        const confirmed = confirm('Are you sure you want to delete this history entry?');
        if (!confirmed) return;
        
        try {
            if (typeof eel !== 'undefined' && stateManager.get('eelConnected')) {
                const result = await eel.delete_history_entry(entryId)();
                
                if (result && result.success) {
                    console.log('Entry deleted successfully');
                    
                    // Announce to screen readers
                    if (typeof window.accessibility !== 'undefined' && window.accessibility.announceToScreenReader) {
                        window.accessibility.announceToScreenReader('History entry deleted', 'polite');
                    }
                    
                    // Remove from local array
                    this.entries = this.entries.filter(e => e.entry_id !== entryId);
                    
                    // Re-render
                    this.filterAndRenderEntries();
                    
                    // Show success message
                    this.showSuccess('Entry deleted');
                } else {
                    this.showError(result?.message || 'Failed to delete entry');
                }
            } else {
                // Remove from mock data
                this.entries = this.entries.filter(e => e.entry_id !== entryId);
                this.filterAndRenderEntries();
            }
            
        } catch (error) {
            console.error('Error deleting entry:', error);
            this.showError('Failed to delete entry: ' + error.message);
        }
    }
    
    /**
     * Clear all history entries
     */
    async clearAllHistory() {
        console.log('Clearing all history...');
        
        // Confirm with user
        const confirmed = confirm(
            'Are you sure you want to delete ALL history entries?\n\n' +
            'This action cannot be undone.'
        );
        if (!confirmed) return;
        
        try {
            if (typeof eel !== 'undefined' && stateManager.get('eelConnected')) {
                const result = await eel.clear_all_history()();
                
                if (result && result.success) {
                    console.log('All history cleared');
                    
                    // Announce to screen readers
                    if (typeof window.accessibility !== 'undefined' && window.accessibility.announceToScreenReader) {
                        window.accessibility.announceToScreenReader('All history cleared', 'polite');
                    }
                    
                    // Clear local array
                    this.entries = [];
                    
                    // Re-render
                    this.filterAndRenderEntries();
                    
                    // Show success message
                    this.showSuccess('All history cleared');
                } else {
                    this.showError(result?.message || 'Failed to clear history');
                }
            } else {
                // Clear mock data
                this.entries = [];
                this.filterAndRenderEntries();
            }
            
        } catch (error) {
            console.error('Error clearing history:', error);
            this.showError('Failed to clear history: ' + error.message);
        }
    }
    
    /**
     * Show export dialog and handle export
     */
    async showExportDialog() {
        console.log('Showing export dialog...');
        
        // Simple format selection (in a real implementation, use a proper dialog)
        const format = prompt('Export format:\n1. JSON\n2. CSV\n\nEnter 1 or 2:');
        
        if (!format || (format !== '1' && format !== '2')) {
            return;
        }
        
        const formatType = format === '1' ? 'json' : 'csv';
        
        // Ask for filename
        const defaultFilename = `history_${new Date().toISOString().split('T')[0]}.${formatType}`;
        const filename = prompt(`Export filename:`, defaultFilename);
        
        if (!filename) return;
        
        try {
            if (typeof eel !== 'undefined' && stateManager.get('eelConnected')) {
                const result = await eel.export_history(formatType, filename)();
                
                if (result && result.success) {
                    this.showSuccess(`History exported to ${result.filepath}`);
                } else {
                    this.showError(result?.message || 'Failed to export history');
                }
            } else {
                // Client-side export as fallback
                this.exportClientSide(formatType, filename);
            }
            
        } catch (error) {
            console.error('Error exporting history:', error);
            this.showError('Failed to export history: ' + error.message);
        }
    }
    
    /**
     * Export history on client side (fallback)
     */
    exportClientSide(format, filename) {
        let content;
        let mimeType;
        
        if (format === 'json') {
            content = JSON.stringify(this.entries, null, 2);
            mimeType = 'application/json';
        } else {
            // CSV format
            const headers = ['Timestamp', 'Status', 'Duration', 'Description'];
            const rows = this.entries.map(e => [
                e.timestamp,
                e.status,
                e.duration_seconds,
                e.task_description.replace(/"/g, '""') // Escape quotes
            ]);
            
            content = headers.join(',') + '\n' +
                rows.map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
            mimeType = 'text/csv';
        }
        
        // Create download link
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
        
        this.showSuccess('History exported');
    }
    
    /**
     * Copy output to clipboard
     */
    async copyOutput(output) {
        try {
            await navigator.clipboard.writeText(output);
            this.showSuccess('Output copied to clipboard');
        } catch (error) {
            console.error('Error copying to clipboard:', error);
            this.showError('Failed to copy to clipboard');
        }
    }
    
    /**
     * Show mock data for development/testing
     */
    showMockData() {
        this.entries = [
            {
                entry_id: '1',
                task_description: 'Create a calculator module with unit tests',
                timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
                duration_seconds: 145.5,
                status: 'success',
                output: 'Task completed successfully...',
                error_message: null
            },
            {
                entry_id: '2',
                task_description: 'Refactor authentication system to use JWT tokens',
                timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
                duration_seconds: 320.2,
                status: 'success',
                output: 'Refactoring completed...',
                error_message: null
            },
            {
                entry_id: '3',
                task_description: 'Fix bug in user registration validation',
                timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
                duration_seconds: 89.7,
                status: 'failed',
                output: 'Error occurred during execution...',
                error_message: 'Validation logic incomplete'
            }
        ];
        
        this.filterAndRenderEntries();
    }
    
    /**
     * Show error message
     */
    showError(message) {
        console.error(message);
        // TODO: Use proper toast/notification system
        alert('Error: ' + message);
    }
    
    /**
     * Show success message
     */
    showSuccess(message) {
        console.log(message);
        // TODO: Use proper toast/notification system
        // For now, just log to console
    }
}

// Create global instance
const historyView = new HistoryView();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        historyView.init();
    });
} else {
    historyView.init();
}

// Export for debugging
if (typeof window !== 'undefined') {
    window.historyView = historyView;
}
