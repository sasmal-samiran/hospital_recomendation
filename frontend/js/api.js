/**
 * PulseRoute Central API Client
 */
class ApiClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl || window.ENV.API_BASE_URL;
  }

  getAuthToken() {
    return localStorage.getItem(window.ENV.TOKEN_STORAGE_KEY);
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = options.headers || {};

    const token = this.getAuthToken();
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const config = {
      ...options,
      headers
    };

    try {
      const response = await fetch(url, config);

      if (response.status === 401) {
        // If unauthorized/expired token
        if (this.getAuthToken() && !endpoint.includes('/auth/login')) {
          console.warn('Session expired or unauthorized. Logging out.');
          window.Auth.logout(false);
          window.Router.navigate('error-401');
          throw new Error('Your session has expired. Please sign in again.');
        }
      }

      if (response.status === 403) {
        const errJson = await response.json().catch(() => ({}));
        const msg = errJson?.error?.message || 'Access Forbidden: You do not have sufficient permissions.';
        window.Router.navigate('error-403');
        throw new Error(msg);
      }

      if (!response.ok) {
        let errorData;
        try {
          errorData = await response.json();
        } catch (e) {
          errorData = { error: { message: `Server error (${response.status}): ${response.statusText}` } };
        }

        const errorMessage = errorData?.error?.message || 
                             errorData?.detail || 
                             `Request failed with status ${response.status}`;
        
        const err = new Error(errorMessage);
        err.status = response.status;
        err.data = errorData;
        throw err;
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      throw error;
    }
  }

  // ---------------- AUTH APIS ----------------
  async login(email, password) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
  }

  async register(data) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async getMe() {
    return this.request('/auth/me', { method: 'GET' });
  }

  async updateProfile(data) {
    return this.request('/auth/profile', {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  async changePassword(currentPassword, newPassword) {
    return this.request('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword
      })
    });
  }

  // ---------------- HOSPITAL & ROUTE APIS ----------------
  async getNearbyHospitals(lat, lon, radius = 5000, limit = 5) {
    return this.request(`/hospitals/nearby?lat=${lat}&lon=${lon}&radius=${radius}&limit=${limit}`, {
      method: 'GET'
    });
  }

  async calculateRoute(originLat, originLon, destLat, destLon) {
    return this.request('/routes/calculate', {
      method: 'POST',
      body: JSON.stringify({
        origin_lat: originLat,
        origin_lon: originLon,
        dest_lat: destLat,
        dest_lon: destLon
      })
    });
  }

  // ---------------- WEATHER APIS ----------------
  async getCurrentWeather(lat, lon) {
    return this.request(`/weather/current?lat=${lat}&lon=${lon}`, {
      method: 'GET'
    });
  }

  // ---------------- ROAD CONDITION APIS ----------------
  async analyzeRoadUrl(imageUrl) {
    return this.request('/road-condition/analyze-url', {
      method: 'POST',
      body: JSON.stringify({ image_url: imageUrl })
    });
  }

  async analyzeRoadUpload(file) {
    const formData = new FormData();
    formData.append('file', file);
    return this.request('/road-condition/analyze-upload', {
      method: 'POST',
      body: formData
    });
  }

  async estimateRoadCondition(weatherSafety = 90.0, congestionRatio = 1.0) {
    return this.request('/road-condition/estimate', {
      method: 'POST',
      body: JSON.stringify({
        weather_safety: weatherSafety,
        congestion_ratio: congestionRatio
      })
    });
  }

  async getRoadLabels() {
    return this.request('/road-condition/labels', { method: 'GET' });
  }

  // ---------------- RECOMMENDATION ENGINE ----------------
  async getBestHospitalRecommendations(payload) {
    return this.request('/recommendations/best-hospitals', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  // ---------------- HISTORY APIS ----------------
  async getMyHistory(limit = 50) {
    return this.request(`/history/my-history?limit=${limit}`, { method: 'GET' });
  }

  async saveHistory(data) {
    return this.request('/history/save', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async getHistoryDetail(historyId) {
    return this.request(`/history/${historyId}`, { method: 'GET' });
  }

  async deleteHistory(historyId) {
    return this.request(`/history/${historyId}`, { method: 'DELETE' });
  }

  // ---------------- ADMIN APIS ----------------
  async getAdminStats() {
    return this.request('/admin/stats', { method: 'GET' });
  }

  async getAdminUsers() {
    return this.request('/admin/users', { method: 'GET' });
  }

  async updateUserRole(userId, role) {
    return this.request(`/admin/users/${userId}/role`, {
      method: 'PUT',
      body: JSON.stringify({ role })
    });
  }

  async getAdminLogs(limit = 100) {
    return this.request(`/admin/logs?limit=${limit}`, { method: 'GET' });
  }
}

window.API = new ApiClient();
