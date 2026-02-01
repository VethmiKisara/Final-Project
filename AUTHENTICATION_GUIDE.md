# DisasterWatch Authentication System Guide

## Overview
DisasterWatch now implements a unified, server-side session-based authentication system with role-based access control (RBAC). The system has been upgraded from client-side sessionStorage to Flask server-side sessions for improved security and control.

## Architecture

### Backend (Flask)
- **Session Management**: Flask `session` object with secret key `'disasterwatch_secret_2026'`
- **Route Protection**: Decorator-based access control
- **Mock Credentials**: Hardcoded in `VALID_USERS` dictionary (demo mode)

### Frontend
- **Login Form**: Role-aware form with conditional passkey field
- **Navbar Integration**: Dynamic display based on `session.role`
- **Session Awareness**: Jinja2 templates render based on server-side session

## Mock Credentials

### User Account
- **Username**: `user1`
- **Password**: `pass123`
- **Role**: `user`
- **Access**: Dashboard, Alerts

### Admin Account
- **Username**: `admin1`
- **Password**: `admin123`
- **Passkey**: `secret2026`
- **Role**: `admin`
- **Access**: Dashboard, Alerts, Admin Panel

## Login Flow

### 1. User Login (Regular User)
```
1. User navigates to /login
2. Selects "User" role (default)
3. Enters username: user1
4. Enters password: pass123
5. Clicks "Login"
6. Flask validates credentials
7. Session['user'] = 'user1'
8. Session['role'] = 'user'
9. Redirects to /dashboard
```

### 2. Admin Login
```
1. User navigates to /login
2. Selects "Admin" role
3. Passkey field becomes visible
4. Enters username: admin1
5. Enters password: admin123
6. Enters passkey: secret2026
7. Clicks "Login"
8. Flask validates all three fields
9. Session['user'] = 'admin1'
10. Session['role'] = 'admin'
11. Redirects to /admin
```

## Login Form Features

### HTML Form (login.html)
- **Username Field**: Text input with user icon
- **Password Field**: Password input with show/hide toggle
- **Role Selector**: Radio buttons for "User" or "Admin"
- **Passkey Field**: 
  - Hidden by default
  - Shows only when "Admin" is selected
  - Required for admin login
  - Show/hide password toggle
- **Flash Messages**: Display error/success messages from Flask
- **Security**: All fields validated server-side

### JavaScript Interactivity
```javascript
// Toggle passkey field visibility based on role selection
function togglePasskey() {
    const roleAdmin = document.getElementById('roleAdmin').checked;
    const passkeyContainer = document.getElementById('passkeyContainer');
    
    if (roleAdmin) {
        passkeyContainer.style.display = 'block';
        passkeyInput.required = true;
    } else {
        passkeyContainer.style.display = 'none';
        passkeyInput.required = false;
    }
}
```

## Route Protection

### Decorators

**@login_required**
```python
# Checks if user is in session
# Redirects to /login if not authenticated
# Used by: /dashboard, /alerts
```

**@admin_required**
```python
# Checks if user is in session AND role == 'admin'
# Redirects to /login if not authenticated
# Redirects to /dashboard if not admin
# Used by: /admin
```

### Protected Routes
- `GET /dashboard` - User dashboard
- `GET /alerts` - Alert logs
- `GET /admin` - Admin panel

### Public Routes
- `GET /` - Home page
- `GET/POST /login` - Login form
- `GET /logout` - Logout

## Navbar Integration

### Dynamic Display (base.html)
```html
{% if session.user %}
    <!-- Show authenticated user links -->
    <a href="/dashboard">Dashboard</a>
    <a href="/alerts">Alerts</a>
    {% if session.role == 'admin' %}
        <a href="/admin">Admin Panel</a>
    {% endif %}
    <a href="/logout">Logout ({{ session.user }})</a>
{% else %}
    <!-- Show login link -->
    <a href="/login">Login</a>
{% endif %}
```

## Home Page Display (home.html)

### For Logged-Out Users
- Shows "DisasterWatch" welcome card
- Displays three action buttons:
  1. Login
  2. Sign Up as User
  3. Sign Up as Admin

### For Logged-In Users
- Shows personalized greeting: "Welcome back, [username]!"
- Shows "Go to Dashboard" button
- Hides all login/signup buttons

## Logout

### Process
1. User clicks "Logout" in navbar
2. Routes to `GET /logout`
3. Flask calls `session.clear()`
4. Sets flash message: "Logged out successfully"
5. Redirects to `/` (home page)
6. Navbar automatically updates

## API Endpoints

### No Authentication Required (Public)
- `GET /api/alerts` - Fetch all alerts
- `GET /api/alerts/new` - Get new alerts every 20-30 seconds
- `GET /api/logs` - Get system logs (admin view in frontend)

