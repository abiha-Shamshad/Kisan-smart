/**
 * Authentication State Manager for Kisan Smart
 * Manages user authentication state and UI updates
 */

class AuthManager {
    constructor() {
        this.token = localStorage.getItem('auth_token');
        this.user = null;
        this.isInitialized = false;
    }

    /**
     * Initialize auth manager
     * Call this on page load to check auth state and update UI
     */
    async init() {
        if (this.isInitialized) return;

        if (this.isAuthenticated()) {
            try {
                await this.loadCurrentUser();
            } catch (error) {
                console.error('Failed to load user:', error);
                this.logout();
            }
        }

        this.updateUI();
        this.isInitialized = true;
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!api.getToken();
    }

    /**
     * Load current user data from API
     */
    async loadCurrentUser() {
        if (!this.isAuthenticated()) return null;

        if (this.user) return this.user;

        try {
            const response = await api.getCurrentUser();
            this.user = response.data;
            return this.user;
        } catch (error) {
            this.clearAuth();
            throw error;
        }
    }

    /**
     * Login user
     */
    async login(email, password, rememberMe = false) {
        try {
            const response = await api.login(email, password, rememberMe);
            this.token = response.data.access_token;
            this.user = response.data.user;
            this.updateUI();
            return response;
        } catch (error) {
            throw error;
        }
    }

    /**
     * Logout user
     */
    async logout() {
        try {
            if (this.isAuthenticated()) {
                await api.logout();
            }
        } finally {
            this.clearAuth();
            window.location.href = '/login';
        }
    }

    /**
     * Clear authentication data
     */
    clearAuth() {
        this.token = null;
        this.user = null;
        api.clearToken();
    }

    /**
     * Update UI based on authentication state
     */
    updateUI() {
        const authLinks = document.querySelector('.auth-links');
        const userMenu = document.querySelector('.user-menu');
        const userNameSpan = document.querySelector('.user-name');

        if (this.isAuthenticated() && this.user) {
            // Hide auth links, show user menu
            if (authLinks) authLinks.classList.add('d-none');
            if (userMenu) userMenu.classList.remove('d-none');

            // Update user name
            if (userNameSpan) {
                userNameSpan.textContent = this.user.full_name || this.user.email;
            }
        } else {
            // Show auth links, hide user menu
            if (authLinks) authLinks.classList.remove('d-none');
            if (userMenu) userMenu.classList.add('d-none');
        }
    }

    /**
     * Get current user
     */
    getCurrentUser() {
        return this.user;
    }

    /**
     * Check if user has specific role
     */
    hasRole(roleName) {
        return this.user && this.user.role === roleName;
    }
}

/**
 * Form Helper Functions
 */
const FormHelpers = {
    /**
     * Set button loading state
     */
    setButtonLoading(button, isLoading) {
        if (isLoading) {
            button.disabled = true;
            button.classList.add('btn-loading');
            button.dataset.originalText = button.innerHTML;
            button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
        } else {
            button.disabled = false;
            button.classList.remove('btn-loading');
            if (button.dataset.originalText) {
                button.innerHTML = button.dataset.originalText;
            }
        }
    },

    /**
     * Set form loading state
     */
    setFormLoading(form, isLoading) {
        const inputs = form.querySelectorAll('input, textarea, select, button');
        inputs.forEach(input => {
            input.disabled = isLoading;
        });
    }
};

/**
 * Toast Notification System
 */
const Toast = {
    container: null,

    init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    },

    show(message, type = 'info', duration = 5000) {
        this.init();

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
      <div class="toast-header">
        <strong class="me-auto">${this.getTypeLabel(type)}</strong>
        <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
      </div>
      <div class="toast-body">${message}</div>
    `;

        this.container.appendChild(toast);

        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => toast.remove(), duration);
        }
    },

    success(message, duration) {
        this.show(message, 'success', duration);
    },

    error(message, duration) {
        this.show(message, 'error', duration);
    },

    warning(message, duration) {
        this.show(message, 'warning', duration);
    },

    info(message, duration) {
        this.show(message, 'info', duration);
    },

    getTypeLabel(type) {
        const labels = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Info'
        };
        return labels[type] || 'Notification';
    }
};

// Create global auth manager instance
const auth = new AuthManager();

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    auth.init();
});
