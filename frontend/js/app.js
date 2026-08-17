/**
 * PulseRoute Main Application Logic & View Controllers
 */
class AppController {
  constructor() {
    this.map = null;
    this.currentRecommendation = null;
    this.selectedHospitalIndex = 0;
    this.toastTimeout = null;
  }

  init() {
    // Initialize map on emergency view container
    this.map = new window.MapController('emergency-map');

    // Subscribe to Auth changes to update UI headers
    window.Auth.onChange(() => this.updateNavigationState());
    this.updateNavigationState();

    // Verify session
    window.Auth.verifySession();

    // Bind Global Events
    this.bindEvents();

    // Initialize Router
    window.Router.init();
  }

  updateNavigationState() {
    const isAuth = window.Auth.isAuthenticated();
    const isAdmin = window.Auth.isAdmin();
    const user = window.Auth.getUser();

    // Toggle guest vs authenticated elements
    document.querySelectorAll('.guest-only').forEach(el => {
      el.style.display = isAuth ? 'none' : '';
    });
    document.querySelectorAll('.auth-only').forEach(el => {
      el.style.display = isAuth ? '' : 'none';
    });
    document.querySelectorAll('.admin-only').forEach(el => {
      el.style.display = isAdmin ? '' : 'none';
    });

    // Update user name and badge in navbar
    const userNameEl = document.getElementById('nav-user-name');
    const userRoleEl = document.getElementById('nav-user-role');
    if (userNameEl && user) {
      userNameEl.textContent = user.full_name || user.email;
    }
    if (userRoleEl && user) {
      userRoleEl.textContent = user.role.toUpperCase();
      userRoleEl.className = `role-badge ${user.role}`;
    }
  }

