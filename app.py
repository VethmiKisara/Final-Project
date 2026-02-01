from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.secret_key = 'disasterwatch_secret_2026'  # Secret key for sessions

# Mock alerts data - Real-time simulation
mock_alerts = [
    {
        "id": 1,
        "type": "Flood",
        "lat": 6.9271,
        "lng": 80.7789,
        "confidence": 92,
        "credibility": 85,
        "severity": "high",
        "message": "Heavy flooding reported in Colombo area",
        "timestamp": "2026-01-30 20:15"
    },
    {
        "id": 2,
        "type": "Earthquake",
        "lat": 7.2906,
        "lng": 80.6337,
        "confidence": 78,
        "credibility": 65,
        "severity": "medium",
        "message": "Tremors detected in Kandy region",
        "timestamp": "2026-01-30 19:45"
    },
    {
        "id": 3,
        "type": "Wildfire",
        "lat": 6.3520,
        "lng": 80.7789,
        "confidence": 85,
        "credibility": 90,
        "severity": "high",
        "message": "Active wildfire reported near Galle",
        "timestamp": "2026-01-30 19:20"
    },
    {
        "id": 4,
        "type": "Storm",
        "lat": 7.8731,
        "lng": 80.7718,
        "confidence": 65,
        "credibility": 70,
        "severity": "medium",
        "message": "Severe storm warning issued for Northern Province",
        "timestamp": "2026-01-30 18:50"
    },
    {
        "id": 5,
        "type": "Landslide",
        "lat": 6.8235,
        "lng": 80.7722,
        "confidence": 72,
        "credibility": 75,
        "severity": "low",
        "message": "Minor landslide activity in Badulla district",
        "timestamp": "2026-01-30 18:30"
    }
]

alert_id_counter = 6

# Disaster types available
DISASTER_TYPES = ["Flood", "Earthquake", "Wildfire", "Storm", "Landslide", "Tsunami", "Drought"]
DISASTER_MESSAGES = {
    "Flood": [
        "Heavy flooding reported in {location}",
        "Water levels rising in {location}",
        "Flash flood warning in {location}"
    ],
    "Earthquake": [
        "Tremors detected in {location}",
        "Seismic activity reported in {location}",
        "Earthquake warning for {location}"
    ],
    "Wildfire": [
        "Active wildfire reported in {location}",
        "Fire spreading in {location}",
        "Uncontrolled fire in {location}"
    ],
    "Storm": [
        "Severe storm warning for {location}",
        "Thunderstorm in progress at {location}",
        "Strong winds reported in {location}"
    ],
    "Landslide": [
        "Landslide activity in {location}",
        "Ground movement detected in {location}",
        "Slope failure in {location}"
    ]
}

LOCATIONS = [
    "Colombo", "Kandy", "Galle", "Jaffna", "Batticaloa",
    "Matara", "Ratnapura", "Anuradhapura", "Badulla", "Kurunegala"
]

# System logs for admin panel
system_logs = [
    {"timestamp": "2026-01-30 21:45", "level": "INFO", "message": "System initialized successfully"},
    {"timestamp": "2026-01-30 21:46", "level": "INFO", "message": "Connected to social media feeds"},
    {"timestamp": "2026-01-30 21:47", "level": "WARNING", "message": "API rate limit approaching"},
    {"timestamp": "2026-01-30 21:48", "level": "ERROR", "message": "Failed to connect to secondary API"},
    {"timestamp": "2026-01-30 21:49", "level": "INFO", "message": "Real-time alert monitoring active"},
]


# Mock user credentials
VALID_USERS = {
    'user1': {'password': 'pass123', 'role': 'user'},
    'admin1': {'password': 'admin123', 'role': 'admin', 'passkey': 'secret2026'}
}


def login_required(f):
    """Decorator to check if user is logged in"""
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please login first', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


