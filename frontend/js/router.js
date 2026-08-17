/**
 * Client-side View Router with Role-Based Navigation Guards
 */
class Router {
  constructor() {
    this.routes = {
      'landing': { id: 'view-landing', title: 'Home | PulseRoute AI', public: true },
      'login': { id: 'view-login', title: 'Sign In | PulseRoute AI', public: true, guestOnly: true },
      'register': { id: 'view-register', title: 'Sign Up | PulseRoute AI', public: true, guestOnly: true },
      'dashboard': { id: 'view-dashboard', title: 'User Dashboard | PulseRoute AI', authRequired: true },
      'emergency': { id: 'view-emergency', title: 'Emergency Hospital Finder | PulseRoute AI', public: true },
      'hospital-detail': { id: 'view-hospital-detail', title: 'Hospital Details | PulseRoute AI', public: true },
      'profile': { id: 'view-profile', title: 'My Medical Profile | PulseRoute AI', authRequired: true },
      'history': { id: 'view-history', title: 'Search History | PulseRoute AI', authRequired: true },
      'admin': { id: 'view-admin', title: 'Admin System Control | PulseRoute AI', adminRequired: true },
      'error-401': { id: 'view-error-401', title: '401 - Unauthorized | PulseRoute AI', public: true },
      'error-403': { id: 'view-error-403', title: '403 - Forbidden | PulseRoute AI', public: true },
      'error-404': { id: 'view-error-404', title: '404 - Page Not Found | PulseRoute AI', public: true },
      'error-500': { id: 'view-error-500', title: '500 - Server Error | PulseRoute AI', public: true },
    };

    this.currentRoute = null;
    window.addEventListener('hashchange', () => this.handleRouting());
  }

  init() {
    this.handleRouting();
  }

  navigate(routeName, params = null) {
    if (params) {
      window.sessionStorage.setItem('pulseroute_route_params', JSON.stringify(params));
    }
    window.location.hash = `#${routeName}`;
  }

  getRouteParams() {
    try {
      const data = window.sessionStorage.getItem('pulseroute_route_params');
      return data ? JSON.parse(data) : null;
    } catch (e) {
      return null;
    }
  }

  handleRouting() {
    const rawHash = window.location.hash.replace(/^#\/?/, '').trim();
    const routeName = rawHash || 'landing';

    let targetRoute = this.routes[routeName];
    if (!targetRoute) {
      targetRoute = this.routes['error-404'];
      this.navigate('error-404');
      return;
    }

    const isAuth = window.Auth.isAuthenticated();
    const isAdmin = window.Auth.isAdmin();

    // Guard: Auth required
    if (targetRoute.authRequired && !isAuth) {
      window.App.showToast('Please sign in to access this page.', 'warning');
      this.navigate('login');
      return;
    }

    // Guard: Admin required
    if (targetRoute.adminRequired && !isAdmin) {
      window.App.showToast('Access restricted: Administrator role required.', 'error');
      this.navigate('error-403');
      return;
    }

    // Guard: Guest only (e.g. login/register when already logged in)
    if (targetRoute.guestOnly && isAuth) {
      this.navigate(isAdmin ? 'admin' : 'dashboard');
      return;
    }

    this.renderView(routeName, targetRoute);
  }

  renderView(routeName, routeConfig) {
    this.currentRoute = routeName;
    document.title = routeConfig.title;

    // Hide all view sections
    document.querySelectorAll('.app-view').forEach(view => {
      view.classList.remove('active');
    });

    // Show target view
    const targetElement = document.getElementById(routeConfig.id);
    if (targetElement) {
      targetElement.classList.add('active');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Update active nav links
    document.querySelectorAll('.nav-link').forEach(link => {
      const href = link.getAttribute('href') || '';
      if (href.includes(`#${routeName}`)) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });

    // Trigger view-specific lifecycles in App
    if (window.App && typeof window.App.onViewChange === 'function') {
      window.App.onViewChange(routeName, this.getRouteParams());
    }
  }
}

window.Router = new Router();
