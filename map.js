/* ============================================
   DisasterWatch - Leaflet Map Module
   ============================================ */

let map;
let markers = {};
let mapMarkers = [];
let alerts = [];
let selectedAlertId = null;

// Initialize the map
function initMap() {
    // Center coordinates (Sri Lanka)
    const centerLat = 7.8731;
    const centerLng = 80.7718;

    // Create map instance
    map = L.map('map').setView([centerLat, centerLng], 8);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
        minZoom: 5
    }).addTo(map);

    // Add custom controls
    addMapControls();

    Logger.log('Map initialized successfully');
}

// Add custom map controls
function addMapControls() {
    // Zoom to fit all markers button
    const fitButton = L.Control.extend({
        options: {
            position: 'topleft'
        },
        onAdd: function(map) {
            const container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
            const button = L.DomUtil.create('a', '', container);
            button.innerHTML = '<i class="fas fa-expand"></i>';
            button.title = 'Fit all alerts';
            button.style.width = '36px';
            button.style.height = '36px';
            button.style.lineHeight = '36px';
            button.style.textAlign = 'center';
            button.style.cursor = 'pointer';
            button.style.fontSize = '16px';
            
            L.DomEvent.on(button, 'click', function(e) {
                L.DomEvent.stopPropagation(e);
                fitMarkersToMap();
            });

            return container;
        }
    });

    new fitButton().addTo(map);
}

// Load alerts from API
async function loadAlerts() {
    try {
        // Build query parameters
        const typeFilter = document.getElementById('typeFilter')?.value || 'all';
        const severityFilter = document.getElementById('severityFilter')?.value || 'all';
        const confidenceFilter = parseInt(document.getElementById('confidenceFilter')?.value || 0);

        let url = '/api/alerts';
        const params = [];

        if (typeFilter !== 'all') params.push(`type=${typeFilter}`);
        if (severityFilter !== 'all') params.push(`severity=${severityFilter}`);
        if (confidenceFilter > 0) params.push(`minConfidence=${confidenceFilter}`);

        if (params.length > 0) {
            url += '?' + params.join('&');
        }

        const data = await fetch(url).then(r => r.json());
        alerts = data;
        mapMarkers = data;

        // Clear existing markers
        Object.values(markers).forEach(marker => map.removeLayer(marker));
        markers = {};

        // Add new markers
        data.forEach(alert => {
            addMarker(alert);
        });

        Logger.log(`Loaded ${data.length} alerts`);
        fitMarkersToMap();

    } catch (error) {
        Logger.error('Failed to load alerts', error);
    }
}

// Add a marker to the map
function addMarker(alert) {
    const color = getMarkerColor(alert.severity);
    
    // Create custom icon
    const icon = L.divIcon({
        className: 'custom-marker',
        html: `
            <div style="
                background-color: ${color};
                width: 30px;
                height: 30px;
                border-radius: 50%;
                border: 3px solid white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 16px;
                cursor: pointer;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            ">
                <i class="fas fa-exclamation" style="color: white; font-size: 12px;"></i>
            </div>
        `,
        iconSize: [30, 30],
        iconAnchor: [15, 15],
        popupAnchor: [0, -15]
    });

    // Create marker
    const marker = L.marker([alert.lat, alert.lng], { icon: icon })
        .bindPopup(createPopupContent(alert), {
            maxWidth: 300,
            minWidth: 250
        })
        .addTo(map);

    // Add click event
    marker.on('click', function() {
        selectedAlertId = alert.id;
        showAlertDetails(alert);
        map.setView([alert.lat, alert.lng], 12);
    });

    marker.alert = alert;
    markers[alert.id] = marker;
}

// Create popup content for marker
function createPopupContent(alert) {
    return `
        <div style="padding: 10px;">
            <h6 style="margin: 0 0 10px 0; color: #0052cc;">
                <i class="fas fa-exclamation-triangle" style="color: ${getMarkerColor(alert.severity)}; margin-right: 8px;"></i>
                ${alert.type}
            </h6>
            <p style="margin: 8px 0; font-size: 12px;">${alert.message}</p>
            <div style="margin: 8px 0; font-size: 11px; color: #666;">
                <strong>Confidence:</strong> ${alert.confidence}%<br>
                <strong>Credibility:</strong> ${alert.credibility}%<br>
                <strong>Severity:</strong> ${alert.severity.toUpperCase()}<br>
                <strong>Location:</strong> ${alert.lat.toFixed(4)}°, ${alert.lng.toFixed(4)}°<br>
                <strong>Time:</strong> ${alert.timestamp}
            </div>
        </div>
    `;
}

