/**
 * Client-Side Validation Functions for Kisan Smart
 */

const Validators = {
    /**
     * Validate username
     * Rules: 3-20 characters, alphanumeric and underscore only
     */
    validateUsername(username) {
        if (!username || username.length < 3 || username.length > 20) {
            return { valid: false, message: 'Username must be 3-20 characters long' };
        }

        const regex = /^[a-zA-Z0-9_]+$/;
        if (!regex.test(username)) {
            return { valid: false, message: 'Username can only contain letters, numbers, and underscores' };
        }

        return { valid: true };
    },

    /**
     * Validate email address
     */
    validateEmail(email) {
        if (!email) {
            return { valid: false, message: 'Email is required' };
        }

        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!regex.test(email)) {
            return { valid: false, message: 'Please enter a valid email address' };
        }

        return { valid: true };
    },

    /**
     * Validate password strength
     * Returns an object with individual requirement checks
     */
    validatePassword(password) {
        return {
            length: password.length >= 8,
            uppercase: /[A-Z]/.test(password),
            lowercase: /[a-z]/.test(password),
            number: /[0-9]/.test(password),
            special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
        };
    },

    /**
     * Calculate password strength score
     * Returns: 0 (weak), 1 (medium), 2 (strong)
     */
    calculatePasswordStrength(password) {
        if (!password) return 0;

        const checks = this.validatePassword(password);
        const score = Object.values(checks).filter(Boolean).length;

        if (score < 3) return 0; // weak
        if (score < 5) return 1; // medium
        return 2; // strong
    },

    /**
     * Get password strength label and color
     */
    getPasswordStrengthInfo(password) {
        const strength = this.calculatePasswordStrength(password);
        const info = {
            0: { label: 'Weak', color: 'danger', class: 'weak' },
            1: { label: 'Medium', color: 'warning', class: 'medium' },
            2: { label: 'Strong', color: 'success', class: 'strong' }
        };
        return info[strength];
    },

    /**
     * Validate password match
     */
    validatePasswordMatch(password, confirmPassword) {
        if (!confirmPassword) {
            return { valid: false, message: 'Please confirm your password' };
        }

        if (password !== confirmPassword) {
            return { valid: false, message: 'Passwords do not match' };
        }

        return { valid: true };
    },

    /**
     * Validate phone number (optional field)
     */
    validatePhoneNumber(phone) {
        if (!phone) return { valid: true }; // Optional field

        // Remove spaces and dashes
        const cleaned = phone.replace(/[\s-]/g, '');

        // Check if it's a valid phone number (10-15 digits)
        const regex = /^\+?[0-9]{10,15}$/;
        if (!regex.test(cleaned)) {
            return { valid: false, message: 'Please enter a valid phone number' };
        }

        return { valid: true };
    },

    /**
     * Validate required field
     */
    validateRequired(value, fieldName = 'This field') {
        if (!value || (typeof value === 'string' && value.trim() === '')) {
            return { valid: false, message: `${fieldName} is required` };
        }
        return { valid: true };
    },

    /**
     * Validate numeric range for fertilizer inputs
     */
    validateNumericRange(value, min, max, fieldName) {
        const num = parseFloat(value);

        if (isNaN(num)) {
            return { valid: false, message: `${fieldName} must be a number` };
        }

        if (num < min || num > max) {
            return { valid: false, message: `${fieldName} must be between ${min} and ${max}` };
        }

        return { valid: true };
    }
};

/**
 * UI Helper Functions for Form Validation
 */
const ValidationUI = {
    /**
     * Show field error
     */
    showFieldError(fieldId, message) {
        const field = document.getElementById(fieldId);
        if (!field) return;

        field.classList.remove('is-valid');
        field.classList.add('is-invalid');

        // Find or create feedback element
        let feedback = field.parentElement.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            field.parentElement.appendChild(feedback);
        }
        feedback.textContent = message;
        feedback.style.display = 'block';
    },

    /**
     * Show field success
     */
    showFieldSuccess(fieldId) {
        const field = document.getElementById(fieldId);
        if (!field) return;

        field.classList.remove('is-invalid');
        field.classList.add('is-valid');

        // Hide invalid feedback
        const invalidFeedback = field.parentElement.querySelector('.invalid-feedback');
        if (invalidFeedback) {
            invalidFeedback.style.display = 'none';
        }
    },

    /**
     * Clear field feedback
     */
    clearFieldFeedback(fieldId) {
        const field = document.getElementById(fieldId);
        if (!field) return;

        field.classList.remove('is-valid', 'is-invalid');

        const feedback = field.parentElement.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.style.display = 'none';
        }
    },

    /**
     * Clear all form feedback
     */
    clearAllFeedback(formId) {
        const form = document.getElementById(formId);
        if (!form) return;

        form.querySelectorAll('.is-valid, .is-invalid').forEach(field => {
            field.classList.remove('is-valid', 'is-invalid');
        });

        form.querySelectorAll('.invalid-feedback').forEach(feedback => {
            feedback.style.display = 'none';
        });
    }
};
