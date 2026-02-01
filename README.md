# DisasterWatch - Real-Time Multimodal Disaster Detection

A real-time disaster monitoring web application that detects and alerts users about disasters happening in real-time using social media data.

## Features

✅ **Interactive Leaflet Map** - Real-time disaster markers with color-coded severity levels
✅ **User Authentication** - Login/Signup with sessionStorage (no database)
✅ **Admin Panel** - Configure keywords, API settings, and monitor system logs
✅ **Alert Logs** - Comprehensive table with filtering and sorting capabilities
✅ **Real-time Simulation** - New disaster alerts added every 20-30 seconds
✅ **Responsive Design** - Works on desktop and mobile devices
✅ **Blue Professional Theme** - Clean and modern UI design

## Project Structure

```
disasterwatch/
├── app.py                          # Flask backend
├── requirements.txt                # Python dependencies
├── templates/
│   ├── base.html                   # Base template with navbar
│   ├── home.html                   # Home page
│   ├── login.html                  # Login page
│   ├── signup_user.html            # User signup
│   ├── signup_admin.html           # Admin signup
│   ├── dashboard.html              # Main dashboard with map
│   ├── alerts.html                 # Alert logs table
│   └── admin.html                  # Admin configuration panel
├── static/
│   ├── css/
│   │   └── style.css               # Main stylesheet
│   └── js/
│       ├── auth.js                 # Authentication utilities
│       ├── map.js                  # Leaflet map integration
│       └── dashboard.js            # Dashboard functionality
└── README.md                       # This file
```

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Map**: Leaflet.js with OpenStreetMap tiles
- **UI Framework**: Bootstrap 5 CDN
- **Icons**: Font Awesome 6
- **Storage**: SessionStorage (no database)

## Installation

### Prerequisites

- Python 3.7+
- pip (Python package manager)

### Setup Instructions

1. **Navigate to project directory**
   ```bash
   cd "e:/Degree Notes & Prcticals/3.1 semester/3.1/re/UI Design"
   ```

2. **Create virtual environment (recommended)**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Flask server**
   ```bash
   python app.py
   ```

5. **Open in browser**
   ```
   http://localhost:5000
   ```

## Usage

### Home Page
- View welcome screen with features overview
- Links to Login and Sign Up

### User Authentication
- **Login**: Use any username and password (credentials are not validated in demo mode)
- **User Sign Up**: Create user account with username, email, and password
- **Admin Sign Up**: Create admin account (requires 4+ character admin code)
- **Logout**: Clear session and return to home

### Dashboard
- **Interactive Map**: 70% of screen with disaster markers
  - Red markers = High severity
  - Yellow markers = Medium severity
  - Green markers = Low severity
- **Sidebar**: 30% with filters and alert details
  - Filter by disaster type
  - Filter by severity level
  - Adjust minimum confidence threshold
- **Real-time Updates**: New alerts appear every 20-30 seconds

### Alert Logs
- View all disaster alerts in table format
- Column-coded rows by severity
- Search and filter capabilities
- Sortable columns
- Progress bars for confidence and credibility metrics

### Admin Panel
- **Keywords Configuration**: Add/edit keywords to monitor
- **API Settings**: Configure social media API connections
- **System Logs**: View real-time system activity and events

## API Endpoints

### Public Endpoints
- `GET /` - Home page
- `POST /login` - Login route
- `POST /signup/user` - User signup
- `POST /signup/admin` - Admin signup
- `GET /logout` - Logout

### Protected Endpoints (Requires Authentication)
- `GET /dashboard` - Main dashboard
- `GET /alerts` - Alert logs
- `GET /admin` - Admin panel (requires admin role)

### API Endpoints (JSON)
- `GET /api/alerts` - Fetch all alerts with optional filters
  - Query params: `type`, `severity`, `minConfidence`
- `GET /api/alerts/new` - Get a simulated new alert
- `GET /api/logs` - Fetch system logs
- `POST /api/logs/add` - Add a log entry

## Mock Data

### Sample Alert Structure
```json
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
}
```

### Disaster Types
- Flood
- Earthquake
- Wildfire
- Storm
- Landslide
- Tsunami
- Drought

### Severity Levels
- **High** (85-95% confidence) - Red markers
- **Medium** (60-84% confidence) - Yellow markers
- **Low** (40-59% confidence) - Green markers

## Features Implementation Details

### Authentication
- Uses JavaScript sessionStorage (no server-side sessions)
- User role detection (admin vs regular user)
- Protected routes check authentication before rendering

### Real-time Alerts
- Server generates random new alerts via `/api/alerts/new`
- Client-side JavaScript adds new markers every 20-30 seconds
- Notifications appear when new alerts are detected

### Map Filtering
- Client-side filtering applied to existing alerts
- Filters work without database queries
- Real-time filter updates

### Admin Features
- Keyword management interface
- API configuration forms
- System logs display
- Admin-only access control

## Browser Compatibility

- Chrome/Chromium (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Responsive Breakpoints

- Desktop: Full layout (70% map, 30% sidebar)
- Tablet (768px-991px): Adjusted spacing
- Mobile (<768px): Stacked layout, collapsible sidebar

## Performance Considerations

- Lazy loading of map tiles
- Efficient marker rendering
- Client-side filtering (no server queries)
- Debounced filter updates
- Optimized CSS with minimal reflows

## Future Enhancements

- Real database integration (PostgreSQL/MongoDB)
- Actual social media API connections (Twitter, Reddit)
- Real NLP sentiment analysis
- User notifications and alerts
- Map heat maps
- Advanced analytics dashboard
- Export alerts to CSV/PDF
- User preferences and settings
- Multi-language support

## Troubleshooting

### Port 5000 already in use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :5000
kill -9 <PID>
```

### Styles not loading
- Clear browser cache (Ctrl+Shift+Delete)
- Check if `static/css/style.css` exists
- Check browser console for 404 errors

### Map not displaying
- Check if Leaflet.js CDN is accessible
- Ensure OpenStreetMap tiles CDN is reachable
- Check browser console for JavaScript errors

### Session not persisting
- Check if sessionStorage is enabled in browser
- Try different browser
- Clear browser data and refresh

## License

MIT License - Free to use and modify

## Support

For issues or questions, check the console (F12) for error messages and verify:
1. Flask server is running (`python app.py`)
2. Browser is accessing `http://localhost:5000`
3. JavaScript console has no errors
4. All CDN resources are loading

---

**Created**: January 2026
**Version**: 1.0.0
**Status**: Production Ready (Demo Mode - No Database)