### Note
API endpoints are currently public. Consider adding session checks if needed:
```python
@app.route('/api/alerts')
@login_required  # Add this decorator to require login
def get_alerts():
    # ...
```

## Flash Messages

### Message Categories
- **'danger'** (Red): Login errors, invalid credentials, unauthorized access
- **'success'** (Green): Successful login
- **'warning'** (Yellow): Session expired, login required
- **'info'** (Blue): Logout confirmation

### Common Messages
- "Invalid username or password" - Wrong credentials
- "Invalid admin passkey" - Wrong passkey
- "Please login first" - Trying to access protected route
- "Admin access required" - Non-admin trying to access /admin
- "Welcome [username]!" - Successful login
- "Logged out successfully" - After logout

## Configuration

### Secret Key (app.py)
```python
app.secret_key = 'disasterwatch_secret_2026'
```
**Note**: Change this in production!

### Mock Credentials (app.py)
```python
VALID_USERS = {
    'user1': {'password': 'pass123', 'role': 'user'},
    'admin1': {'password': 'admin123', 'role': 'admin', 'passkey': 'secret2026'}
}
```

## Testing Checklist

- [ ] User login with user1/pass123 works
- [ ] User cannot access /admin
- [ ] Admin login requires passkey field
- [ ] Admin login with admin1/admin123/secret2026 works
- [ ] Wrong passkey rejects admin login
- [ ] Wrong password rejects both user and admin
- [ ] Logout clears session and redirects
- [ ] Navbar shows/hides admin link based on role
- [ ] Home page shows welcome message when logged in
- [ ] Protected routes redirect to login when not authenticated
- [ ] Flash messages display correctly

## Future Enhancements

1. **Database Integration**: Replace mock credentials with database
2. **Password Hashing**: Use werkzeug.security.generate_password_hash
3. **Email Verification**: Add email confirmation for signup
4. **Password Reset**: Implement forgot password functionality
5. **Session Timeout**: Add automatic logout after inactivity
6. **API Authentication**: Add token-based auth for API calls
7. **Role-Based API Access**: Restrict API endpoints by role
8. **Audit Logging**: Track login/logout events
9. **Two-Factor Authentication**: Add 2FA for admin accounts

## Files Modified

1. **app.py**
   - Added Flask session imports
   - Added `app.secret_key`
   - Added `VALID_USERS` dictionary
   - Added `login_required()` decorator
   - Added `admin_required()` decorator
   - Rewrote `/login` route with GET/POST handling
   - Updated `/logout` route
   - Added decorators to protected routes

2. **templates/login.html**
   - Complete rewrite with role selector
   - Added conditional passkey field
   - Added JavaScript for passkey visibility toggle
   - Added password visibility toggle
   - Integrated Flask flash messages

3. **templates/base.html**
   - Updated navbar to use `session.role` instead of sessionStorage
   - Conditional rendering of navbar links
   - Removed JavaScript sessionStorage checks

4. **templates/home.html**
   - Updated to use `session.user` instead of sessionStorage
   - Removed JavaScript sessionStorage logic
   - Server-side rendering of logged-in state

5. **static/js/auth.js**
   - Removed sessionStorage-based functions
   - Removed checkAuth() function
   - Kept utility functions (showNotification, apiCall, etc.)

## Session Variables

**session['user']**: Username of logged-in user (string)
**session['role']**: Role of logged-in user ('user' or 'admin')

## Example Usage in Templates

```jinja2
<!-- Check if user is logged in -->
{% if session.user %}
    <p>Welcome, {{ session.user }}!</p>
{% endif %}

<!-- Check if user is admin -->
{% if session.role == 'admin' %}
    <a href="/admin">Admin Panel</a>
{% endif %}

<!-- Display username in navbar -->
<a href="/logout">Logout ({{ session.user }})</a>
```

## Security Notes

⚠️ **Demo Mode**: This app uses hardcoded mock credentials for demonstration.

🔒 **For Production**:
1. Use a proper database (PostgreSQL, MySQL, etc.)
2. Hash passwords with `werkzeug.security.generate_password_hash()`
3. Use HTTPS only (SSL/TLS)
4. Set `SESSION_COOKIE_SECURE = True`
5. Set `SESSION_COOKIE_HTTPONLY = True`
6. Use a strong, random secret key
7. Implement CSRF protection
8. Add session timeout
9. Log authentication events
10. Use proper passkey generation and storage

---

**Last Updated**: January 30, 2026
**System**: DisasterWatch v1.0
**Authentication Type**: Flask Server-Side Sessions with Role-Based Access Control
