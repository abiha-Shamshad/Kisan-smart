/**
 * Home Dashboard Handler for Kisan Smart
 * Manages stats, recent activity, and charts
 */

const HomeDashboard = {
    stats: null,
    recentPredictions: [],
    charts: {},

    /**
     * Initialize dashboard
     */
    async init() {
        // Load user info
        await this.loadUserInfo();

        // Load stats
        await this.loadStats();

        // Load recent predictions
        await this.loadRecentPredictions();

        // Load charts (if data available)
        if (this.recentPredictions.length > 0) {
            this.initCharts();
        }
    },

    /**
     * Load user info
     */
    async loadUserInfo() {
        try {
            const response = await api.getCurrentUser();
            if (response.data && response.data.username) {
                document.getElementById('userName').textContent = response.data.username;
            }
        } catch (error) {
            console.error('Failed to load user info:', error);
        }
    },

    /**
     * Load dashboard stats
     */
    async loadStats() {
        try {
            const response = await api.getHistoryStats();
            this.stats = response.data;

            this.updateStatCards();
        } catch (error) {
            console.error('Failed to load stats:', error);
            Toast.error('Failed to load dashboard statistics');
        }
    },

    /**
     * Update stat cards with data
     */
    updateStatCards() {
        const stats = this.stats || {};

        // Total Predictions
        this.animateValue(
            document.querySelector('.stat-card-primary .stat-number'),
            0,
            stats.total_predictions || 0,
            1500
        );

        // This Month
        const thisMonthCard = document.querySelector('.stat-card-success');
        this.animateValue(
            thisMonthCard.querySelector('.stat-number'),
            0,
            stats.this_month || 0,
            1500
        );

        // Update trend
        const trend = stats.month_change || 0;
        const trendElem = thisMonthCard.querySelector('.stat-trend');
        if (trend > 0) {
            trendElem.className = 'stat-sublabel stat-trend text-success';
            trendElem.textContent = `+${trend} from last month`;
        } else if (trend < 0) {
            trendElem.className = 'stat-sublabel stat-trend text-danger';
            trendElem.textContent = `${trend} from last month`;
        } else {
            trendElem.className = 'stat-sublabel stat-trend text-muted';
            trendElem.textContent = 'Same as last month';
        }

        // Average Confidence
        this.animateValue(
            document.querySelector('.stat-card-warning .stat-number'),
            0,
            Math.round(stats.avg_confidence || 0),
            1500
        );

        // Crops Analyzed
        this.animateValue(
            document.querySelector('.stat-card-info .stat-number'),
            0,
            stats.unique_crops || 0,
            1500
        );

        // Add animation class
        document.querySelectorAll('.stat-card').forEach(card => {
            card.classList.add('animate');
        });
    },

    /**
     * Animate number count up
     */
    animateValue(element, start, end, duration) {
        if (!element) return;

        const range = end - start;
        const increment = range / (duration / 16); // 60fps
        let current = start;

        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                current = end;
                clearInterval(timer);
            }
            element.textContent = Math.round(current);
        }, 16);
    },

    /**
     * Load recent predictions
     */
    async loadRecentPredictions() {
        const container = document.getElementById('recentActivityContainer');

        try {
            const response = await api.getHistory(1, 5); // First page, 5 items
            this.recentPredictions = response.data.predictions || [];

            if (this.recentPredictions.length === 0) {
                this.showEmptyState(container);
            } else {
                this.renderRecentActivity(container);
            }
        } catch (error) {
            console.error('Failed to load recent predictions:', error);
            container.innerHTML = `
        <div class="alert alert-danger">
          <i class="fas fa-exclamation-triangle me-2"></i>
          Failed to load recent predictions. Please try again.
        </div>
      `;
        }
    },

    /**
     * Render recent activity table
     */
    renderRecentActivity(container) {
        const rows = this.recentPredictions.map(pred => `
      <tr onclick="window.location.href='/history'">
        <td>
          <div class="crop-badge">
            <i class="fas fa-seedling"></i>
            <span>${pred.crop_type || 'Unknown'}</span>
          </div>
        </td>
        <td>${pred.fertilizer_type || 'N/A'}</td>
        <td class="hide-mobile">${pred.quantity || 0} kg/ha</td>
        <td>
          <span class="confidence-badge ${this.getConfidenceClass(pred.overall_confidence)}">
            ${Math.round(pred.overall_confidence || 0)}%
          </span>
        </td>
        <td class="hide-mobile">${this.formatDate(pred.created_at)}</td>
        <td>
          <button class="btn btn-sm btn-outline-primary action-btn" onclick="event.stopPropagation(); HistoryManager.viewDetails('${pred.id}')">
            <i class="fas fa-eye"></i>
          </button>
        </td>
      </tr>
    `).join('');

        container.innerHTML = `
      <div class="table-responsive">
        <table class="table recent-activity-table">
          <thead>
            <tr>
              <th>Crop</th>
              <th>Fertilizer</th>
              <th class="hide-mobile">Quantity</th>
              <th>Confidence</th>
              <th class="hide-mobile">Date</th>
              <th>Actions</th>
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
     * Show empty state
     */
    showEmptyState(container) {
        container.innerHTML = `
      <div class="empty-state">
        <i class="fas fa-chart-line"></i>
        <h5>No predictions yet</h5>
        <p>Get started by creating your first fertilizer recommendation</p>
        <a href="/predict" class="btn btn-primary">
          <i class="fas fa-magic me-2"></i>Make Your First Prediction
        </a>
      </div>
    `;
    },

    /**
     * Get confidence CSS class
     */
    getConfidenceClass(confidence) {
        if (confidence >= 80) return 'confidence-high';
        if (confidence >= 60) return 'confidence-medium';
        return 'confidence-low';
    },

    /**
     * Format date
     */
    formatDate(dateString) {
        if (!dateString) return 'N/A';

        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return 'Today';
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;

        return date.toLocaleDateString();
    },

    /**
     * Initialize charts
     */
    initCharts() {
        if (!this.stats || !this.stats.chart_data) return;

        const chartsSection = document.getElementById('chartsSection');
        chartsSection.style.display = 'block';

        // Predictions over time chart
        this.createTimelineChart();

        // Predictions by crop chart
        this.createCropChart();
    },

    /**
     * Create timeline chart
     */
    createTimelineChart() {
        const ctx = document.getElementById('timelineChart');
        if (!ctx) return;

        const chartData = this.stats.chart_data.timeline || {};

        this.charts.timeline = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels || [],
                datasets: [{
                    label: 'Predictions',
                    data: chartData.values || [],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    },

    /**
     * Create crop chart
     */
    createCropChart() {
        const ctx = document.getElementById('cropChart');
        if (!ctx) return;

        const chartData = this.stats.chart_data.by_crop || {};

        this.charts.crop = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartData.labels || [],
                datasets: [{
                    label: 'Predictions',
                    data: chartData.values || [],
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.8)',
                        'rgba(0, 123, 255, 0.8)',
                        'rgba(255, 193, 7, 0.8)',
                        'rgba(220, 53, 69, 0.8)',
                        'rgba(111, 66, 193, 0.8)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    },

    /**
     * Export all data
     */
    async exportAll() {
        try {
            await api.exportHistory();
            Toast.success('Export started! Your file will download shortly.');
        } catch (error) {
            console.error('Export failed:', error);
            Toast.error('Failed to export data. Please try again.');
        }
    }
};
