# DisasterWatch Authentication - Quick Test Reference

## Starting the Application

```bash
cd "e:\Degree Notes & Prcticals\3.1 semester\3.1\re\UI Design"
python app.py
```

Then navigate to: **http://localhost:5000**

---

## Test Credentials

### User Account
```
Username: user1
Password: pass123
Role: User
Access: Dashboard, Alerts
```

### Admin Account
```
Username: admin1
Password: admin123
Passkey: secret2026
Role: Admin
Access: Dashboard, Alerts, Admin Panel
```

---

## Test Scenarios

### ✅ Test 1: User Login (Success)
1. Go to `/login`
2. Enter username: `user1`
3. Enter password: `pass123`
4. Select role: `User` (default)
5. Click "Login"
6. **Expected**: Redirect to /dashboard, see dashboard page

### ✅ Test 2: Admin Login (Success)
1. Go to `/login`
2. Select role: `Admin`
3. **Expect**: Passkey field appears
4. Enter username: `admin1`
5. Enter password: `admin123`
6. Enter passkey: `secret2026`
7. Click "Login"
8. **Expected**: Redirect to /admin, see admin panel

### ❌ Test 3: Wrong Password
1. Go to `/login`
2. Enter username: `user1`
3. Enter password: `wrongpassword`
4. Click "Login"
5. **Expected**: Flash message "Invalid username or password", stay on login page

### ❌ Test 4: Wrong Admin Passkey
1. Go to `/login`
2. Select role: `Admin`
3. Enter username: `admin1`
4. Enter password: `admin123`
5. Enter passkey: `wrongpasskey`
6. Click "Login"
7. **Expected**: Flash message "Invalid admin passkey", stay on login page

### ❌ Test 5: Missing Admin Passkey
1. Go to `/login`
2. Select role: `Admin`
3. Enter username: `admin1`
4. Enter password: `admin123`
5. Leave passkey empty
6. Click "Login"
7. **Expected**: Alert "Please enter the admin passkey", stay on login page

### 🔐 Test 6: Protected Route (Logged Out)
1. Logout (if logged in)
2. Try to access `/dashboard` directly
3. **Expected**: Redirect to /login with "Please login first" message

### 🔐 Test 7: Admin-Only Route (User Account)
1. Login as user1
2. Try to access `/admin` directly (or click navbar)
3. **Expected**: Flash message "Admin access required", redirect to /dashboard

### 🔐 Test 8: Admin Panel (Admin Account)
1. Login as admin1
2. Click "Admin Panel" in navbar (or access `/admin`)
3. **Expected**: Admin panel loads successfully

### ➡️ Test 9: Logout
1. Login as any user
2. Click "Logout" in navbar
3. **Expected**: Redirect to home, flash message "Logged out successfully"
4. **Verify**: Navbar shows only "Login" button

### 🏠 Test 10: Home Page - Logged Out
1. Navigate to `/` (home)
2. **Expected**: Show "Welcome to DisasterWatch" with buttons:
   - Login
   - Sign Up as User
   - Sign Up as Admin

### 🏠 Test 11: Home Page - Logged In
1. Login as user1
2. Navigate to `/` (home)
3. **Expected**: Show "Welcome back, user1!" with button:
   - Go to Dashboard

### 🧭 Test 12: Navbar Display - User
1. Login as user1
2. Check navbar
3. **Expected**: Show links:
   - Home
   - Dashboard
   - Alerts
   - Logout (user1)
   - ❌ Admin Panel (should NOT show)

### 🧭 Test 13: Navbar Display - Admin
1. Login as admin1
2. Check navbar
3. **Expected**: Show links:
   - Home
   - Dashboard
   - Alerts
   - Admin Panel ⭐ (should show in warning/yellow)
   - Logout (admin1)

### 🧭 Test 14: Navbar Display - Logged Out
1. Logout
2. Check navbar
3. **Expected**: Show links:
   - Home
   - Login (button)

---

## Checklist for Complete Testing

- [ ] User login works
- [ ] User cannot access admin area
- [ ] Admin login works with passkey
- [ ] Admin can access admin panel
- [ ] Passkey field shows/hides based on role selection
- [ ] Wrong credentials show error
- [ ] Wrong passkey shows error
- [ ] Logout clears session
- [ ] Protected routes redirect when not logged in
- [ ] Admin-only routes redirect when not admin
- [ ] Navbar shows correct links based on login status
- [ ] Navbar shows admin link only for admin users
- [ ] Home page shows personalized message when logged in
- [ ] Home page shows login buttons when logged out
- [ ] Flash messages display correctly
- [ ] Password visibility toggle works
- [ ] Passkey visibility toggle works
- [ ] Cannot bypass login by accessing dashboard directly

---

## Common Issues & Solutions

### Issue: Passkey field doesn't appear
**Solution**: JavaScript might be disabled or error. Check browser console (F12).

### Issue: Flask shows "Unable to find session"
**Solution**: Secret key not set. Check `app.secret_key = 'disasterwatch_secret_2026'` in app.py.

### Issue: Navbar doesn't update after login
**Solution**: Page must reload. Flask session is server-side, so browser must fetch page again.

### Issue: Login button disabled/not working
**Solution**: Check form fields have `name` attributes (username, password, role, passkey).

### Issue: Can't access admin even with correct credentials
**Solution**: Verify you selected "Admin" role and entered correct passkey (secret2026).

---

## Database Connection (Future)

When moving from mock credentials to database:

```python
# Example structure (SQLAlchemy)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    passkey_hash = db.Column(db.String(255))  # For admin users
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
```

---

## File Locations

- **Backend**: `app.py`
- **Login Template**: `templates/login.html`
- **Base Template**: `templates/base.html`
- **Home Template**: `templates/home.html`
- **Dashboard Template**: `templates/dashboard.html`
- **Admin Template**: `templates/admin.html`
- **Alerts Template**: `templates/alerts.html`
- **Auth Utilities**: `static/js/auth.js`
- **Styling**: `static/css/style.css`

---

## Documentation Files

- 📄 `AUTHENTICATION_GUIDE.md` - Comprehensive authentication guide
- 📄 `IMPLEMENTATION_CHANGES.md` - Detailed change summary
- 📄 `README.md` - Project overview
- 📄 `QUICK_START.md` - Quick start guide
- 📄 `PROJECT_SUMMARY.md` - Project summary

---

## Key Changes Summary

✅ **From**: Client-side sessionStorage
✅ **To**: Server-side Flask sessions

**Benefits**:
- More secure
- Better control
- Flash messages
- Role-based access
- Admin passkey protection

**Features**:
- Unified login page
- Role selector (User/Admin)
- Conditional passkey field
- Real-time navbar updates
- Session-based access control
- Flash message feedback

---

## Support

For issues or questions:
1. Check `AUTHENTICATION_GUIDE.md`
2. Review `IMPLEMENTATION_CHANGES.md`
3. Run test scenarios above
4. Check browser console (F12) for errors
5. Check Flask terminal for error messages

---

**Last Updated**: January 30, 2026
**Status**: ✅ Ready for Testing
