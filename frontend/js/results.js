/**
 * Results Dashboard Handler for Kisan Smart
 * Renders prediction results with visualizations
 */

const ResultsDashboard = {
    results: null,

    /**
     * Initialize results dashboard
     */
    init() {
        // Get results from sessionStorage
        const resultsData = sessionStorage.getItem('predictionResults');

        if (!resultsData) {
            this.showError('No prediction data found. Please make a prediction first.');
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 2000);
            return;
        }

        try {
            this.results = JSON.parse(resultsData);
            this.render();
        } catch (error) {
            this.showError('Failed to load results');
            console.error(error);
        }
    },

    /**
     * Render results dashboard
     */
    render() {
        const container = document.getElementById('resultsContainer');

        container.innerHTML = `
      <!-- Hero Section -->
      <div class="recommendation-hero">
        <div class="card text-center">
          <div class="card-body">
            <div class="fertilizer-icon">
              <i class="fas fa-seedling fa-4x"></i>
            </div>
            <h2 class="fertilizer-type">${this.results.fertilizer_type || 'NPK 20-20-20'}</h2>
            <div class="quantity-display">
              <span class="quantity-value">${this.formatNumber(this.results.quantity || 125)}</span>
              <span class="quantity-unit">kg/hectare</span>
            </div>
            <div class="total-quantity">
              <small>Total for your farm: <strong>${this.formatNumber((this.results.quantity || 125) * (this.results.farm_area || 2.5))} kg</strong></small>
            </div>
            <div class="confidence-meter mt-4">
              ${this.renderConfidenceMeter()}
            </div>
          </div>
        </div>
      </div>

      <!-- Detailed Sections -->
      <div class="row mt-4">
        <!-- NPK Breakdown -->
        <div class="col-md-6 mb-4">
          <div class="card h-100">
            <div class="card-header bg-success text-white">
              <h5 class="mb-0"><i class="fas fa-chart-pie me-2"></i>Fertilizer Composition</h5>
            </div>
            <div class="card-body">
              <canvas id="npkChart" width="400" height="300"></canvas>
              ${this.renderNPKDetails()}
            </div>
          </div>
        </div>

        <!-- Application Guidelines -->
        <div class="col-md-6 mb-4">
          <div class="card h-100">
            <div class="card-header bg-info text-white">
              <h5 class="mb-0"><i class="fas fa-clipboard-list me-2"></i>Application Guidelines</h5>
            </div>
            <div class="card-body">
              ${this.renderGuidelines()}
            </div>
          </div>
        </div>
      </div>

      <!-- Confidence Details -->
      <div class="card mb-4">
        <div class="card-header bg-primary text-white">
          <h5 class="mb-0"><i class="fas fa-info-circle me-2"></i>Confidence Details</h5>
        </div>
        <div class="card-body">
          ${this.renderConfidenceDetails()}
        </div>
      </div>

      <!-- Alternative Recommendations -->
      ${this.renderAlternatives()}

      <!-- Input Summary (Collapsible) -->
      <div class="card mb-4">
        <div class="card-header" id="inputSummaryHeader">
          <h5 class="mb-0">
            <button class="btn btn-link w-100 text-start text-decoration-none" type="button" 
                    data-bs-toggle="collapse" data-bs-target="#inputSummary">
              <i class="fas fa-chevron-down me-2"></i>
              View Input Parameters
            </button>
          </h5>
        </div>
        <div id="inputSummary" class="collapse">
          <div class="card-body">
            ${this.renderInputSummary()}
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="action-buttons text-center mb-5">
        <button class="btn btn-success btn-lg" onclick="ResultsDashboard.saveRecommendation()">
          <i class="fas fa-save me-2"></i>Save Recommendation
        </button>
        <button class="btn btn-outline-primary btn-lg" onclick="window.print()">
          <i class="fas fa-print me-2"></i>Print
        </button>
        <button class="btn btn-outline-secondary btn-lg" onclick="ResultsDashboard.downloadPDF()">
          <i class="fas fa-file-pdf me-2"></i>Download PDF
        </button>
        <button class="btn btn-outline-dark btn-lg" onclick="ResultsDashboard.newPrediction()">
          <i class="fas fa-plus me-2"></i>New Prediction
        </button>
      </div>
    `;

        // Render charts
        this.renderNPKChart();
    },

    /**
     * Render confidence meter (SVG circular progress)
     */
    renderConfidenceMeter() {
        const confidence = this.results.confidence || 85;
        const radius = 60;
        const circumference = 2 * Math.PI * radius;
        const offset = circumference - (confidence / 100) * circumference;

        let color, label;
        if (confidence >= 80) {
            color = '#28a745';
            label = 'High Confidence';
        } else if (confidence >= 60) {
            color = '#ffc107';
            label = 'Medium Confidence';
        } else {
            color = '#dc3545';
            label = 'Low Confidence';
        }

        return `
      <div class="progress-circle" data-percent="${confidence}">
        <svg width="140" height="140">
          <circle cx="70" cy="70" r="${radius}" fill="none" stroke="#e9ecef" stroke-width="12"></circle>
          <circle cx="70" cy="70" r="${radius}" fill="none" stroke="${color}" stroke-width="12"
                  stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"
                  stroke-linecap="round" style="transition: stroke-dashoffset 1s ease;">
          </circle>
        </svg>
        <div class="progress-text">
          <span class="percent">${confidence}%</span>
          <span class="label">${label}</span>
        </div>
      </div>
    `;
    },

    /**
     * Render NPK details
     */
    renderNPKDetails() {
        const npk = this.results.npk_ratio || { n: 20, p: 20, k: 20 };

        return `
      <div class="npk-details mt-3">
        <div class="row text-center">
          <div class="col-4">
            <div class="p-3 bg-primary bg-opacity-10 rounded">
              <i class="fas fa-leaf text-primary fa-2x mb-2"></i>
              <h4 class="mb-0">${npk.n}%</h4>
              <small class="text-muted">Nitrogen (N)</small>
            </div>
          </div>
          <div class="col-4">
            <div class="p-3 bg-danger bg-opacity-10 rounded">
              <i class="fas fa-seedling text-danger fa-2x mb-2"></i>
              <h4 class="mb-0">${npk.p}%</h4>
              <small class="text-muted">Phosphorus (P)</small>
            </div>
          </div>
          <div class="col-4">
            <div class="p-3 bg-success bg-opacity-10 rounded">
              <i class="fas fa-tree text-success fa-2x mb-2"></i>
              <h4 class="mb-0">${npk.k}%</h4>
              <small class="text-muted">Potassium (K)</small>
            </div>
          </div>
        </div>
      </div>
    `;
    },

    /**
     * Render application guidelines
     */
    renderGuidelines() {
        return `
      <ul class="list-unstyled">
        <li class="mb-3">
          <i class="fas fa-check-circle text-success me-2"></i>
          <strong>Split Application:</strong> Apply in 2-3 doses for better absorption
        </li>
        <li class="mb-3">
          <i class="fas fa-check-circle text-success me-2"></i>
          <strong>First Dose:</strong> Apply at sowing or planting time
        </li>
        <li class="mb-3">
          <i class="fas fa-check-circle text-success me-2"></i>
          <strong>Second Dose:</strong> Apply after 30-45 days
        </li>
        <li class="mb-3">
          <i class="fas fa-check-circle text-success me-2"></i>
          <strong>Irrigation:</strong> Ensure adequate moisture after application
        </li>
        <li class="mb-3">
          <i class="fas fa-check-circle text-success me-2"></i>
          <strong>Testing:</strong> Re-test soil after 60 days for best results
        </li>
      </ul>
    `;
    },

    /**
     * Render confidence details
     */
    renderConfidenceDetails() {
        const typeConfidence = this.results.type_confidence || 87;
        const quantityConfidence = this.results.quantity_confidence || 82;

        return `
      <div class="row">
        <div class="col-md-4 mb-3">
          <strong>Type Confidence:</strong>
          <div class="progress mt-2" style="height: 25px;">
            <div class="progress-bar bg-success" style="width: ${typeConfidence}%">
              ${typeConfidence}%
            </div>
          </div>
        </div>
        <div class="col-md-4 mb-3">
          <strong>Quantity Confidence:</strong>
          <div class="progress mt-2" style="height: 25px;">
            <div class="progress-bar bg-info" style="width: ${quantityConfidence}%">
              ${quantityConfidence}%
            </div>
          </div>
        </div>
        <div class="col-md-4 mb-3">
          <strong>Overall Confidence:</strong>
          <div class="progress mt-2" style="height: 25px;">
            <div class="progress-bar bg-primary" style="width: ${this.results.confidence}%">
              ${this.results.confidence}%
            </div>
          </div>
        </div>
      </div>
      <p class="mt-3 text-muted">
        <i class="fas fa-info-circle me-2"></i>
        Based on analysis of similar soil conditions and crop requirements. High confidence indicates strong alignment with historical data patterns.
      </p>
    `;
    },

    /**
     * Render alternative recommendations
     */
    renderAlternatives() {
        if (!this.results.alternatives || this.results.alternatives.length === 0) {
            return '';
        }

        const rows = this.results.alternatives.map((alt, index) => `
      <tr>
        <td>${alt.fertilizer_type}</td>
        <td>${this.formatNumber(alt.quantity)} kg/ha</td>
        <td>
          <div class="progress" style="height: 20px;">
            <div class="progress-bar ${alt.confidence >= 80 ? 'bg-success' : 'bg-warning'}" 
                 style="width: ${alt.confidence}%">
              ${alt.confidence}%
            </div>
          </div>
        </td>
        <td>
          <button class="btn btn-sm btn-outline-primary" onclick="ResultsDashboard.viewAlternative(${index})">
            View Details
          </button>
        </td>
      </tr>
    `).join('');

        return `
      <div class="card mb-4">
        <div class="card-header bg-secondary text-white">
          <h5 class="mb-0"><i class="fas fa-list-alt me-2"></i>Alternative Recommendations</h5>
        </div>
        <div class="card-body">
          <table class="table table-hover">
            <thead>
              <tr>
                <th>Fertilizer Type</th>
                <th>Quantity</th>
                <th>Confidence</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              ${rows}
            </tbody>
          </table>
        </div>
      </div>
    `;
    },

    /**
     * Render input summary
     */
    renderInputSummary() {
        const inputs = this.results.inputs || {};

        return `
      <div class="row">
        <div class="col-md-6 mb-3">
          <strong>Crop Type:</strong> ${inputs.crop_type || 'N/A'}
        </div>
        <div class="col-md-6 mb-3">
          <strong>Farm Area:</strong> ${inputs.farm_area || 'N/A'} hectares
        </div>
        <div class="col-md-4 mb-3">
          <strong>Nitrogen (N):</strong> ${inputs.nitrogen || 'N/A'} kg/ha
        </div>
        <div class="col-md-4 mb-3">
          <strong>Phosphorus (P):</strong> ${inputs.phosphorus || 'N/A'} kg/ha
        </div>
        <div class="col-md-4 mb-3">
          <strong>Potassium (K):</strong> ${inputs.potassium || 'N/A'} kg/ha
        </div>
        <div class="col-md-4 mb-3">
          <strong>Soil pH:</strong> ${inputs.ph || 'N/A'}
        </div>
        <div class="col-md-4 mb-3">
          <strong>Moisture:</strong> ${inputs.moisture || 'N/A'}%
        </div>
        <div class="col-md-4 mb-3">
          <strong>Temperature:</strong> ${inputs.temperature || 'N/A'}°C
        </div>
      </div>
    `;
    },

    /**
     * Render NPK chart
     */
    renderNPKChart() {
        const npk = this.results.npk_ratio || { n: 20, p: 20, k: 20 };

        const ctx = document.getElementById('npkChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Nitrogen (N)', 'Phosphorus (P)', 'Potassium (K)'],
                datasets: [{
                    data: [npk.n, npk.p, npk.k],
                    backgroundColor: ['#007bff', '#dc3545', '#28a745'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    title: {
                        display: true,
                        text: `NPK Ratio: ${npk.n}:${npk.p}:${npk.k}`,
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    }
                }
            }
        });
    },

    /**
     * Save recommendation to history
     */
    async saveRecommendation() {
        try {
            const response = await api.savePrediction(this.results);
            Toast.success('Recommendation saved to your history!');
        } catch (error) {
            Toast.error('Failed to save recommendation');
            console.error(error);
        }
    },

    /**
     * Download PDF
     */
    downloadPDF() {
        // For now, use browser print. Can implement jsPDF later
        window.print();
    },

    /**
     * New prediction
     */
    newPrediction() {
        sessionStorage.removeItem('predictionResults');
        window.location.href = '/dashboard';
    },

    /**
     * View alternative
     */
    viewAlternative(index) {
        const alt = this.results.alternatives[index];
        alert(`Alternative: ${alt.fertilizer_type}\nQuantity: ${alt.quantity} kg/ha\nConfidence: ${alt.confidence}%`);
    },

    /**
     * Show error
     */
    showError(message) {
        const container = document.getElementById('resultsContainer');
        container.innerHTML = `
      <div class="alert alert-danger text-center">
        <i class="fas fa-exclamation-triangle fa-3x mb-3"></i>
        <h4>${message}</h4>
        <a href="/dashboard" class="btn btn-primary mt-3">Go to Dashboard</a>
      </div>
    `;
    },

    /**
     * Format number
     */
    formatNumber(num) {
        return parseFloat(num).toFixed(1);
    }
};