// Show alert details in sidebar
function showAlertDetails(alert) {
    const container = document.getElementById('alertDetailsContainer');
    
    const severityColors = {
        'high': '#dc3545',
        'medium': '#ffc107',
        'low': '#28a745'
    };

    const severityTextColors = {
        'high': '#fff',
        'medium': '#000',
        'low': '#fff'
    };

    const html = `
        <div class="alert-detail-card mb-3" style="border-left: 4px solid ${getMarkerColor(alert.severity)}; background-color: ${getMarkerColor(alert.severity)}15;">
            <div class="mb-3">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                    <h5 class="mb-0">
                        <i class="fas fa-map-pin me-2" style="color: ${getMarkerColor(alert.severity)};"></i>
                        ${alert.type}
                    </h5>
                    <span class="badge" style="background-color: ${severityColors[alert.severity]}; color: ${severityTextColors[alert.severity]};">
                        ${alert.severity.toUpperCase()}
                    </span>
                </div>
            </div>

            <div class="mb-3">
                <label class="small fw-bold text-muted d-block">Message</label>
                <p class="mb-0">${alert.message}</p>
            </div>

            <div class="row g-2 mb-3">
                <div class="col-6">
                    <label class="small fw-bold text-muted d-block">Confidence</label>
                    <div class="progress" style="height: 24px;">
                        <div class="progress-bar" style="width: ${alert.confidence}%">
                            ${alert.confidence}%
                        </div>
                    </div>
                </div>
                <div class="col-6">
                    <label class="small fw-bold text-muted d-block">Credibility</label>
                    <div class="progress" style="height: 24px;">
                        <div class="progress-bar bg-info" style="width: ${alert.credibility}%">
                            ${alert.credibility}%
                        </div>
                    </div>
                </div>
            </div>

            <div class="row g-2 small text-muted">
                <div class="col-12">
                    <i class="fas fa-map-marker-alt me-2"></i>
                    <strong>Location:</strong> ${alert.lat.toFixed(4)}°, ${alert.lng.toFixed(4)}°
                </div>
                <div class="col-12 mt-2">
                    <i class="fas fa-clock me-2"></i>
                    <strong>Timestamp:</strong> ${alert.timestamp}
                </div>
                <div class="col-12 mt-2">
                    <i class="fas fa-hashtag me-2"></i>
                    <strong>ID:</strong> ${alert.id}
                </div>
            </div>

            <div class="mt-3">
                <button class="btn btn-sm btn-primary w-100" onclick="viewAlertDetails(${alert.id})">
                    <i class="fas fa-arrow-right me-1"></i>View Full Details
                </button>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

// Fit all markers in view
function fitMarkersToMap() {
    if (Object.keys(markers).length === 0) {
        // Default view if no markers
        map.setView([7.8731, 80.7718], 8);
        return;
    }

    const group = new L.featureGroup(Object.values(markers));
    map.fitBounds(group.getBounds().pad(0.1), { animate: true });
}

// Add a random alert simulation
async function addRandomAlert() {
    try {
        const response = await fetch('/api/alerts/new');
        const newAlert = await response.json();

        // Add to alerts array
        alerts.push(newAlert);
        mapMarkers.push(newAlert);

        // Add marker
        addMarker(newAlert);

        // Show notification
        showNotification(`New ${newAlert.type} alert detected!`, 'warning', 4000);

        Logger.log('New alert added:', newAlert);

        // Update stats
        updateStats();

    } catch (error) {
        Logger.error('Failed to add random alert', error);
    }
}

// Update dashboard statistics
function updateStats() {
    const totalAlerts = mapMarkers.length;
    const highSeverity = mapMarkers.filter(a => a.severity === 'high').length;

    const totalElement = document.getElementById('totalAlerts');
    const highElement = document.getElementById('highSeverityCount');

    if (totalElement) totalElement.textContent = totalAlerts;
    if (highElement) highElement.textContent = highSeverity;
}

// View alert details (navigate to alerts page with filter)
function viewAlertDetails(alertId) {
    const alert = alerts.find(a => a.id === alertId);
    if (alert) {
        LocalStorage.set('selectedAlert', alert);
        window.location.href = '/alerts';
    }
}

// Initialize map cluster groups (advanced feature)
function initializeClusterMarkers() {
    // This would require Leaflet.markercluster plugin
    // For now, using basic markers
}

// Export functions for external use
window.mapFunctions = {
    initMap,
    loadAlerts,
    addMarker,
    addRandomAlert,
    fitMarkersToMap,
    updateStats
};

Logger.log('Map module loaded');
