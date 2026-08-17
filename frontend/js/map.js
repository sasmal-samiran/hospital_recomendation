/**
 * Leaflet Interactive Map Controller
 */
class MapController {
  constructor(elementId = 'map') {
    this.elementId = elementId;
    this.map = null;
    this.userMarker = null;
    this.radiusCircle = null;
    this.hospitalMarkers = [];
    this.routePolylines = [];
    this.activePolyline = null;
  }

  init(center = window.ENV.DEFAULT_MAP_CENTER, zoom = 13) {
    const container = document.getElementById(this.elementId);
    if (!container) return;

    // Destroy existing if re-initializing
    if (this.map) {
      this.map.remove();
      this.map = null;
    }

    this.map = L.map(this.elementId, {
      center: center,
      zoom: zoom,
      zoomControl: true
    });

    // High quality OpenStreetMap tiles with retina support
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(this.map);

    this.setUserLocation(center[0], center[1]);
  }

  setUserLocation(lat, lon, radiusMeters = 5000) {
    if (!this.map) return;

    if (this.userMarker) {
      this.map.removeLayer(this.userMarker);
    }
    if (this.radiusCircle) {
      this.map.removeLayer(this.radiusCircle);
    }

    // Custom pulsating user location marker
    const userIcon = L.divIcon({
      className: 'user-radar-pin',
      html: `<div class="pulse-radar"></div><div class="center-dot"><i class="fa-solid fa-person-circle-exclamation"></i></div>`,
      iconSize: [36, 36],
      iconAnchor: [18, 18]
    });

    this.userMarker = L.marker([lat, lon], { icon: userIcon })
      .addTo(this.map)
      .bindPopup(`<strong>Your Location</strong><br><small>${lat.toFixed(5)}, ${lon.toFixed(5)}</small>`)
      .openPopup();

    // Radius circle
    this.radiusCircle = L.circle([lat, lon], {
      color: '#06b6d4',
      fillColor: '#06b6d4',
      fillOpacity: 0.08,
      weight: 1.5,
      dashArray: '5, 5',
      radius: radiusMeters
    }).addTo(this.map);

    this.map.setView([lat, lon], 13);
  }

  clearHospitalLayers() {
    if (!this.map) return;
    this.hospitalMarkers.forEach(m => this.map.removeLayer(m));
    this.hospitalMarkers = [];
    this.routePolylines.forEach(p => this.map.removeLayer(p));
    this.routePolylines = [];
    this.activePolyline = null;
  }

  renderRankedHospitals(rankedList, originLat, originLon) {
    if (!this.map || !rankedList || rankedList.length === 0) return;

    this.clearHospitalLayers();
    const bounds = L.latLngBounds([[originLat, originLon]]);

    rankedList.forEach((item, index) => {
      const h = item.hospital;
      const r = item.route;
      const rank = item.rank;
      const score = item.scores.final_composite_score;
      const isTop = rank === 1;

      // Pin icon with rank badge
      const iconHtml = `
        <div class="hospital-map-badge ${isTop ? 'top-pick' : ''}">
          <span class="rank-num">#${rank}</span>
          <i class="fa-solid fa-hospital"></i>
        </div>
      `;

      const hospIcon = L.divIcon({
        className: 'custom-hospital-marker',
        html: iconHtml,
        iconSize: [40, 40],
        iconAnchor: [20, 20]
      });

      const popupContent = `
        <div class="map-popup-card">
          <div class="popup-header">
            <span class="popup-rank">Rank #${rank}</span>
            <span class="popup-score">${score.toFixed(1)}/100</span>
          </div>
          <h4>${h.name}</h4>
          <p class="popup-address">${h.formatted_address || 'Address not listed'}</p>
          <div class="popup-metrics">
            <div><i class="fa-solid fa-route"></i> ${r.distance_km} km</div>
            <div><i class="fa-solid fa-clock"></i> ${r.duration_minutes} min</div>
            <div><i class="fa-solid fa-road"></i> ${item.road_condition ? item.road_condition.road_score : '--'}/100</div>
          </div>
          <button class="popup-select-btn" onclick="window.App.selectHospital(${index})">
            <i class="fa-solid fa-arrow-right"></i> View Full Route
          </button>
        </div>
      `;

      const marker = L.marker([h.lat, h.lon], { icon: hospIcon })
        .addTo(this.map)
        .bindPopup(popupContent);

      this.hospitalMarkers.push(marker);
      bounds.extend([h.lat, h.lon]);

      // Render polyline route if coordinates exist
      if (r.lane_coordinates && r.lane_coordinates.length > 0) {
        const polyCoords = r.lane_coordinates.map(c => [c[0], c[1]]);
        
        let color = '#94a3b8'; // default slate
        if (isTop) {
          color = '#10b981'; // Emerald for top recommendation
        } else if (r.congestion_ratio > 1.3) {
          color = '#f59e0b'; // Amber for traffic
        }

        const polyline = L.polyline(polyCoords, {
          color: color,
          weight: isTop ? 5 : 3.5,
          opacity: isTop ? 0.9 : 0.6,
          lineJoin: 'round',
          dashArray: isTop ? null : '6, 6'
        }).addTo(this.map);

        this.routePolylines.push(polyline);
        if (isTop) {
          this.activePolyline = polyline;
        }
      }
    });

    this.map.fitBounds(bounds, { padding: [50, 50] });
  }

  highlightRoute(index, rankedList) {
    if (!this.map || !rankedList || !rankedList[index]) return;
    const item = rankedList[index];

    // Reset styles
    this.routePolylines.forEach((p, i) => {
      if (i === index) {
        p.setStyle({ color: '#10b981', weight: 6, opacity: 1.0, dashArray: null });
        p.bringToFront();
      } else {
        p.setStyle({ color: '#94a3b8', weight: 2.5, opacity: 0.35, dashArray: '4, 4' });
      }
    });

    if (this.hospitalMarkers[index]) {
      this.hospitalMarkers[index].openPopup();
      this.map.panTo([item.hospital.lat, item.hospital.lon]);
    }
  }
}

window.MapController = MapController;
