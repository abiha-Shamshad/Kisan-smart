/**
 * Prediction Form Handler for Kisan Smart
 * Manages dual slider inputs, validation, and prediction submission
 */

const PredictionForm = {
    // Sample data for different crops
    sampleData: {
        wheat: {
            nitrogen: 45,
            phosphorus: 30,
            potassium: 25,
            ph: 6.8,
            moisture: 65,
            temperature: 22
        },
        rice: {
            nitrogen: 50,
            phosphorus: 35,
            potassium: 30,
            ph: 6.5,
            moisture: 75,
            temperature: 25
        },
        maize: {
            nitrogen: 60,
            phosphorus: 40,
            potassium: 35,
            ph: 6.2,
            moisture: 60,
            temperature: 24
        },
        cotton: {
            nitrogen: 55,
            phosphorus: 38,
            potassium: 32,
            ph: 6.5,
            moisture: 55,
            temperature: 26
        },
        sugarcane: {
            nitrogen: 70,
            phosphorus: 45,
            potassium: 40,
            ph: 6.8,
            moisture: 70,
            temperature: 28
        }
    },

    /**
     * Initialize the form
     */
    init() {
        this.setupDualInputs();
        this.setupFormHandlers();
        this.updateAllStatuses();
    },

    /**
     * Setup dual input synchronization (slider + number)
     */
    setupDualInputs() {
        const parameters = ['nitrogen', 'phosphorus', 'potassium', 'ph', 'moisture', 'temperature'];

        parameters.forEach(param => {
            const slider = document.getElementById(`${param}_slider`);
            const input = document.getElementById(param);

            if (!slider || !input) return;

            // Slider changes update input
            slider.addEventListener('input', () => {
                input.value = slider.value;
                this.updateStatus(param, parseFloat(slider.value));
            });

            // Input changes update slider
            input.addEventListener('input', () => {
                const value = parseFloat(input.value);
                if (!isNaN(value)) {
                    slider.value = value;
                    this.updateStatus(param, value);
                }
            });
        });
    },

    /**
     * Update status indicator for a parameter
     */
    updateStatus(param, value) {
        const statusElem = document.getElementById(`${param}_status`);
        if (!statusElem) return;

        let status, label;

        // Determine status based on parameter and value
        if (param === 'nitrogen' || param === 'phosphorus' || param === 'potassium') {
            // NPK: 0-66 = low, 67-133 = medium, 134+ = high
            if (value < 67) {
                status = 'low';
                label = 'Low';
            } else if (value < 134) {
                status = 'medium';
                label = 'Medium';
            } else {
                status = 'high';
                label = 'High';
            }
        } else if (param === 'ph') {
            // pH: <5.5 = acidic, 5.5-7.5 = neutral, >7.5 = alkaline
            if (value < 5.5) {
                status = 'low';
                label = 'Acidic';
            } else if (value <= 7.5) {
                status = 'high';
                label = 'Neutral';
            } else {
                status = 'medium';
                label = 'Alkaline';
            }
        } else if (param === 'moisture') {
            // Moisture: <40 = low, 40-70 = optimal, >70 = high
            if (value < 40) {
                status = 'low';
                label = 'Low';
            } else if (value <= 70) {
                status = 'high';
                label = 'Optimal';
            } else {
                status = 'medium';
                label = 'High';
            }
        } else if (param === 'temperature') {
            // Temperature: <15 = low, 15-30 = optimal, >30 = high
            if (value < 15) {
                status = 'low';
                label = 'Cold';
            } else if (value <= 30) {
                status = 'high';
                label = 'Optimal';
            } else {
                status = 'medium';
                label = 'Hot';
            }
        }

        // Update status element
        statusElem.className = `status ${status}`;
        statusElem.textContent = label;
    },

    /**
     * Update all status indicators
     */
    updateAllStatuses() {
        const parameters = ['nitrogen', 'phosphorus', 'potassium', 'ph', 'moisture', 'temperature'];
        parameters.forEach(param => {
            const input = document.getElementById(param);
            if (input) {
                this.updateStatus(param, parseFloat(input.value) || 0);
            }
        });
    },

    /**
     * Setup form handlers
     */
    setupFormHandlers() {
        const form = document.getElementById('predictionForm');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleSubmit();
        });
    },

    /**
     * Handle form submission
     */
    async handleSubmit() {
        // Clear previous errors
        ValidationUI.clearAllFeedback('predictionForm');

        // Validate all fields
        if (!this.validateForm()) {
            Toast.error('Please check all required fields');
            return;
        }

        // Collect form data
        const formData = this.collectFormData();

        // Show loading overlay
        this.showLoading(true);

        try {
            // Make API call
            const response = await api.predict(formData);

            // Hide loading
            this.showLoading(false);

            // Redirect to results page with response data
            // Store results in sessionStorage for results page
            sessionStorage.setItem('predictionResults', JSON.stringify(response.data));
            window.location.href = '/results';

        } catch (error) {
            this.showLoading(false);

            // Handle specific errors
            if (error.message.includes('validation')) {
                Toast.error('Invalid input data. Please check your values.');
            } else if (error.message.includes('model')) {
                Toast.error('Prediction service is temporarily unavailable. Please try again later.');
            } else {
                Toast.error(error.message || 'Failed to get recommendation. Please try again.');
            }
        }
    },

    /**
     * Validate form
     */
    validateForm() {
        let isValid = true;

        // Check crop type
        const cropType = document.getElementById('crop_type').value;
        if (!cropType) {
            ValidationUI.showFieldError('crop_type', 'Please select a crop');
            isValid = false;
        }

        // Check farm area
        const farmArea = parseFloat(document.getElementById('farm_area').value);
        if (!farmArea || farmArea < 0.1) {
            ValidationUI.showFieldError('farm_area', 'Farm area must be at least 0.1 hectares');
            isValid = false;
        }

        // Check NPK values (required, 0-200)
        const npkParams = ['nitrogen', 'phosphorus', 'potassium'];
        npkParams.forEach(param => {
            const value = parseFloat(document.getElementById(param).value);
            if (isNaN(value) || value < 0 || value > 200) {
                ValidationUI.showFieldError(param, `${param} must be between 0-200 kg/ha`);
                isValid = false;
            }
        });

        // Check pH (required, 3.0-10.0)
        const ph = parseFloat(document.getElementById('ph').value);
        if (isNaN(ph) || ph < 3.0 || ph > 10.0) {
            ValidationUI.showFieldError('ph', 'pH must be between 3.0-10.0');
            isValid = false;
        }

        // Optional fields (if provided, validate range)
        const moisture = parseFloat(document.getElementById('moisture').value);
        if (moisture && (moisture < 0 || moisture > 100)) {
            ValidationUI.showFieldError('moisture', 'Moisture must be between 0-100%');
            isValid = false;
        }

        const temperature = parseFloat(document.getElementById('temperature').value);
        if (temperature && (temperature < -10 || temperature > 50)) {
            ValidationUI.showFieldError('temperature', 'Temperature must be between -10 to 50°C');
            isValid = false;
        }

        return isValid;
    },

    /**
     * Collect form data
     */
    collectFormData() {
        return {
            crop_type: document.getElementById('crop_type').value,
            farm_area: parseFloat(document.getElementById('farm_area').value),
            nitrogen: parseFloat(document.getElementById('nitrogen').value),
            phosphorus: parseFloat(document.getElementById('phosphorus').value),
            potassium: parseFloat(document.getElementById('potassium').value),
            ph: parseFloat(document.getElementById('ph').value),
            moisture: parseFloat(document.getElementById('moisture').value) || null,
            temperature: parseFloat(document.getElementById('temperature').value) || null
        };
    },

    /**
     * Show/hide loading overlay
     */
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            if (show) {
                overlay.classList.remove('hidden');
            } else {
                overlay.classList.add('hidden');
            }
        }
    }
};

