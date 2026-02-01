# DisasterWatch - Quick Start Guide

## 🚀 Get Running in 2 Minutes

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Flask Server
```bash
python app.py
```

You'll see:
```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

### Step 3: Open in Browser
Visit: **http://localhost:5000**

---

## 📋 Quick Demo Flow

### First Time?
1. Click **"Sign Up"** button on home page
2. Fill in username, email, password
3. Click **"Create Account"**
4. You'll be logged in automatically!

### Already Have Account?
1. Click **"Login"** button
2. Enter any username/password
3. Click **"Login"**

---

## 🗺️ Dashboard Features

### Map (Left 70%)
- **Red Markers** = High severity disasters
- **Yellow Markers** = Medium severity
- **Green Markers** = Low severity
- Click marker to see details in sidebar
- Click "Expand" button to fit all alerts

### Sidebar (Right 30%)
- **Filter by Type**: Flood, Earthquake, Wildfire, etc.
- **Filter by Severity**: High, Medium, Low
- **Adjust Confidence**: Slide to set minimum %
- **Click Marker**: View full details below
- **Alert Stats**: See total and high-severity counts

### Real-Time Updates
- New disaster alert appears **every 20-30 seconds**
- Notification banner shows when new alert appears
- Marker automatically added to map

---

## 📊 Alert Logs Page

Access from navbar: **Alerts**

- **Table View**: All disasters in sortable table
- **Color-Coded Rows**: Red (high), Yellow (medium), Green (low)
- **Columns**:
  - Type: Disaster type with icon
  - Message: Alert details
  - Confidence: Percentage bar
  - Credibility: Percentage bar
  - Severity: HIGH/MEDIUM/LOW badge
  - Timestamp: Date and time
  - Location: GPS coordinates

- **Search**: Find alerts by type, message, or ID
- **Filters**: Apply multiple filters at once
- **Statistics**: Total and breakdown by severity

---

## ⚙️ Admin Panel

Access from navbar: **Admin Panel** (only for admin accounts)

### To Create Admin Account:
1. Go to home page
2. Click **"Sign Up"** → scroll down
3. Click **"Sign up as admin"** link
4. Use any 4+ character code as "Admin Registration Code"
5. Create account

### Admin Features:

#### 1. Keywords Configuration
- Add keywords to monitor
- One per line
- Use `#` for hashtags
- Click "Save Keywords"

#### 2. API Settings
- Configure Twitter, Reddit, Sentiment Analysis APIs
- Set update interval (10-300 seconds)
- Set confidence threshold (0-100%)
- Click "Save API Settings"

#### 3. System Logs
- Real-time system events
- Filtered by: INFO, WARNING, ERROR
- Color-coded badges
- Auto-refreshes every 10 seconds
- "Clear Logs" button

---

## 🎨 Color Theme

| Element | Color | Meaning |
|---------|-------|---------|
| Navbar | Blue (#0052cc) | Primary brand color |
| High Severity | Red (#dc3545) | Urgent/Critical |
| Medium Severity | Yellow (#ffc107) | Warning |
| Low Severity | Green (#28a745) | Safe/Monitor |
| Buttons | Blue (#0052cc) | Interactive |

---

## 🔐 Authentication

### Session Storage
- Uses browser sessionStorage (cleared on close)
- No real passwords stored
- No database needed
- Demo mode: any credentials work

### Roles
- **User**: Access dashboard & alerts
- **Admin**: Also access admin panel

---

## 🌍 Map Details

### Centered On
Sri Lanka region (coordinates: 7.8731°N, 80.7718°E)

### Zoom Levels
- Default: Level 8 (entire country visible)
- Click marker: Zoom to Level 12
- Click "Expand" button: Fit all markers

### Tile Source
- OpenStreetMap (free, no API key needed)
- Updates automatically
- Supports zoom up to Level 19

---

## 📱 Mobile Responsive

- **Desktop**: 70% map + 30% sidebar
- **Tablet**: Adjusted spacing
- **Mobile**: Touch-friendly, stacked layout

---

## 🐛 Troubleshooting

### "Can't connect to server"
- Make sure Flask is running: `python app.py`
- Check if using http://localhost:5000
- Not https://

### "Map not showing"
- Check internet connection (needs OpenStreetMap tiles)
- Clear cache (Ctrl+Shift+Delete)
- Try different browser

### "Not logged in when I refresh"
- **This is normal!** sessionStorage clears on page close
- Reopen the website and login again
- Or use "Remember me" on login form

### "Admin panel not accessible"
- Make sure you signed up as ADMIN
- Use 4+ character admin code
- Check if browser shows "ADMIN" in navbar

---

## 📌 Test Accounts

Any credentials work in demo mode:

**User Account:**
- Username: testuser
- Password: test123

**Admin Account:**
- Username: admin
- Password: admin123
- Admin Code: admin1234

---

## 🔄 Data Refresh

- Dashboard: Auto-refreshes alerts every 15 seconds
- Alert Logs: Auto-refreshes every 15 seconds
- Admin Logs: Auto-refreshes every 10 seconds
- New Alerts: Added every 20-30 seconds

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Click Marker | View alert details |
| Scroll Map | Zoom in/out |
| Drag Map | Pan around |
| Ctrl+Shift+Delete | Clear cache |
| F12 | Open Developer Console |

---

## 🎯 Key Features Checklist

✅ Interactive map with disaster markers
✅ Real-time alert simulation
✅ User login/signup with roles
✅ Admin panel with configuration
✅ Alert logs with filtering
✅ Color-coded severity levels
✅ Confidence & credibility metrics
✅ Search and filter functionality
✅ Responsive mobile design
✅ No database (sessionStorage only)
✅ Professional blue theme
✅ Leaflet.js map integration

---

## 📞 Support

Check **README.md** for more detailed documentation and troubleshooting.

**Happy monitoring! 🚨🌍**