  bindEvents() {
    // Mobile navigation toggle
    const mobileToggle = document.getElementById('mobile-menu-btn');
    const navMenu = document.getElementById('nav-menu');
    if (mobileToggle && navMenu) {
      mobileToggle.addEventListener('click', () => {
        navMenu.classList.toggle('open');
      });
    }

    // Radius slider sync
    const radiusSlider = document.getElementById('radius-slider');
    const radiusValue = document.getElementById('radius-value');
    if (radiusSlider && radiusValue) {
      radiusSlider.addEventListener('input', (e) => {
        const val = e.target.value;
        radiusValue.textContent = `${(val / 1000).toFixed(1)} km`;
      });
    }

    // Road condition image input switch (URL vs Upload)
    const urlTab = document.getElementById('tab-img-url');
    const uploadTab = document.getElementById('tab-img-upload');
    const urlInputGroup = document.getElementById('group-img-url');
    const uploadInputGroup = document.getElementById('group-img-upload');

    if (urlTab && uploadTab) {
      urlTab.addEventListener('click', () => {
        urlTab.classList.add('active');
        uploadTab.classList.remove('active');
        urlInputGroup.style.display = 'block';
        uploadInputGroup.style.display = 'none';
      });

      uploadTab.addEventListener('click', () => {
        uploadTab.classList.add('active');
        urlTab.classList.remove('active');
        uploadInputGroup.style.display = 'block';
        urlInputGroup.style.display = 'none';
      });
    }

    // File upload preview
    const fileInput = document.getElementById('road-image-file');
    const previewContainer = document.getElementById('road-image-preview');
    if (fileInput && previewContainer) {
      fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = (ev) => {
            previewContainer.innerHTML = `<img src="${ev.target.result}" alt="Road Preview" class="preview-thumb"><button type="button" class="btn-clear-img" onclick="window.App.clearUploadedImage()">&times;</button>`;
            previewContainer.style.display = 'block';
          };
          reader.readAsDataURL(file);
        }
      });
    }

    // Quick GPS location trigger button
    const gpsBtn = document.getElementById('btn-get-gps');
    if (gpsBtn) {
      gpsBtn.addEventListener('click', () => this.detectCurrentLocation());
    }

    // Emergency Form Submit
    const emergencyForm = document.getElementById('emergency-form');
    if (emergencyForm) {
      emergencyForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleEmergencySearch();
      });
    }

    // Auth Forms
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
      loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleLogin();
      });
    }

    const registerForm = document.getElementById('register-form');
    if (registerForm) {
      registerForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleRegister();
      });
    }

    // Profile Form
    const profileForm = document.getElementById('profile-form');
    if (profileForm) {
      profileForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleProfileUpdate();
      });
    }

    // Password Change Form
    const passwordForm = document.getElementById('password-form');
    if (passwordForm) {
      passwordForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handlePasswordChange();
      });
    }
  }

  clearUploadedImage() {
    const fileInput = document.getElementById('road-image-file');
    const previewContainer = document.getElementById('road-image-preview');
    if (fileInput) fileInput.value = '';
    if (previewContainer) {
      previewContainer.innerHTML = '';
      previewContainer.style.display = 'none';
    }
  }

  detectCurrentLocation() {
    const latInput = document.getElementById('origin-lat');
    const lonInput = document.getElementById('origin-lon');
    const gpsStatus = document.getElementById('gps-status');

    if (!navigator.geolocation) {
      this.showToast('Geolocation is not supported by your browser.', 'error');
      return;
    }

    if (gpsStatus) gpsStatus.textContent = 'Acquiring GPS coordinates...';

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        if (latInput) latInput.value = lat.toFixed(6);
        if (lonInput) lonInput.value = lon.toFixed(6);
        if (gpsStatus) gpsStatus.innerHTML = `<span class="text-success"><i class="fa-solid fa-circle-check"></i> GPS Located: (${lat.toFixed(4)}, ${lon.toFixed(4)})</span>`;
        this.showToast('GPS coordinates acquired successfully.', 'success');

        if (this.map) {
          this.map.setUserLocation(lat, lon);
        }
      },
      (err) => {
        console.warn('GPS Error:', err);
        // Default to Kolkata demo coordinate if location permission denied
        const defaultLat = 22.729189;
        const defaultLon = 88.496305;
        if (latInput) latInput.value = defaultLat;
        if (lonInput) lonInput.value = defaultLon;
        if (gpsStatus) gpsStatus.innerHTML = `<span class="text-muted"><i class="fa-solid fa-location-crosshairs"></i> Using Default Demo GPS (${defaultLat}, ${defaultLon})</span>`;
        this.showToast('Location permission denied or unavailable. Using demo coordinates.', 'info');
        
        if (this.map) {
          this.map.setUserLocation(defaultLat, defaultLon);
        }
      },
      { timeout: 8000, enableHighAccuracy: true }
    );
  }

  onViewChange(routeName, params) {
    if (routeName === 'emergency') {
      setTimeout(() => {
        if (!this.map.map) {
          this.map.init();
        } else {
          this.map.map.invalidateSize();
        }
      }, 200);

      // Auto populate coordinates if empty
      const latInput = document.getElementById('origin-lat');
      const lonInput = document.getElementById('origin-lon');
      if (latInput && !latInput.value) latInput.value = '22.729189';
      if (lonInput && !lonInput.value) lonInput.value = '88.496305';
    }

    if (routeName === 'dashboard') {
      this.loadDashboardData();
    }

    if (routeName === 'profile') {
      this.loadProfileView();
    }

    if (routeName === 'history') {
      this.loadHistoryView();
    }

    if (routeName === 'admin') {
      this.loadAdminView();
    }

    if (routeName === 'hospital-detail') {
      this.renderHospitalDetailView(params);
    }
  }

  // ---------------- EMERGENCY RECOMMENDATION ----------------

  async handleEmergencySearch() {
    const lat = parseFloat(document.getElementById('origin-lat')?.value);
    const lon = parseFloat(document.getElementById('origin-lon')?.value);
    const radius = parseFloat(document.getElementById('radius-slider')?.value || 5000);
    const limit = parseInt(document.getElementById('max-hospitals')?.value || 5);
    const roadUrl = document.getElementById('road-image-url')?.value.trim();
    const roadFile = document.getElementById('road-image-file')?.files[0];

    if (isNaN(lat) || isNaN(lon)) {
      this.showToast('Please specify valid latitude and longitude coordinates.', 'error');
      return;
    }

    this.showEmergencyLoading(true);

    try {
      let finalRoadImageUrl = roadUrl || null;

      // If user uploaded an image file, analyze it first
      if (roadFile) {
        this.updateLoadingStep('Analyzing uploaded road surface with CLIP AI...');
        try {
          const roadAnalysis = await window.API.analyzeRoadUpload(roadFile);
          this.showToast(`Road analyzed: ${roadAnalysis.condition_label} (${roadAnalysis.road_score}/100)`, 'info');
        } catch (e) {
          console.warn('Road file analysis skipped:', e);
        }
      }

      this.updateLoadingStep('Searching nearby hospitals and computing live traffic routes...');

      const payload = {
        latitude: lat,
        longitude: lon,
        radius_meters: radius,
        max_hospitals_to_evaluate: limit,
        road_image_url: finalRoadImageUrl
      };

      const response = await window.API.getBestHospitalRecommendations(payload);
      this.currentRecommendation = response;

      this.showEmergencyLoading(false);
      this.renderRecommendationResults(response, lat, lon);

      // Save to history automatically if logged in
      if (window.Auth.isAuthenticated() && response.recommended_hospital) {
        const rec = response.recommended_hospital;
        window.API.saveHistory({
          origin_lat: lat,
          origin_lon: lon,
          radius_meters: radius,
          recommended_hospital_name: rec.hospital.name,
          recommended_hospital_distance_km: rec.route.distance_km,
          recommended_hospital_duration_min: rec.route.duration_minutes,
          composite_score: rec.scores.final_composite_score,
          weather_condition: rec.weather.weather_main,
          road_condition_label: rec.road_condition ? rec.road_condition.condition_label : 'Heuristic',
          total_evaluated: response.total_evaluated,
          raw_result: response
        }).catch(e => console.warn('Could not auto-save history:', e));
      }

      this.showToast(`Found and ranked ${response.total_evaluated} hospital routes!`, 'success');
    } catch (error) {
      this.showEmergencyLoading(false);
      this.showToast(error.message || 'Emergency routing calculation failed.', 'error');
    }
  }

  showEmergencyLoading(isLoading) {
    const loadingCard = document.getElementById('emergency-loading');
    const resultsCard = document.getElementById('emergency-results');
    const submitBtn = document.getElementById('btn-submit-emergency');

    if (loadingCard) loadingCard.style.display = isLoading ? 'block' : 'none';
    if (resultsCard && isLoading) resultsCard.style.display = 'none';
    if (submitBtn) {
      submitBtn.disabled = isLoading;
      submitBtn.innerHTML = isLoading ? '<i class="fa-solid fa-spinner fa-spin"></i> Calculating Optimal Routes...' : '<i class="fa-solid fa-bolt"></i> Find Fastest Emergency Hospital';
    }
  }

  updateLoadingStep(text) {
    const stepEl = document.getElementById('loading-step-text');
    if (stepEl) stepEl.textContent = text;
  }

  renderRecommendationResults(data, originLat, originLon) {
    const resultsCard = document.getElementById('emergency-results');
    const hospitalListEl = document.getElementById('ranked-hospitals-list');
    const topHeroEl = document.getElementById('top-hospital-hero');

    if (!resultsCard || !hospitalListEl) return;
    resultsCard.style.display = 'block';

    const ranked = data.ranked_hospitals || [];
    const topPick = data.recommended_hospital;

    // Render Leaflet map
    if (this.map) {
      this.map.setUserLocation(originLat, originLon, data.radius_meters || 5000);
      this.map.renderRankedHospitals(ranked, originLat, originLon);
    }

    // Top Recommendation Hero
    if (topHeroEl && topPick) {
      const h = topPick.hospital;
      const r = topPick.route;
      const scores = topPick.scores;
      const w = topPick.weather;
      const road = topPick.road_condition;

      topHeroEl.innerHTML = `
        <div class="top-pick-banner">
          <div class="badge-emerald"><i class="fa-solid fa-star"></i> RECOMMENDED #1 EMERGENCY ROUTE</div>
          <div class="top-score">Overall Score: <strong>${scores.final_composite_score.toFixed(1)}/100</strong></div>
        </div>
        <div class="hero-content-grid">
          <div class="hero-main-info">
            <h2 class="hero-hospital-name">${h.name}</h2>
            <p class="hero-address"><i class="fa-solid fa-location-dot"></i> ${h.formatted_address || 'Address provided via map pin'}</p>
            
            <div class="hero-pills">
              <span class="pill pill-time"><i class="fa-solid fa-clock"></i> ETA: ${r.duration_minutes.toFixed(1)} mins</span>
              <span class="pill pill-distance"><i class="fa-solid fa-route"></i> Distance: ${r.distance_km.toFixed(2)} km</span>
              <span class="pill pill-traffic"><i class="fa-solid fa-car"></i> Congestion: ${r.congestion_ratio.toFixed(2)}x</span>
              <span class="pill pill-weather"><i class="fa-solid fa-cloud-sun"></i> Weather: ${w.weather_main} (${w.temperature_celsius}°C)</span>
            </div>

            <p class="hero-notes"><i class="fa-solid fa-circle-info"></i> ${topPick.recommendation_notes}</p>
          </div>

          <div class="hero-score-breakdown">
            <h4>Decision Factors</h4>
            <div class="score-bar-row">
              <span>Arrival Time (ETA)</span>
              <div class="progress-track"><div class="progress-fill emerald" style="width: ${scores.duration_score}%"></div></div>
              <span>${scores.duration_score.toFixed(0)}%</span>
            </div>
            <div class="score-bar-row">
              <span>Traffic Free Flow</span>
              <div class="progress-track"><div class="progress-fill teal" style="width: ${scores.congestion_score}%"></div></div>
              <span>${scores.congestion_score.toFixed(0)}%</span>
            </div>
            <div class="score-bar-row">
              <span>Road Quality Score</span>
              <div class="progress-track"><div class="progress-fill cyan" style="width: ${scores.road_condition_score}%"></div></div>
              <span>${scores.road_condition_score.toFixed(0)}%</span>
            </div>
            <div class="score-bar-row">
              <span>Weather Safety</span>
              <div class="progress-track"><div class="progress-fill blue" style="width: ${scores.weather_safety_score}%"></div></div>
              <span>${scores.weather_safety_score.toFixed(0)}%</span>
            </div>

            <div class="hero-actions">
              <button class="btn btn-primary" onclick="window.App.openHospitalDetails(0)">
                <i class="fa-solid fa-circle-info"></i> Full Details & Navigation
              </button>
              <a href="https://www.google.com/maps/dir/?api=1&destination=${h.lat},${h.lon}" target="_blank" class="btn btn-secondary">
                <i class="fa-solid fa-diamond-turn-right"></i> Google Maps
              </a>
            </div>
          </div>
        </div>
      `;
    }

    // Other ranked candidates
    hospitalListEl.innerHTML = ranked.map((item, idx) => {
      const h = item.hospital;
      const r = item.route;
      const scores = item.scores;
      const isTop = idx === 0;

      return `
        <div class="ranked-card ${isTop ? 'selected' : ''}" onclick="window.App.selectHospital(${idx})">
          <div class="rank-badge ${isTop ? 'rank-1' : ''}">#${item.rank}</div>
          <div class="ranked-card-info">
            <h4>${h.name}</h4>
            <p class="ranked-address"><i class="fa-solid fa-location-dot"></i> ${h.formatted_address || 'Address on map'}</p>
            <div class="ranked-tags">
              <span><i class="fa-solid fa-clock"></i> ${r.duration_minutes.toFixed(1)} min</span>
              <span><i class="fa-solid fa-road"></i> ${r.distance_km.toFixed(2)} km</span>
              <span><i class="fa-solid fa-shield-halved"></i> Score: <strong>${scores.final_composite_score.toFixed(1)}</strong></span>
            </div>
          </div>
          <button class="btn-inspect" onclick="event.stopPropagation(); window.App.openHospitalDetails(${idx})">
            <i class="fa-solid fa-chevron-right"></i>
          </button>
        </div>
      `;
    }).join('');

    resultsCard.scrollIntoView({ behavior: 'smooth' });
  }

  selectHospital(index) {
    if (!this.currentRecommendation || !this.currentRecommendation.ranked_hospitals) return;
    this.selectedHospitalIndex = index;
    const ranked = this.currentRecommendation.ranked_hospitals;

    // Highlight on map
    if (this.map) {
      this.map.highlightRoute(index, ranked);
    }

    // Highlight card
    document.querySelectorAll('.ranked-card').forEach((card, i) => {
      if (i === index) card.classList.add('selected');
      else card.classList.remove('selected');
    });
  }

  openHospitalDetails(index) {
    if (!this.currentRecommendation || !this.currentRecommendation.ranked_hospitals) return;
    const hospitalData = this.currentRecommendation.ranked_hospitals[index];
    window.Router.navigate('hospital-detail', hospitalData);
  }

  renderHospitalDetailView(data) {
    const container = document.getElementById('hospital-detail-content');
    if (!container || !data) {
      if (container) container.innerHTML = `<div class="empty-state"><p>No hospital selected. Please perform an emergency search first.</p><button class="btn btn-primary" onclick="window.Router.navigate('emergency')">Go to Emergency Finder</button></div>`;
      return;
    }

    const h = data.hospital;
    const r = data.route;
    const scores = data.scores;
    const w = data.weather;
    const road = data.road_condition;

    container.innerHTML = `
      <div class="detail-hero-header">
        <div>
          <span class="badge-emerald"><i class="fa-solid fa-hospital"></i> RANK #${data.rank} HOSPITAL</span>
          <h2>${h.name}</h2>
          <p class="text-muted"><i class="fa-solid fa-location-dot"></i> ${h.formatted_address || 'Address provided via GPS coordinates'}</p>
        </div>
        <div class="detail-actions">
          <a href="https://www.google.com/maps/dir/?api=1&destination=${h.lat},${h.lon}" target="_blank" class="btn btn-primary">
            <i class="fa-solid fa-diamond-turn-right"></i> Start Navigation
          </a>
          <button class="btn btn-secondary" onclick="window.Router.navigate('emergency')">
            <i class="fa-solid fa-arrow-left"></i> Back to Results
          </button>
        </div>
      </div>

      <div class="detail-grid">
        <div class="detail-card">
          <h3><i class="fa-solid fa-gauge-high"></i> Route & Traffic Metrics</h3>
          <div class="stat-list">
            <div class="stat-row"><span>Estimated Travel Duration</span><strong>${r.duration_minutes.toFixed(1)} minutes</strong></div>
            <div class="stat-row"><span>Free Flow Duration</span><strong>${r.static_duration_minutes.toFixed(1)} minutes</strong></div>
            <div class="stat-row"><span>Route Distance</span><strong>${r.distance_km.toFixed(2)} km (${r.distance_meters.toFixed(0)} m)</strong></div>
            <div class="stat-row"><span>Traffic Congestion Ratio</span><strong>${r.congestion_ratio.toFixed(2)}x ${r.congestion_ratio > 1.3 ? '<span class="text-warning">(Congested)</span>' : '<span class="text-success">(Smooth)</span>'}</strong></div>
          </div>
        </div>

        <div class="detail-card">
          <h3><i class="fa-solid fa-cloud-sun-rain"></i> Live Weather Hazards</h3>
          <div class="stat-list">
            <div class="stat-row"><span>Current Weather</span><strong>${w.weather_main} (${w.weather_description})</strong></div>
            <div class="stat-row"><span>Temperature</span><strong>${w.temperature_celsius}°C</strong></div>
            <div class="stat-row"><span>Visibility</span><strong>${(w.visibility_meters / 1000).toFixed(1)} km</strong></div>
            <div class="stat-row"><span>Wind Speed</span><strong>${w.wind_speed_mps} m/s</strong></div>
            <div class="stat-row"><span>Weather Safety Score</span><strong>${w.safety_penalty_score.toFixed(1)} / 100</strong></div>
          </div>
        </div>

        <div class="detail-card">
          <h3><i class="fa-solid fa-road"></i> Road Condition Assessment</h3>
          <div class="stat-list">
            <div class="stat-row"><span>Surface Quality</span><strong>${road ? road.condition_label : 'Assessed Clear'}</strong></div>
            <div class="stat-row"><span>Condition Category</span><strong>${road ? road.category : 'Excellent'}</strong></div>
            <div class="stat-row"><span>Road Quality Score</span><strong>${road ? road.road_score : 95} / 100</strong></div>
            <div class="stat-row"><span>Vision Confidence</span><strong>${road ? road.confidence_percent : 90}%</strong></div>
          </div>
        </div>

        <div class="detail-card">
          <h3><i class="fa-solid fa-brain"></i> Recommendation Decision Analysis</h3>
          <p class="notes-box">${data.recommendation_notes}</p>
          <div class="final-score-box">
            <span>Composite Emergency Suitability Score</span>
            <h2>${scores.final_composite_score.toFixed(1)} / 100</h2>
          </div>
        </div>
      </div>
    `;
  }

  // ---------------- AUTH FLOWS ----------------

  async handleLogin() {
    const email = document.getElementById('login-email')?.value.trim();
    const password = document.getElementById('login-password')?.value;

    if (!email || !password) {
      this.showToast('Please enter both email and password.', 'error');
      return;
    }

    const btn = document.getElementById('btn-login-submit');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Signing in...';
    }

    try {
      const res = await window.Auth.login(email, password);
      this.showToast(`Welcome back, ${res.user.full_name}!`, 'success');
      window.Router.navigate(res.user.role === 'admin' ? 'admin' : 'dashboard');
    } catch (err) {
      this.showToast(err.message || 'Login failed.', 'error');
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = 'Sign In';
      }
    }
  }

  async handleRegister() {
    const email = document.getElementById('reg-email')?.value.trim();
    const password = document.getElementById('reg-password')?.value;
    const fullName = document.getElementById('reg-name')?.value.trim();
    const bloodGroup = document.getElementById('reg-blood')?.value;
    const emergencyContact = document.getElementById('reg-contact')?.value.trim();
    const phone = document.getElementById('reg-phone')?.value.trim();

    if (!email || !password || !fullName) {
      this.showToast('Please fill in all required fields.', 'error');
      return;
    }

    const btn = document.getElementById('btn-register-submit');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Creating Account...';
    }

    try {
      const res = await window.Auth.register({
        email,
        password,
        full_name: fullName,
        blood_group: bloodGroup || null,
        emergency_contact: emergencyContact || null,
        phone_number: phone || null
      });
      this.showToast('Registration successful! Welcome to PulseRoute AI.', 'success');
      window.Router.navigate('dashboard');
    } catch (err) {
      this.showToast(err.message || 'Registration failed.', 'error');
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = 'Create Account';
      }
    }
  }

  // ---------------- USER DASHBOARD ----------------

  async loadDashboardData() {
    const user = window.Auth.getUser();
    if (!user) return;

    const welcomeEl = document.getElementById('dash-welcome-name');
    const bloodEl = document.getElementById('dash-blood-group');
    const contactEl = document.getElementById('dash-emergency-contact');

    if (welcomeEl) welcomeEl.textContent = user.full_name || user.email;
    if (bloodEl) bloodEl.textContent = user.blood_group || 'Not specified';
    if (contactEl) contactEl.textContent = user.emergency_contact || 'None set';

    // Fetch recent searches
    const recentContainer = document.getElementById('dash-recent-searches');
    if (recentContainer) {
      recentContainer.innerHTML = '<div class="loading-spinner"><i class="fa-solid fa-spinner fa-spin"></i> Loading recent activity...</div>';
      try {
        const historyRes = await window.API.getMyHistory(3);
        if (historyRes.items && historyRes.items.length > 0) {
          recentContainer.innerHTML = historyRes.items.map(item => `
            <div class="recent-item">
              <div>
                <strong>${item.recommended_hospital_name}</strong>
                <p class="text-muted"><i class="fa-solid fa-calendar"></i> ${new Date(item.timestamp).toLocaleString()} &bull; Score: ${item.composite_score.toFixed(1)}/100</p>
              </div>
              <button class="btn btn-sm btn-secondary" onclick="window.App.loadPastRecommendation(${item.id})">
                Inspect
              </button>
            </div>
          `).join('');
        } else {
          recentContainer.innerHTML = '<p class="text-muted">No emergency searches yet. Click "Find Emergency Hospital" to get started.</p>';
        }
      } catch (e) {
        recentContainer.innerHTML = '<p class="text-muted">Could not load recent searches.</p>';
      }
    }

    // Fetch live local weather widget
    const weatherContainer = document.getElementById('dash-weather-widget');
    if (weatherContainer) {
      try {
        const w = await window.API.getCurrentWeather(22.729189, 88.496305);
        weatherContainer.innerHTML = `
          <div class="weather-widget-card">
            <div class="weather-icon"><i class="fa-solid fa-cloud-sun"></i></div>
            <div>
              <h3>${w.temperature_celsius}°C</h3>
              <p>${w.weather_main} &bull; Safety ${w.safety_penalty_score}/100</p>
            </div>
          </div>
        `;
      } catch (e) {
        weatherContainer.innerHTML = '<p class="text-muted">Weather unavailable.</p>';
      }
    }
  }

  // ---------------- PROFILE VIEW ----------------

  async loadProfileView() {
    const user = window.Auth.getUser();
    if (!user) return;

    const emailEl = document.getElementById('prof-email');
    const nameInput = document.getElementById('prof-name');
    const bloodInput = document.getElementById('prof-blood');
    const contactInput = document.getElementById('prof-contact');
    const phoneInput = document.getElementById('prof-phone');
    const roleBadge = document.getElementById('prof-role');

    if (emailEl) emailEl.value = user.email;
    if (nameInput) nameInput.value = user.full_name || '';
    if (bloodInput) bloodInput.value = user.blood_group || '';
    if (contactInput) contactInput.value = user.emergency_contact || '';
    if (phoneInput) phoneInput.value = user.phone_number || '';
    if (roleBadge) {
      roleBadge.textContent = user.role.toUpperCase();
      roleBadge.className = `role-badge ${user.role}`;
    }
  }

  async handleProfileUpdate() {
    const fullName = document.getElementById('prof-name')?.value.trim();
    const bloodGroup = document.getElementById('prof-blood')?.value;
    const emergencyContact = document.getElementById('prof-contact')?.value.trim();
    const phone = document.getElementById('prof-phone')?.value.trim();

    try {
      const updated = await window.API.updateProfile({
        full_name: fullName,
        blood_group: bloodGroup,
        emergency_contact: emergencyContact,
        phone_number: phone
      });
      window.Auth.updateUserProfile(updated);
      this.showToast('Profile updated successfully.', 'success');
    } catch (e) {
      this.showToast(e.message || 'Failed to update profile.', 'error');
    }
  }

  async handlePasswordChange() {
    const curr = document.getElementById('pass-current')?.value;
    const newPass = document.getElementById('pass-new')?.value;

    if (!curr || !newPass) {
      this.showToast('Please provide both current and new password.', 'error');
      return;
    }

    try {
      await window.API.changePassword(curr, newPass);
      this.showToast('Password changed successfully.', 'success');
      document.getElementById('password-form')?.reset();
    } catch (e) {
      this.showToast(e.message || 'Failed to change password.', 'error');
    }
  }

  // ---------------- HISTORY VIEW ----------------

  async loadHistoryView() {
    const container = document.getElementById('history-table-body');
    if (!container) return;

    container.innerHTML = '<tr><td colspan="7" class="text-center py-4"><i class="fa-solid fa-spinner fa-spin"></i> Loading search history...</td></tr>';

    try {
      const res = await window.API.getMyHistory(50);
      const items = res.items || [];

      if (items.length === 0) {
        container.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">No emergency recommendation records found.</td></tr>';
        return;
      }

      container.innerHTML = items.map(item => `
        <tr>
          <td>#${item.id}</td>
          <td>${new Date(item.timestamp).toLocaleString()}</td>
          <td><strong>${item.recommended_hospital_name}</strong></td>
          <td>${item.recommended_hospital_duration_min ? item.recommended_hospital_duration_min.toFixed(1) + ' min' : '--'}</td>
          <td><span class="badge-score">${item.composite_score.toFixed(1)}/100</span></td>
          <td>${item.weather_condition || 'Clear'}</td>
          <td>
            <button class="btn btn-sm btn-primary" onclick="window.App.loadPastRecommendation(${item.id})">
              <i class="fa-solid fa-eye"></i> View
            </button>
            <button class="btn btn-sm btn-danger" onclick="window.App.deleteHistoryItem(${item.id})">
              <i class="fa-solid fa-trash"></i>
            </button>
          </td>
        </tr>
      `).join('');
    } catch (e) {
      container.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-danger">Error loading history: ${e.message}</td></tr>`;
    }
  }

  async loadPastRecommendation(id) {
    try {
      const record = await window.API.getHistoryDetail(id);
      if (record.raw_result && record.raw_result.ranked_hospitals) {
        this.currentRecommendation = record.raw_result;
        window.Router.navigate('emergency');
        setTimeout(() => {
          this.renderRecommendationResults(record.raw_result, record.origin_lat, record.origin_lon);
        }, 300);
      } else {
        this.showToast('Stored recommendation data is incomplete.', 'warning');
      }
    } catch (e) {
      this.showToast('Could not load history record details.', 'error');
    }
  }

  async deleteHistoryItem(id) {
    if (!confirm('Are you sure you want to remove this recommendation record?')) return;
    try {
      await window.API.deleteHistory(id);
      this.showToast('Record deleted.', 'success');
      this.loadHistoryView();
    } catch (e) {
      this.showToast(e.message || 'Could not delete record.', 'error');
    }
  }

  // ---------------- ADMIN VIEW ----------------

  async loadAdminView() {
    // Load Stats
    try {
      const stats = await window.API.getAdminStats();
      document.getElementById('stat-total-users').textContent = stats.total_users;
      document.getElementById('stat-total-admins').textContent = stats.total_admins;
      document.getElementById('stat-total-queries').textContent = stats.total_recommendations;
      document.getElementById('stat-avg-score').textContent = `${stats.average_composite_score}/100`;
    } catch (e) {
      console.warn('Admin stats error:', e);
    }

    // Load Users
    const usersTable = document.getElementById('admin-users-table');
    if (usersTable) {
      usersTable.innerHTML = '<tr><td colspan="6" class="text-center"><i class="fa-solid fa-spinner fa-spin"></i> Loading users...</td></tr>';
      try {
        const res = await window.API.getAdminUsers();
        const users = res.users || [];
        usersTable.innerHTML = users.map(u => `
          <tr>
            <td>#${u.id}</td>
            <td><strong>${u.full_name}</strong></td>
            <td>${u.email}</td>
            <td><span class="role-badge ${u.role}">${u.role.toUpperCase()}</span></td>
            <td>${new Date(u.created_at).toLocaleDateString()}</td>
            <td>
              ${u.role === 'admin' ? 
                `<button class="btn btn-sm btn-outline-warning" onclick="window.App.changeUserRole(${u.id}, 'user')">Demote to User</button>` : 
                `<button class="btn btn-sm btn-outline-success" onclick="window.App.changeUserRole(${u.id}, 'admin')">Promote to Admin</button>`
              }
            </td>
          </tr>
        `).join('');
      } catch (e) {
        usersTable.innerHTML = `<tr><td colspan="6" class="text-danger">Error: ${e.message}</td></tr>`;
      }
    }

    // Load System Logs
    const logsTable = document.getElementById('admin-logs-table');
    if (logsTable) {
      logsTable.innerHTML = '<tr><td colspan="7" class="text-center"><i class="fa-solid fa-spinner fa-spin"></i> Loading query logs...</td></tr>';
      try {
        const logRes = await window.API.getAdminLogs(50);
        const logs = logRes.logs || [];
        logsTable.innerHTML = logs.map(l => `
          <tr>
            <td>#${l.id}</td>
            <td>${new Date(l.timestamp).toLocaleTimeString()}</td>
            <td>${l.user_email || 'Guest / Direct'}</td>
            <td>${l.origin_lat.toFixed(4)}, ${l.origin_lon.toFixed(4)}</td>
            <td><strong>${l.recommended_hospital_name}</strong></td>
            <td><span class="badge-score">${l.composite_score.toFixed(1)}/100</span></td>
            <td>${l.total_evaluated} evaluated</td>
          </tr>
        `).join('');
      } catch (e) {
        logsTable.innerHTML = `<tr><td colspan="7" class="text-danger">Error: ${e.message}</td></tr>`;
      }
    }
  }

  async changeUserRole(userId, newRole) {
    if (!confirm(`Change user #${userId} role to '${newRole}'?`)) return;
    try {
      await window.API.updateUserRole(userId, newRole);
      this.showToast(`User role updated to ${newRole}.`, 'success');
      this.loadAdminView();
    } catch (e) {
      this.showToast(e.message || 'Failed to update user role.', 'error');
    }
  }

  // ---------------- TOAST NOTIFICATIONS ----------------

  showToast(message, type = 'info') {
    const toast = document.getElementById('app-toast');
    const toastMsg = document.getElementById('toast-message');
    const toastIcon = document.getElementById('toast-icon');

    if (!toast || !toastMsg) return;

    if (this.toastTimeout) clearTimeout(this.toastTimeout);

    toast.className = `toast-popup show toast-${type}`;
    toastMsg.textContent = message;

    if (toastIcon) {
      if (type === 'success') toastIcon.className = 'fa-solid fa-circle-check';
      else if (type === 'error') toastIcon.className = 'fa-solid fa-triangle-exclamation';
      else if (type === 'warning') toastIcon.className = 'fa-solid fa-circle-exclamation';
      else toastIcon.className = 'fa-solid fa-circle-info';
    }

    this.toastTimeout = setTimeout(() => {
      toast.classList.remove('show');
    }, 4500);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.App = new AppController();
  window.App.init();
});
