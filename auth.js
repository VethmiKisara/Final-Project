/* ============================================
   DisasterWatch - Authentication Module
   (Now using Flask server-side sessions)
   ============================================ */

// Flask handles authentication server-side
// This module provides utility functions for the frontend

// Show notification
function showNotification(message, type = 'info', duration = 3000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.top = '100px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-warning',
        info: 'fas fa-info-circle'
    };

    alertDiv.innerHTML = `
        <i class="${icons[type] || icons.info} me-2"></i>${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    if (duration > 0) {
        setTimeout(() => {
            alertDiv.remove();
        }, duration);
    }

    return alertDiv;
}

// API call helper
async function apiCall(endpoint, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    };

    const finalOptions = { ...defaultOptions, ...options };

    try {
        const response = await fetch(endpoint, finalOptions);
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API Call Error:', error);
        throw error;
    }
}

// Format timestamp for display
function formatTimestamp(timestamp) {
    const date = new Date(timestamp.replace(' ', 'T'));
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// Get severity badge HTML
function getSeverityBadge(severity) {
    const badges = {
        'high': '<span class="badge badge-severity-high"><i class="fas fa-exclamation-triangle me-1"></i>HIGH</span>',
        'medium': '<span class="badge badge-severity-medium"><i class="fas fa-exclamation-circle me-1"></i>MEDIUM</span>',
        'low': '<span class="badge badge-severity-low"><i class="fas fa-info-circle me-1"></i>LOW</span>'
    };
    return badges[severity] || badges['low'];
}

// Get marker color by severity
function getMarkerColor(severity) {
    const colors = {
        'high': '#dc3545',      // Red
        'medium': '#ffc107',    // Yellow/Orange
        'low': '#28a745'        // Green
    };
    return colors[severity] || colors['low'];
}

// Local storage utilities for additional data persistence
const LocalStorage = {
    set: function(key, value) {
        try {
            localStorage.setItem(`disasterwatch_${key}`, JSON.stringify(value));
        } catch (e) {
            console.error('LocalStorage set error:', e);
        }
    },
    get: function(key) {
        try {
            const item = localStorage.getItem(`disasterwatch_${key}`);
            return item ? JSON.parse(item) : null;
        } catch (e) {
            console.error('LocalStorage get error:', e);
            return null;
        }
    },
    remove: function(key) {
        try {
            localStorage.removeItem(`disasterwatch_${key}`);
        } catch (e) {
            console.error('LocalStorage remove error:', e);
        }
    },
    clear: function() {
        try {
            const keys = Object.keys(localStorage);
            keys.forEach(key => {
                if (key.startsWith('disasterwatch_')) {
                    localStorage.removeItem(key);
                }
            });
        } catch (e) {
            console.error('LocalStorage clear error:', e);
        }
    }
};

// Logging utility
const Logger = {
    log: function(message, data = null) {
        console.log(`[DisasterWatch] ${message}`, data);
    },
    error: function(message, error = null) {
        console.error(`[DisasterWatch ERROR] ${message}`, error);
    },
    warn: function(message, data = null) {
        console.warn(`[DisasterWatch WARN] ${message}`, data);
    }
};
