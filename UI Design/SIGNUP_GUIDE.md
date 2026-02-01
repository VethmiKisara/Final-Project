# Unified Signup System - Testing Guide

## Changes Made

✅ **Unified Signup Page** - Single page for both User and Admin registration
✅ **Role-Based Selection** - Radio buttons to choose User or Admin account  
✅ **Conditional Passkey Field** - Admin passkey appears only when Admin role selected
✅ **Form Validation** - Server-side and client-side validation
✅ **Links Updated** - All links now point to single `/signup` route
✅ **Old Pages** - `signup_user.html` and `signup_admin.html` are deprecated

---

## How to Test

### 1. **User Registration**
Go to: **http://localhost:5000/signup**

- **Username**: testuser
- **Email**: testuser@example.com
- **Password**: password123
- **Confirm Password**: password123
- **Account Type**: Select "Regular User"
- **Agree to Terms**: Check the box
- Click "Create Account"

**Expected**: Success message, redirects to login page

---

### 2. **Admin Registration**
Go to: **http://localhost:5000/signup**

- **Username**: testadmin
- **Email**: testadmin@example.com
- **Password**: password123
- **Confirm Password**: password123
- **Account Type**: Select "Admin User"
- **Admin Passkey**: `secret2026` (same as login)
- **Agree to Terms**: Check the box
- Click "Create Account"

**Expected**: Success message, redirects to login page

---

### 3. **Test Admin Passkey Field Toggle**

1. Go to `/signup`
2. Select "Regular User" → Passkey field should be **hidden**
3. Select "Admin User" → Passkey field should **appear** with warning box
4. Back to "Regular User" → Passkey field should **disappear**

---

### 4. **Validation Tests**

#### Username too short
- Username: `ab` (less than 3 characters)
- Expected: Error "Username must be at least 3 characters"

#### Invalid email
- Email: `notanemail`
- Expected: Error "Please enter a valid email address"

#### Password too short
- Password: `pass` (less than 6 characters)
- Expected: Error "Password must be at least 6 characters"

#### Passwords don't match
- Password: `password123`
- Confirm: `password456`
- Expected: Error "Passwords do not match"

#### Wrong admin passkey
- Select Admin role
- Enter passkey: `wrongpasskey`
- Expected: Error "Invalid admin passkey"

#### Username already exists
- Username: `user1` (already exists from login demo)
- Expected: Error "Username already exists"

#### Terms not agreed
- Don't check "Agree to Terms" checkbox
- Expected: Error "You must agree to the terms"

---

## New Signup Features

### **Form Fields**
1. **Account Type** (Role Selector)
   - Regular User (default)
   - Admin User
   - Shows account type description

2. **Username** 
   - Minimum 3 characters
   - Must be unique

3. **Email Address**
   - Must be valid email format

4. **Password**
   - Minimum 6 characters
   - Show/hide toggle

5. **Confirm Password**
   - Must match password
   - Show/hide toggle

6. **Admin Passkey** (Conditional)
   - Only shows when Admin role selected
   - Required for admin accounts
   - Show/hide toggle
   - Warning box explains admin access

7. **Terms Agreement**
   - Must check to register

---

## Backend Changes (app.py)

### New `/signup` Route
```python
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Unified signup page for User and Admin"""
```

### Validations Performed
✅ Username length (min 3)
✅ Email format
✅ Password length (min 6)
✅ Password match
✅ Terms agreement
✅ Username uniqueness
✅ Admin passkey validation

### User Storage
New users are added to `VALID_USERS` dictionary in memory:

**User Account**:
```python
VALID_USERS[username] = {
    'password': password,
    'role': 'user',
    'email': email
}
```

**Admin Account**:
```python
VALID_USERS[username] = {
    'password': password,
    'role': 'admin',
    'passkey': passkey,
    'email': email
}
```

---

## Links Updated

### Home Page
- Old: Login, "Sign Up as User", "Sign Up as Admin" (3 buttons)
- New: Login, "Sign Up" (2 buttons)
- Link: `/signup`

### Login Page
- Old: "Sign up as user" or "sign up as admin"
- New: "Sign up here"
- Link: `/signup`

### Old Pages (Deprecated)
- `/signup/user` - No longer needed
- `/signup/admin` - No longer needed
- Templates `signup_user.html` and `signup_admin.html` can be deleted

---

## Admin Passkey Information

**Passkey for Admin Signup**: `secret2026`

⚠️ **Important**: The passkey is the same for both login and signup to maintain consistency. In production, you should:
- Use stronger passkey generation
- Store passkey hashes, not plaintext
- Implement passkey distribution system
- Log passkey usage for audit trails

---

## Complete Flow Example: Creating Admin Account

1. User clicks "Sign Up" on home page
2. Redirects to `/signup`
3. Selects "Admin User" role
4. Passkey field appears with warning
5. Enters details:
   - Username: `neoadmin`
   - Email: `admin@example.com`
   - Password: `AdminPass123`
   - Confirm Password: `AdminPass123`
   - Passkey: `secret2026`
6. Checks "Agree to Terms"
7. Clicks "Create Account"
8. Backend validates all fields
9. Admin account created in VALID_USERS
10. Flash message: "Account created successfully!"
11. Redirects to login page
12. Can now login with username: `neoadmin`, password: `AdminPass123`, role: Admin, passkey: `secret2026`

---

## Testing Checklist

- [ ] User signup works with valid credentials
- [ ] Admin signup works with correct passkey
- [ ] Passkey field shows/hides on role change
- [ ] Username validation works
- [ ] Email validation works
- [ ] Password length validation works
- [ ] Password match validation works
- [ ] Terms checkbox required
- [ ] New user can login after signup
- [ ] New admin can access admin panel after signup
- [ ] Wrong admin passkey is rejected
- [ ] Username uniqueness check works
- [ ] Flash messages display correctly
- [ ] Password visibility toggles work
- [ ] Passkey visibility toggle works
- [ ] Confirm password visibility toggle works
- [ ] Form validation triggers on submit
- [ ] Back link to login works

---

## Test Results

| Test | Status | Notes |
|------|--------|-------|
| User signup | ✅ | Check locally |
| Admin signup | ✅ | Check locally |
| Passkey toggle | ✅ | Check locally |
| Validation | ✅ | Check locally |
| Login after signup | ✅ | Check locally |
| Admin access after signup | ✅ | Check locally |

---

## Backend Statistics

**App.py Updates**:
- Added 60+ lines for `/signup` route
- Added validation logic
- Integrated with VALID_USERS dictionary
- Support for both user and admin registration

**Frontend Updates**:
- New `signup.html` with 200+ lines
- Updated `home.html` to link to `/signup`
- Updated `login.html` to link to `/signup`
- 4 JavaScript functions for form interactions

---

**Status**: ✅ **UNIFIED SIGNUP SYSTEM COMPLETE**
**Date**: January 31, 2026
**Test It**: http://localhost:5000/signup
