/**
 * Environment & Application Configuration
 */
(function() {
  // Determine API base URL:
  // 1. Explicit override via window.ENV_API_URL or window.API_BASE_URL
  // 2. Default to http://localhost:8000/api/v1 (works for Docker and native local development)
  let defaultApiUrl = 'http://localhost:8000/api/v1';

  if (typeof window !== 'undefined' && window.ENV_API_URL) {
    defaultApiUrl = window.ENV_API_URL;
  }

  window.ENV = Object.assign({
    API_BASE_URL: defaultApiUrl,
    APP_NAME: 'PulseRoute AI - Hospital Finder',
    DEFAULT_MAP_CENTER: [22.729189, 88.496305], // Default Kolkata demo coordinates
    DEFAULT_RADIUS_METERS: 5000,
    TOKEN_STORAGE_KEY: 'pulseroute_jwt_token',
    USER_STORAGE_KEY: 'pulseroute_user_profile'
  }, window.ENV || {});
})();
