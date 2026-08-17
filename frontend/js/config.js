/**
 * Environment & Application Configuration
 */
window.ENV = window.ENV || {
  API_BASE_URL: 'http://localhost:8000/api/v1',
  APP_NAME: 'PulseRoute AI - Hospital Finder',
  DEFAULT_MAP_CENTER: [22.729189, 88.496305], // Default coordinates
  DEFAULT_RADIUS_METERS: 5000,
  TOKEN_STORAGE_KEY: 'pulseroute_jwt_token',
  USER_STORAGE_KEY: 'pulseroute_user_profile'
};
