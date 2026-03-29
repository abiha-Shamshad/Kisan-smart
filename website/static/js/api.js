/**
 * API Client for Kisan Smart Backend
 * Handles all HTTP requests to the Flask API with JWT authentication
 */

const API_BASE_URL = '/api/v1';

class APIClient {
  constructor() {
    this.token = localStorage.getItem('auth_token');
  }

  /**
   * Generic request handler with JWT authentication
   */
  async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    // Add JWT token if available
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(API_BASE_URL + endpoint, {
        ...options,
        headers
      });

      const data = await response.json();

      if (!response.ok) {
        // Handle specific error cases
        if (response.status === 401) {
          this.clearToken();
          throw new Error('Session expired. Please login again.');
        }
        throw new Error(data.error?.message || 'Request failed');
      }

      return data;
    } catch (error) {
      if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
        throw new Error('Network error. Please check your connection.');
      }
      throw error;
    }
  }

  /**
   * Authentication Methods
   */
  async register(userData) {
    const response = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
    return response;
  }

  async login(email, password, remember_me = false) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password, remember_me })
    });

    // Store token
    if (response.data && response.data.access_token) {
      this.token = response.data.access_token;
      localStorage.setItem('auth_token', this.token);
    }

    return response;
  }

  async logout() {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } finally {
      this.clearToken();
    }
  }

  async getCurrentUser() {
    return await this.request('/auth/me');
  }

  async forgotPassword(email) {
    return await this.request('/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email })
    });
  }

  async resetPassword(token, newPassword) {
    return await this.request('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, new_password: newPassword })
    });
  }

  async verifyEmail(token) {
    return await this.request(`/auth/verify/${token}`);
  }

  /**
   * Prediction Methods
   */
  async predict(inputData) {
    return await this.request('/predict', {
      method: 'POST',
      body: JSON.stringify(inputData)
    });
  }

  async batchPredict(inputArray) {
    return await this.request('/predict/batch', {
      method: 'POST',
      body: JSON.stringify(inputArray)
    });
  }

  async validateInput(inputData) {
    return await this.request('/predict/validate', {
      method: 'POST',
      body: JSON.stringify(inputData)
    });
  }

  /**
   * History Methods
   */
  async getHistory(page = 1, perPage = 10, filters = {}) {
    const params = new URLSearchParams({
      page,
      per_page: perPage,
      ...filters
    });
    return await this.request(`/history?${params}`);
  }

  async getPredictionDetail(predictionId) {
    return await this.request(`/history/${predictionId}`);
  }

  async deletePrediction(predictionId) {
    return await this.request(`/history/${predictionId}`, {
      method: 'DELETE'
    });
  }

  async exportHistory() {
    const response = await fetch(API_BASE_URL + '/history/export', {
      headers: {
        'Authorization': `Bearer ${this.token}`
      }
    });

    if (!response.ok) {
      throw new Error('Export failed');
    }

    // Download file
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'history.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  }

  async savePrediction(predictionData) {
    return await this.request('/history', {
      method: 'POST',
      body: JSON.stringify(predictionData)
    });
  }

  async getHistoryStats() {
    return await this.request('/history/stats');
  }

  /**
   * Profile Methods
   */
  async getProfile() {
    return await this.request('/profile');
  }

  async updateProfile(profileData) {
    return await this.request('/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData)
    });
  }

  async changePassword(oldPassword, newPassword) {
    return await this.request('/profile/password', {
      method: 'PUT',
      body: JSON.stringify({
        old_password: oldPassword,
        new_password: newPassword
      })
    });
  }

  async deleteAccount() {
    return await this.request('/profile/', {
      method: 'DELETE'
    });
  }

  /**
   * Reference Data Methods
   */
  async getCrops() {
    return await this.request('/reference/crops');
  }

  async getFertilizers() {
    return await this.request('/reference/fertilizers');
  }

  /**
   * Utility Methods
   */
  isAuthenticated() {
    return !!this.token;
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('auth_token');
  }

  getToken() {
    return this.token;
  }
}

// Create global API instance
const api = new APIClient();
