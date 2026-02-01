/* ============================================
   DisasterWatch - Dashboard Module
   ============================================ */

// Dashboard-specific functions

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard components
    initializeDashboard();
});

function initializeDashboard() {
    // Add event listeners to filter controls
    const typeFilter = document.getElementById('typeFilter');
    const severityFilter = document.getElementById('severityFilter');
    const confidenceFilter = document.getElementById('confidenceFilter');

    if (typeFilter) {
        typeFilter.addEventListener('change', updateConfidenceLabel);
    }

    if (severityFilter) {
        severityFilter.addEventListener('change', updateConfidenceLabel);
    }

    if (confidenceFilter) {
        confidenceFilter.addEventListener('input', updateConfidenceLabel);
    }

    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        // Initialize Bootstrap tooltips
    }

    Logger.log('Dashboard initialized');
}

function updateConfidenceLabel() {
    const confidenceFilter = document.getElementById('confidenceFilter');
    const confidenceValue = document.getElementById('confidenceValue');

    if (confidenceFilter && confidenceValue) {
        const value = parseInt(confidenceFilter.value);
        if (value === 0) {
            confidenceValue.textContent = 'All (0%+)';
        } else {
            confidenceValue.textContent = value + '%+';
        }
    }
}

// Get filtered alerts based on current filter values
function getFilteredAlerts() {
    const typeFilter = document.getElementById('typeFilter')?.value || 'all';
    const severityFilter = document.getElementById('severityFilter')?.value || 'all';
    const confidenceFilter = parseInt(document.getElementById('confidenceFilter')?.value || 0);

    const filtered = window.mapMarkers.filter(alert => {
        let matches = true;

        if (typeFilter !== 'all' && alert.type !== typeFilter) {
            matches = false;
        }

        if (severityFilter !== 'all' && alert.severity !== severityFilter) {
            matches = false;
        }

        if (alert.confidence < confidenceFilter) {
            matches = false;
        }

        return matches;
    });

    return filtered;
}

// Search and filter functionality
function searchAlerts(searchTerm) {
    if (!searchTerm) {
        return window.mapMarkers;
    }

    const term = searchTerm.toLowerCase();
    return window.mapMarkers.filter(alert => {
        return alert.type.toLowerCase().includes(term) ||
               alert.message.toLowerCase().includes(term) ||
               alert.id.toString().includes(term);
    });
}

// Export dashboard functions
window.dashboardFunctions = {
    getFilteredAlerts,
    searchAlerts,
    initializeDashboard
};

Logger.log('Dashboard module loaded');
