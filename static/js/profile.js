/**
 * Profile Manager for Kisan Smart
 * Handles profile editing, password change, and account deletion
 */

const ProfileManager = {
    changePasswordModal: null,
    deleteAccountModal: null,

    /**
     * Initialize profile manager
     */
    async init() {
        // Initialize modals
        this.changePasswordModal = new bootstrap.Modal(document.getElementById('changePasswordModal'));
        this.deleteAccountModal = new bootstrap.Modal(document.getElementById('deleteAccountModal'));

        // Load profile data
        await this.loadProfile();

        // Setup event listeners
        this.setupEventListeners();
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Profile form submit
        document.getElementById('profileForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveProfile();
        });

        // Password strength checker
        document.getElementById('newPassword').addEventListener('input', (e) => {
            this.checkPasswordStrength(e.target.value);
        });
    },

    /**
     * Load profile data
     */
    async loadProfile() {
        try {
            const response = await api.getProfile();
            const profile = response.data;

            // Populate form
            document.getElementById('username').value = profile.username || '';
            document.getElementById('email').value = profile.email || '';
            document.getElementById('fullName').value = profile.full_name || '';
            document.getElementById('phone').value = profile.phone || '';
            document.getElementById('farmName').value = profile.farm_name || '';
            document.getElementById('farmLocation').value = profile.farm_location || '';

            // Load preferences
            document.getElementById('emailRecommendations').checked = profile.email_recommendations !== false;
            document.getElementById('weeklySummary').checked = profile.weekly_summary === true;
            document.getElementById('marketingEmails').checked = profile.marketing_emails === true;

        } catch (error) {
            console.error('Failed to load profile:', error);
            Toast.error('Failed to load profile data');
        }
    },

    /**
     * Save profile
     */
    async saveProfile() {
        // Clear previous errors
        ValidationUI.clearAllFeedback('profileForm');

        // Validate
        const email = document.getElementById('email').value;
        if (!Validators.isValidEmail(email)) {
            ValidationUI.showFieldError('email', 'Please enter a valid email address');
            return;
        }

        const phone = document.getElementById('phone').value;
        if (phone && !Validators.isValidPhone(phone)) {
            ValidationUI.showFieldError('phone', 'Please enter a valid phone number');
            return;
        }

        // Collect data
        const profileData = {
            email: email,
            full_name: document.getElementById('fullName').value || null,
            phone: phone || null,
            farm_name: document.getElementById('farmName').value || null,
            farm_location: document.getElementById('farmLocation').value || null
        };

        // Show loading
        const saveBtn = document.getElementById('saveBtn');
        saveBtn.classList.add('loading');
        saveBtn.disabled = true;

        try {
            await api.updateProfile(profileData);

            Toast.success('Profile updated successfully!');

        } catch (error) {
            console.error('Failed to update profile:', error);
            Toast.error(error.message || 'Failed to update profile');
        } finally {
            saveBtn.classList.remove('loading');
            saveBtn.disabled = false;
        }
    },

    /**
     * Save preferences
     */
    async savePreferences() {
        const preferences = {
            email_recommendations: document.getElementById('emailRecommendations').checked,
            weekly_summary: document.getElementById('weeklySummary').checked,
            marketing_emails: document.getElementById('marketingEmails').checked
        };

        try {
            await api.updateProfile(preferences);
            Toast.success('Preferences saved successfully!');
        } catch (error) {
            console.error('Failed to save preferences:', error);
            Toast.error('Failed to save preferences');
        }
    },

    /**
     * Check password strength
     */
    checkPasswordStrength(password) {
        const fill = document.getElementById('passwordStrengthFill');
        const text = document.getElementById('passwordStrengthText');

        const strength = Validators.checkPasswordStrength(password);

        // Remove all classes
        fill.className = 'strength-fill';
        text.className = 'strength-text';

        if (strength.score === 0) {
            text.textContent = '';
            return;
        }

        if (strength.score < 3) {
            fill.classList.add('weak');
            text.classList.add('weak');
            text.textContent = 'Weak password';
        } else if (strength.score < 4) {
            fill.classList.add('medium');
            text.classList.add('medium');
            text.textContent = 'Medium strength';
        } else {
            fill.classList.add('strong');
            text.classList.add('strong');
            text.textContent = 'Strong password';
        }
    },

    /**
     * Change password
     */
    async changePassword() {
        // Clear previous errors
        document.querySelectorAll('#changePasswordForm .invalid-feedback').forEach(el => {
            el.textContent = '';
            el.previousElementSibling.classList.remove('is-invalid');
        });

        // Get values
        const currentPassword = document.getElementById('currentPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        // Validate
        if (!currentPassword) {
            this.showPasswordError('currentPassword', 'Current password is required');
            return;
        }

        if (!newPassword) {
            this.showPasswordError('newPassword', 'New password is required');
            return;
        }

        const strength = Validators.checkPasswordStrength(newPassword);
        if (strength.score < 3) {
            this.showPasswordError('newPassword', 'Password is too weak. ' + strength.feedback);
            return;
        }

        if (newPassword !== confirmPassword) {
            this.showPasswordError('confirmPassword', 'Passwords do not match');
            return;
        }

        try {
            await api.changePassword(currentPassword, newPassword);

            this.changePasswordModal.hide();

            // Clear form
            document.getElementById('changePasswordForm').reset();
            document.getElementById('passwordStrengthFill').className = 'strength-fill';
            document.getElementById('passwordStrengthText').textContent = '';

            Toast.success('Password changed successfully!');

        } catch (error) {
            console.error('Password change failed:', error);

            if (error.message.includes('current password')) {
                this.showPasswordError('currentPassword', 'Current password is incorrect');
            } else {
                Toast.error(error.message || 'Failed to change password');
            }
        }
    },

    /**
     * Show password error
     */
    showPasswordError(fieldId, message) {
        const input = document.getElementById(fieldId);
        const feedback = input.parentElement.querySelector('.invalid-feedback');
        input.classList.add('is-invalid');
        feedback.textContent = message;
    },

    /**
     * Delete account
     */
    async deleteAccount() {
        const confirmText = document.getElementById('deleteConfirmText').value;
        const password = document.getElementById('deletePassword').value;

        // Validate
        if (confirmText !== 'DELETE') {
            Toast.error('Please type DELETE to confirm');
            return;
        }

        if (!password) {
            Toast.error('Please enter your password');
            return;
        }

        try {
            // Verify password first (you might need to add this endpoint)
            await api.deleteAccount(password);

            this.deleteAccountModal.hide();

            Toast.success('Account deleted successfully. Redirecting...');

            // Clear auth and redirect
            setTimeout(() => {
                localStorage.clear();
                window.location.href = '/';
            }, 2000);

        } catch (error) {
            console.error('Account deletion failed:', error);
            Toast.error(error.message || 'Failed to delete account');
        }
    }
};

/**
 * Toggle password visibility
 */
function togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    const button = input.parentElement.querySelector('.password-toggle');
    const icon = button.querySelector('i');

    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}
