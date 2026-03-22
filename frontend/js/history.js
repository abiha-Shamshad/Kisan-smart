/**
 * History Manager for Kisan Smart
 * Handles prediction history display,filtering, sorting, pagination
 */

const HistoryManager = {
    // State
    allPredictions: [],
    filteredPredictions: [],
    currentPage: 1,
    itemsPerPage: 20,
    totalPages: 1,
    selectedIds: new Set(),
    currentFilters: {},
    currentSort: 'date_desc',
    detailsModal: null,
    deleteModal: null,
    currentDetailId: null,

    /**
     * Initialize history manager
     */
    async init() {
        // Initialize modals
        this.detailsModal = new bootstrap.Modal(document.getElementById('detailsModal'));
        this.deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));

        // Setup event listeners
        this.setupEventListeners();

        // Load history
        await this.loadHistory();
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Search with debounce
        const searchInput = document.getElementById('searchInput');
        let searchTimeout;
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => this.applyFilters(), 300);
        });

        // Date range change
        document.getElementById('dateRange').addEventListener('change', (e) => {
            const customRange = document.getElementById('customDateRange');
            customRange.style.display = e.target.value === 'custom' ? 'flex' : 'none';
        });
    },

    /**
     * Load prediction history
     */
    async loadHistory() {
        const container = document.getElementById('historyTableContainer');

        try {
            // For now, load all predictions (client-side filtering)
            // In production, use server-side pagination
            const response = await api.getHistory(1, 1000);
            this.allPredictions = response.data.predictions || [];
            this.filteredPredictions = [...this.allPredictions];

            this.applySorting();
            this.renderTable();
            this.renderPagination();
            this.updateResultsCount();

        } catch (error) {
            console.error('Failed to load history:', error);
            container.innerHTML = `
        <div class="alert alert-danger m-4">
          <i class="fas fa-exclamation-triangle me-2"></i>
          Failed to load prediction history. Please try again.
        </div>
      `;
        }
    },

    /**
     * Apply filters
     */
    applyFilters() {
        // Get filter values
        const search = document.getElementById('searchInput').value.toLowerCase();
        const dateRange = document.getElementById('dateRange').value;
        const crop = document.getElementById('cropFilter').value;
        const confidence = document.getElementById('confidenceFilter').value;

        // Filter predictions
        this.filteredPredictions = this.allPredictions.filter(pred => {
            // Search filter
            if (search) {
                const matchesCrop = (pred.crop_type || '').toLowerCase().includes(search);
                const matchesFertilizer = (pred.fertilizer_type || '').toLowerCase().includes(search);
                if (!matchesCrop && !matchesFertilizer) return false;
            }

            // Date range filter
            if (dateRange && dateRange !== 'all') {
                if (!this.matchesDateRange(pred.created_at, dateRange)) return false;
            }

            // Crop filter
            if (crop && pred.crop_type !== crop) return false;

            // Confidence filter
            if (confidence) {
                const conf = pred.overall_confidence || 0;
                if (confidence === 'high' && conf < 80) return false;
                if (confidence === 'medium' && (conf < 60 || conf >= 80)) return false;
                if (confidence === 'low' && conf >= 60) return false;
            }

            return true;
        });

        // Update current filters
        this.currentFilters = { search, dateRange, crop, confidence };

        // Reset to page 1
        this.currentPage = 1;

        // Re-render
        this.applySorting();
        this.renderTable();
        this.renderPagination();
        this.updateResultsCount();
        this.renderActiveFilters();
    },

    /**
     * Check if date matches range
     */
    matchesDateRange(dateString, range) {
        const date = new Date(dateString);
        const now = new Date();
        const dayInMs = 24 * 60 * 60 * 1000;

        switch (range) {
            case 'today':
                return date.toDateString() === now.toDateString();
            case '7days':
                return (now - date) <= 7 * dayInMs;
            case '30days':
                return (now - date) <= 30 * dayInMs;
            case '90days':
                return (now - date) <= 90 * dayInMs;
            case 'custom':
                const from = new Date(document.getElementById('dateFrom').value);
                const to = new Date(document.getElementById('dateTo').value);
                return date >= from && date <= to;
            default:
                return true;
        }
    },

    /**
     * Apply date filter (called on date range change)
     */
    applyDateFilter() {
        this.applyFilters();
    },

    /**
     * Clear search
     */
    clearSearch() {
        document.getElementById('searchInput').value = '';
        this.applyFilters();
    },

    /**
     * Apply sorting
     */
    applySorting() {
        const sort = document.getElementById('sortBy').value;
        this.currentSort = sort;

        this.filteredPredictions.sort((a, b) => {
            switch (sort) {
                case 'date_desc':
                    return new Date(b.created_at) - new Date(a.created_at);
                case 'date_asc':
                    return new Date(a.created_at) - new Date(b.created_at);
                case 'confidence_desc':
                    return (b.overall_confidence || 0) - (a.overall_confidence || 0);
                case 'confidence_asc':
                    return (a.overall_confidence || 0) - (b.overall_confidence || 0);
                case 'crop_asc':
                    return (a.crop_type || '').localeCompare(b.crop_type || '');
                default:
                    return 0;
            }
        });

        this.renderTable();
        this.renderPagination();
    },

    /**
     * Render table
     */
    renderTable() {
        const container = document.getElementById('historyTableContainer');

        // Empty state
        if (this.allPredictions.length === 0) {
            container.innerHTML = `
        <div class="empty-state">
          <i class="fas fa-chart-line"></i>
          <h4>No Predictions Yet</h4>
          <p>Get started by creating your first fertilizer recommendation</p>
          <a href="/predict" class="btn btn-primary">
            <i class="fas fa-magic me-2"></i>Make Your First Prediction
          </a>
        </div>
      `;
            return;
        }

        // No results state
        if (this.filteredPredictions.length === 0) {
            container.innerHTML = `
        <div class="no-results">
          <i class="fas fa-search"></i>
          <h5>No Results Found</h5>
          <p>Try adjusting your filters or search terms</p>
          <button class="btn btn-outline-primary" onclick="HistoryManager.clearAllFilters()">
            Clear All Filters
          </button>
        </div>
      `;
            return;
        }

        // Paginate
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageData = this.filteredPredictions.slice(startIndex, endIndex);

        // Render table
        const rows = pageData.map(pred => `
      <tr onclick="HistoryManager.viewDetails('${pred.id}')" class="${this.selectedIds.has(pred.id) ? 'selected' : ''}">
        <td onclick="event.stopPropagation()">
          <input type="checkbox" class="table-checkbox" 
                 ${this.selectedIds.has(pred.id) ? 'checked' : ''}
                 onchange="HistoryManager.toggleSelection('${pred.id}')">
        </td>
        <td>
          <div class="crop-cell">
            <div class="crop-icon">
              <i class="fas fa-seedling"></i>
            </div>
            <span>${pred.crop_type || 'Unknown'}</span>
          </div>
        </td>
        <td>
          <span class="fertilizer-badge">${pred.fertilizer_type || 'N/A'}</span>
        </td>
        <td>${this.formatNumber(pred.quantity || 0)} kg/ha</td>
        <td>
          <span class="confidence-badge ${this.getConfidenceClass(pred.overall_confidence)}">
            ${Math.round(pred.overall_confidence || 0)}%
          </span>
        </td>
        <td>${this.formatDate(pred.created_at)}</td>
        <td onclick="event.stopPropagation()">
          <div class="action-buttons">
            <button class="btn btn-sm btn-outline-primary action-btn" 
                    onclick="HistoryManager.viewDetails('${pred.id}')">
              <i class="fas fa-eye"></i>
            </button>
            <button class="btn btn-sm btn-outline-danger action-btn" 
                    onclick="HistoryManager.deleteSingle('${pred.id}')">
              <i class="fas fa-trash"></i>
            </button>
          </div>
        </td>
      </tr>
    `).join('');

        container.innerHTML = `
      <div class="table-responsive">
        <table class="table history-table">
          <thead>
            <tr>
              <th style="width: 40px;">
                <input type="checkbox" class="table-checkbox" 
                       onchange="HistoryManager.toggleSelectAll(this)">
              </th>
              <th>Crop</th>
              <th>Fertilizer Type</th>
              <th>Quantity</th>
              <th>Confidence</th>
              <th>Date</th>
              <th style="width: 100px;">Actions</th>
            </tr>
          </thead>
          <tbody>
            ${rows}
          </tbody>
        </table>
      </div>
    `;
    },

    /**
     * Render pagination
     */
    renderPagination() {
        this.totalPages = Math.ceil(this.filteredPredictions.length / this.itemsPerPage);
        const container = document.getElementById('paginationContainer');

        if (this.totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        // Calculate page numbers to show
        let pages = [];
        if (this.totalPages <= 7) {
            pages = Array.from({ length: this.totalPages }, (_, i) => i + 1);
        } else {
            if (this.currentPage <= 4) {
                pages = [1, 2, 3, 4, 5, '...', this.totalPages];
            } else if (this.currentPage >= this.totalPages - 3) {
                pages = [1, '...', this.totalPages - 4, this.totalPages - 3, this.totalPages - 2, this.totalPages - 1, this.totalPages];
            } else {
                pages = [1, '...', this.currentPage - 1, this.currentPage, this.currentPage + 1, '...', this.totalPages];
            }
        }

        const pageItems = pages.map(page => {
            if (page === '...') {
                return '<li class="page-item disabled"><span class="page-link">...</span></li>';
            }
            const active = page === this.currentPage ? 'active' : '';
            return `<li class="page-item ${active}">
                <a class="page-link" href="#" onclick="event.preventDefault(); HistoryManager.goToPage(${page})">${page}</a>
              </li>`;
        }).join('');

        const startIndex = (this.currentPage - 1) * this.itemsPerPage + 1;
        const endIndex = Math.min(this.currentPage * this.itemsPerPage, this.filteredPredictions.length);

        container.innerHTML = `
      <div class="pagination-wrapper">
        <div class="pagination-info">
          Showing ${startIndex}-${endIndex} of ${this.filteredPredictions.length}
        </div>
        <nav>
          <ul class="pagination">
            <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
              <a class="page-link" href="#" onclick="event.preventDefault(); HistoryManager.goToPage(1)">
                <i class="fas fa-angle-double-left"></i>
              </a>
            </li>
            <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
              <a class="page-link" href="#" onclick="event.preventDefault(); HistoryManager.goToPage(${this.currentPage - 1})">
                <i class="fas fa-angle-left"></i>
              </a>
            </li>
            ${pageItems}
            <li class="page-item ${this.currentPage === this.totalPages ? 'disabled' : ''}">
              <a class="page-link" href="#" onclick="event.preventDefault(); HistoryManager.goToPage(${this.currentPage + 1})">
                <i class="fas fa-angle-right"></i>
              </a>
            </li>
            <li class="page-item ${this.currentPage === this.totalPages ? 'disabled' : ''}">
              <a class="page-link" href="#" onclick="event.preventDefault(); HistoryManager.goToPage(${this.totalPages})">
                <i class="fas fa-angle-double-right"></i>
              </a>
            </li>
          </ul>
        </nav>
      </div>
    `;
    },

    /**
     * Go to specific page
     */
    goToPage(page) {
        if (page < 1 || page > this.totalPages) return;
        this.currentPage = page;
        this.renderTable();
        this.renderPagination();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    },

    /**
     * Update results count
     */
    updateResultsCount() {
        const elem = document.getElementById('resultsCount');
        if (this.filteredPredictions.length === this.allPredictions.length) {
            elem.textContent = `${this.filteredPredictions.length} predictions`;
        } else {
            elem.textContent = `${this.filteredPredictions.length} of ${this.allPredictions.length} predictions`;
        }
    },

    /**
     * Render active filters
     */
    renderActiveFilters() {
        const container = document.getElementById('activeFilters');
        const filters = [];

        if (this.currentFilters.search) {
            filters.push({ label: `Search: ${this.currentFilters.search}`, key: 'search' });
        }
        if (this.currentFilters.dateRange && this.currentFilters.dateRange !== 'all') {
            const labels = {
                'today': 'Today',
                '7days': 'Last 7 Days',
                '30days': 'Last 30 Days',
                '90days': 'Last 90 Days',
                'custom': 'Custom Range'
            };
            filters.push({ label: `Date: ${labels[this.currentFilters.dateRange]}`, key: 'dateRange' });
        }
        if (this.currentFilters.crop) {
            filters.push({ label: `Crop: ${this.currentFilters.crop}`, key: 'crop' });
        }
        if (this.currentFilters.confidence) {
            filters.push({ label: `Confidence: ${this.currentFilters.confidence}`, key: 'confidence' });
        }

        if (filters.length === 0) {
            container.innerHTML = '';
            return;
        }

        const tags = filters.map(f => `
      <span class="filter-tag">
        ${f.label}
        <button class="remove-filter" onclick="HistoryManager.removeFilter('${f.key}')">
          <i class="fas fa-times"></i>
        </button>
      </span>
    `).join('');

        container.innerHTML = `
      ${tags}
      <a href="#" class="clear-all-filters" onclick="event.preventDefault(); HistoryManager.clearAllFilters()">
        Clear All
      </a>
    `;
    },

    /**
     * Remove single filter
     */
    removeFilter(key) {
        switch (key) {
            case 'search':
                document.getElementById('searchInput').value = '';
                break;
            case 'dateRange':
                document.getElementById('dateRange').value = 'all';
                break;
            case 'crop':
                document.getElementById('cropFilter').value = '';
                break;
            case 'confidence':
                document.getElementById('confidenceFilter').value = '';
                break;
        }
        this.applyFilters();
    },

    /**
     * Clear all filters
     */
    clearAllFilters() {
        document.getElementById('searchInput').value = '';
        document.getElementById('dateRange').value = 'all';
        document.getElementById('cropFilter').value = '';
        document.getElementById('confidenceFilter').value = '';
        document.getElementById('customDateRange').style.display = 'none';
        this.applyFilters();
    },

    /**
     * Toggle selection
     */
    toggleSelection(id) {
        if (this.selectedIds.has(id)) {
            this.selectedIds.delete(id);
        } else {
            this.selectedIds.add(id);
        }
        this.renderTable();
    },

    /**
     * Toggle select all
     */
    toggleSelectAll(checkbox) {
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageData = this.filteredPredictions.slice(startIndex, endIndex);

        if (checkbox.checked) {
            pageData.forEach(pred => this.selectedIds.add(pred.id));
        } else {
            pageData.forEach(pred => this.selectedIds.delete(pred.id));
        }
        this.renderTable();
    },

    /**
     * Export selected
     */
    exportSelected() {
        if (this.selectedIds.size === 0) {
            Toast.warning('Please select predictions to export');
            return;
        }

        const selected = this.allPredictions.filter(p => this.selectedIds.has(p.id));
        ExportManager.exportToCSV(selected);
    },

    /**
     * Delete selected
     */
    deleteSelected() {
        if (this.selectedIds.size === 0) {
            Toast.warning('Please select predictions to delete');
            return;
        }

        const count = this.selectedIds.size;
        document.getElementById('deleteMessage').textContent =
            `Are you sure you want to delete ${count} prediction${count > 1 ? 's' : ''}?`;
        this.deleteModal.show();
    },

    /**
     * Delete single
     */
    deleteSingle(id) {
        this.selectedIds.clear();
        this.selectedIds.add(id);
        document.getElementById('deleteMessage').textContent =
            'Are you sure you want to delete this prediction?';
        this.deleteModal.show();
    },

    /**
     * Confirm delete
     */
    async confirmDelete() {
        const ids = Array.from(this.selectedIds);

        try {
            // Delete each prediction
            await Promise.all(ids.map(id => api.deletePrediction(id)));

            // Remove from local data
            this.allPredictions = this.allPredictions.filter(p => !ids.includes(p.id));
            this.selectedIds.clear();

            // Re-apply filters and render
            this.applyFilters();

            this.deleteModal.hide();
            Toast.success(`Deleted ${ids.length} prediction${ids.length > 1 ? 's' : ''}successfully`);

        } catch (error) {
            console.error('Delete failed:', error);
            Toast.error('Failed to delete predictions. Please try again.');
        }
    },

    /**
     * View prediction details
     */
    async viewDetails(id) {
        this.currentDetailId = id;
        const pred = this.allPredictions.find(p => p.id === id);

        if (!pred) {
            Toast.error('Prediction not found');
            return;
        }

        const content = `
      <div class="details-section">
        <h6>Recommendation Summary</h6>
        <div class="details-grid">
          <div class="detail-item">
            <span class="detail-label">Fertilizer Type</span>
            <span class="detail-value">${pred.fertilizer_type || 'N/A'}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Quantity</span>
            <span class="detail-value">${this.formatNumber(pred.quantity || 0)} kg/ha</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Farm Area</span>
            <span class="detail-value">${pred.farm_area || 'N/A'} hectares</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Confidence</span>
            <span class="detail-value">
              <span class="confidence-badge ${this.getConfidenceClass(pred.overall_confidence)}">
                ${Math.round(pred.overall_confidence || 0)}%
              </span>
            </span>
          </div>
        </div>
      </div>
      
      <div class="details-section">
        <h6>Input Parameters</h6>
        <div class="details-grid">
          <div class="detail-item">
            <span class="detail-label">Crop Type</span>
            <span class="detail-value">${pred.crop_type || 'N/A'}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Nitrogen (N)</span>
            <span class="detail-value">${pred.nitrogen || 0} kg/ha</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Phosphorus (P)</span>
            <span class="detail-value">${pred.phosphorus || 0} kg/ha</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Potassium (K)</span>
            <span class="detail-value">${pred.potassium || 0} kg/ha</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Soil pH</span>
            <span class="detail-value">${pred.ph || 'N/A'}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Moisture</span>
            <span class="detail-value">${pred.moisture || 'N/A'}%</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Temperature</span>
            <span class="detail-value">${pred.temperature || 'N/A'}°C</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Date</span>
            <span class="detail-value">${this.formatDateLong(pred.created_at)}</span>
          </div>
        </div>
      </div>
    `;

        document.getElementById('detailsModalBody').innerHTML = content;
        this.detailsModal.show();
    },

    /**
     * Delete from modal
     */
    deleteFromModal() {
        this.detailsModal.hide();
        if (this.currentDetailId) {
            this.deleteSingle(this.currentDetailId);
        }
    },

    /**
     * Download PDF
     */
    downloadPDF() {
        if (this.currentDetailId) {
            const pred = this.allPredictions.find(p => p.id === this.currentDetailId);
            if (pred) {
                ExportManager.exportToPDF([pred]);
            }
        }
    },

    /**
     * Helper: Get confidence class
     */
    getConfidenceClass(confidence) {
        if (confidence >= 80) return 'confidence-high';
        if (confidence >= 60) return 'confidence-medium';
        return 'confidence-low';
    },

    /**
     * Helper: Format number
     */
    formatNumber(num) {
        return parseFloat(num).toFixed(1);
    },

    /**
     * Helper: Format date
     */
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString();
    },

    /**
     * Helper: Format date (long)
     */
    formatDateLong(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleString();
    }
};