def admin_required(f):
    """Decorator to check if user is admin"""
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please login first', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Admin access required', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@app.route('/')
def home():
    """Home page - redirects based on login status"""
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Unified login page for User and Admin"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'user')
        passkey = request.form.get('passkey', '').strip()

        # Validate username and password
        if username not in VALID_USERS:
            flash('Invalid username or password', 'danger')
            return render_template('login.html')

        user_data = VALID_USERS[username]
        if user_data['password'] != password:
            flash('Invalid username or password', 'danger')
            return render_template('login.html')

        # Check role match
        if user_data['role'] != role:
            flash('Invalid username or password', 'danger')
            return render_template('login.html')

        # If admin role, check passkey
        if role == 'admin':
            if 'passkey' not in user_data:
                flash('This account is not authorized as admin', 'danger')
                return render_template('login.html')
            if user_data['passkey'] != passkey:
                flash('Invalid admin passkey', 'danger')
                return render_template('login.html')

        # Login successful - store in session
        session['user'] = username
        session['role'] = role
        flash(f'Welcome {username}!', 'success')

        # Redirect based on role
        if role == 'admin':
            return redirect(url_for('admin_panel'))
        else:
            return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Unified signup page for User and Admin"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirmPassword', '').strip()
        role = request.form.get('role', 'user')
        passkey = request.form.get('passkey', '').strip()
        agree_terms = request.form.get('agreeTerms')

        # Validation
        if not username or len(username) < 3:
            flash('Username must be at least 3 characters', 'danger')
            return render_template('signup.html')

        if not email or '@' not in email:
            flash('Please enter a valid email address', 'danger')
            return render_template('signup.html')

        if not password or len(password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return render_template('signup.html')

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('signup.html')

        if not agree_terms:
            flash('You must agree to the terms and conditions', 'danger')
            return render_template('signup.html')

        # Check if username already exists
        if username in VALID_USERS:
            flash('Username already exists. Please choose another', 'danger')
            return render_template('signup.html')

        # Check admin passkey if admin role
        if role == 'admin':
            ADMIN_PASSKEY = 'secret2026'  # Same passkey as login
            if passkey != ADMIN_PASSKEY:
                flash('Invalid admin passkey. Registration failed', 'danger')
                return render_template('signup.html')

        # Create new user in mock database
        if role == 'admin':
            VALID_USERS[username] = {
                'password': password,
                'role': 'admin',
                'passkey': passkey,
                'email': email
            }
        else:
            VALID_USERS[username] = {
                'password': password,
                'role': 'user',
                'email': email
            }

        # Registration successful
        flash(f'Account created successfully! Welcome, {username}. You can now login.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/logout')
def logout():
    """Logout route - clear session"""
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('home'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with map and alerts"""
    return render_template('dashboard.html')


@app.route('/alerts')
@login_required
def alerts():
    """Alert logs page"""
    return render_template('alerts.html')


@app.route('/admin')
@admin_required
def admin_panel():
    """Admin configuration panel"""
    return render_template('admin.html')



@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """API endpoint to fetch all alerts with optional filtering"""
    global alert_id_counter
    
    # Query parameters for filtering
    disaster_type = request.args.get('type', None)
    min_confidence = request.args.get('minConfidence', 0, type=int)
    severity = request.args.get('severity', None)
    
    # Filter alerts
    filtered_alerts = mock_alerts
    
    if disaster_type and disaster_type != 'all':
        filtered_alerts = [a for a in filtered_alerts if a['type'] == disaster_type]
    
    if min_confidence > 0:
        filtered_alerts = [a for a in filtered_alerts if a['confidence'] >= min_confidence]
    
    if severity and severity != 'all':
        filtered_alerts = [a for a in filtered_alerts if a['severity'] == severity]
    
    return jsonify(filtered_alerts)


@app.route('/api/alerts/new', methods=['GET'])
def get_new_alert():
    """API endpoint to simulate a new alert (for real-time updates)"""
    global alert_id_counter
    
    disaster_type = random.choice(DISASTER_TYPES)
    location = random.choice(LOCATIONS)
    
    severity_map = {
        "high": (85, 95, 80, 95),
        "medium": (60, 84, 60, 80),
        "low": (40, 59, 40, 60)
    }
    
    severity = random.choice(["high", "medium", "low"])
    conf_range, cred_range = severity_map[severity][:2], severity_map[severity][2:]
    
    new_alert = {
        "id": alert_id_counter,
        "type": disaster_type,
        "lat": random.uniform(5.9, 9.9),
        "lng": random.uniform(79.7, 81.9),
        "confidence": random.randint(conf_range[0], conf_range[1]),
        "credibility": random.randint(cred_range[0], cred_range[1]),
        "severity": severity,
        "message": random.choice(DISASTER_MESSAGES.get(disaster_type, ["Alert in {location}"])).format(location=location),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    alert_id_counter += 1
    mock_alerts.append(new_alert)
    
    return jsonify(new_alert)


@app.route('/api/logs')
def get_logs():
    """API endpoint for system logs (admin panel)"""
    return jsonify(system_logs)


@app.route('/api/logs/add', methods=['POST'])
def add_log():
    """Add a log entry"""
    data = request.json
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "level": data.get('level', 'INFO'),
        "message": data.get('message', 'No message')
    }
    system_logs.append(log_entry)
    return jsonify(log_entry), 201


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
