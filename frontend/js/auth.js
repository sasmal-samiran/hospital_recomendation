/**
 * Authentication and Session State Manager
 */
class AuthManager {
  constructor() {
    this.token = localStorage.getItem(window.ENV.TOKEN_STORAGE_KEY) || null;
    this.user = this._loadUser();
    this.listeners = [];
  }

  _loadUser() {
    try {
      const stored = localStorage.getItem(window.ENV.USER_STORAGE_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch (e) {
      return null;
    }
  }

  onChange(callback) {
    this.listeners.push(callback);
  }

  _notify() {
    this.listeners.forEach(cb => cb(this.user, this.isAuthenticated()));
  }

  isAuthenticated() {
    return !!this.token && !!this.user;
  }

  isAdmin() {
    return this.isAuthenticated() && this.user?.role === 'admin';
  }

  getUser() {
    return this.user;
  }

  getToken() {
    return this.token;
  }

  setSession(token, user) {
    this.token = token;
    this.user = user;
    localStorage.setItem(window.ENV.TOKEN_STORAGE_KEY, token);
    localStorage.setItem(window.ENV.USER_STORAGE_KEY, JSON.stringify(user));
    this._notify();
  }

  updateUserProfile(updatedUser) {
    this.user = { ...this.user, ...updatedUser };
    localStorage.setItem(window.ENV.USER_STORAGE_KEY, JSON.stringify(this.user));
    this._notify();
  }

  async login(email, password) {
    const res = await window.API.login(email, password);
    this.setSession(res.access_token, res.user);
    return res;
  }

  async register(data) {
    const res = await window.API.register(data);
    this.setSession(res.access_token, res.user);
    return res;
  }

  logout(redirect = true) {
    this.token = null;
    this.user = null;
    localStorage.removeItem(window.ENV.TOKEN_STORAGE_KEY);
    localStorage.removeItem(window.ENV.USER_STORAGE_KEY);
    this._notify();
    if (redirect) {
      window.Router.navigate('login');
      window.App.showToast('You have been signed out.', 'info');
    }
  }

  async verifySession() {
    if (!this.token) return;
    try {
      const user = await window.API.getMe();
      this.updateUserProfile(user);
    } catch (e) {
      console.warn('Session verification failed:', e);
      this.logout(false);
    }
  }
}

window.Auth = new AuthManager();