/**
 * Load sample data for selected crop
 */
function loadSampleData() {
    const cropType = document.getElementById('crop_type').value;

    if (!cropType) {
        Toast.info('Please select a crop first');
        return;
    }

    const data = PredictionForm.sampleData[cropType];

    if (!data) {
        Toast.warning('No sample data available for this crop');
        return;
    }

    // Set values
    document.getElementById('nitrogen').value = data.nitrogen;
    document.getElementById('nitrogen_slider').value = data.nitrogen;

    document.getElementById('phosphorus').value = data.phosphorus;
    document.getElementById('phosphorus_slider').value = data.phosphorus;

    document.getElementById('potassium').value = data.potassium;
    document.getElementById('potassium_slider').value = data.potassium;

    document.getElementById('ph').value = data.ph;
    document.getElementById('ph_slider').value = data.ph;

    document.getElementById('moisture').value = data.moisture;
    document.getElementById('moisture_slider').value = data.moisture;

    document.getElementById('temperature').value = data.temperature;
    document.getElementById('temperature_slider').value = data.temperature;

    // Update all statuses
    PredictionForm.updateAllStatuses();

    Toast.success('Sample data loaded successfully!');
}

/**
 * Clear all form fields
 */
function clearForm() {
    const form = document.getElementById('predictionForm');
    form.reset();

    // Reset sliders to default values
    document.getElementById('nitrogen_slider').value = 45;
    document.getElementById('phosphorus_slider').value = 30;
    document.getElementById('potassium_slider').value = 25;
    document.getElementById('ph_slider').value = 6.8;
    document.getElementById('moisture_slider').value = 65;
    document.getElementById('temperature_slider').value = 22;

    // Update all statuses
    PredictionForm.updateAllStatuses();

    // Clear validation feedback
    ValidationUI.clearAllFeedback('predictionForm');

    Toast.info('Form cleared');
}
