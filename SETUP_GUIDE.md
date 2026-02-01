# DisasterWatch - Environment Setup Guide

## 🖥️ System Requirements

### Minimum Requirements
- **OS**: Windows, macOS, or Linux
- **Python**: 3.7+ (3.9+ recommended)
- **RAM**: 512 MB
- **Disk Space**: 100 MB
- **Browser**: Chrome, Firefox, Safari, or Edge (latest)
- **Internet**: Required for CDN resources and map tiles

### Recommended Requirements
- **Python**: 3.9 or 3.10
- **RAM**: 2+ GB
- **Disk Space**: 500 MB
- **Browser**: Chrome or Firefox latest version

---

## 📥 Installation Guide

### Option 1: Windows Setup

#### 1.1 Install Python

**Method A: From python.org**
1. Visit https://www.python.org/downloads/
2. Download "Windows installer (64-bit)"
3. Run the installer
4. ✅ **IMPORTANT**: Check "Add Python to PATH"
5. Click "Install Now"
6. Wait for installation to complete

**Method B: From Microsoft Store**
1. Open Microsoft Store
2. Search for "Python 3.10" or "Python 3.11"
3. Click "Install"
4. Wait for installation

#### 1.2 Verify Installation

Open Command Prompt and run:
```bash
python --version
pip --version
```

You should see:
```
Python 3.9.x (or higher)
pip 21.x.x (or higher)
```

#### 1.3 Install Flask

```bash
cd "e:\Degree Notes & Prcticals\3.1 semester\3.1\re\UI Design"
pip install -r requirements.txt
```

#### 1.4 Run the Application

```bash
python app.py
```

Expected output:
```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

#### 1.5 Open in Browser

Visit: **http://localhost:5000**

---

### Option 2: macOS Setup

#### 2.1 Install Python

**Method A: Using Homebrew (Recommended)**

First, install Homebrew if not already installed:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then install Python:
```bash
brew install python
```

**Method B: Direct Download**
1. Visit https://www.python.org/downloads/
2. Download "macOS 64-bit universal2 installer"
3. Run the installer
4. Follow on-screen instructions

#### 2.2 Verify Installation

```bash
python3 --version
pip3 --version
```

#### 2.3 Create Virtual Environment (Recommended)

```bash
cd "/path/to/UI Design"
python3 -m venv venv
source venv/bin/activate
```

#### 2.4 Install Flask

```bash
pip3 install -r requirements.txt
```

#### 2.5 Run the Application

```bash
python3 app.py
```

#### 2.6 Open in Browser

Visit: **http://localhost:5000**

---

### Option 3: Linux Setup

#### 3.1 Install Python

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**Fedora/CentOS:**
```bash
sudo dnf install python3 python3-pip
```

**Arch:**
```bash
sudo pacman -S python python-pip
```

#### 3.2 Verify Installation

```bash
python3 --version
pip3 --version
```

#### 3.3 Create Virtual Environment (Recommended)

```bash
cd "/path/to/UI Design"
python3 -m venv venv
source venv/bin/activate
```

#### 3.4 Install Flask

```bash
pip3 install -r requirements.txt
```

#### 3.5 Run the Application

```bash
python3 app.py
```

#### 3.6 Open in Browser

Visit: **http://localhost:5000**

---

## 🔧 Virtual Environment Setup (Optional but Recommended)

### Why Use Virtual Environment?
- Isolates project dependencies
- Prevents conflicts with other projects
- Makes project portable
- Easier dependency management

### Setup Virtual Environment

#### Windows:
```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

#### macOS/Linux:
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip3 install -r requirements.txt

# Run application
python3 app.py
```

### Deactivate Virtual Environment
```bash
deactivate
```

---

## 🌐 Browser Configuration

### Enable JavaScript
- Chrome: Enabled by default
- Firefox: Enabled by default
- Safari: Menu → Develop → Enable JavaScript
- Edge: Enabled by default

### Clear Browser Cache (If Needed)
| Browser | Shortcut |
|---------|----------|
| Chrome | Ctrl + Shift + Delete |
| Firefox | Ctrl + Shift + Delete |
| Safari | Cmd + Shift + Delete |
| Edge | Ctrl + Shift + Delete |

### Recommended Browser Settings
- ✅ Enable JavaScript
- ✅ Allow cookies
- ✅ Allow popups (for new windows)
- ✅ Allow camera/microphone (if using in future)

---

## 🔐 Firewall & Network

### Port Configuration
- **Default Port**: 5000
- **Protocol**: HTTP
- **Firewall**: Allow port 5000 for local access

### If Port 5000 is In Use

#### Windows:
```bash
# Find what's using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID)
taskkill /PID <PID> /F

# Or use a different port
python app.py --port 5001
```

#### macOS/Linux:
```bash
# Find what's using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or use a different port
python3 app.py --port 5001
```

---

## 📦 Dependencies

### Required Packages
```
Flask==2.3.3
Werkzeug==2.3.7
```

### External CDN Resources (Auto-loaded)
- Bootstrap 5 CSS (CDN)
- Leaflet.js (CDN)
- Font Awesome Icons (CDN)
- OpenStreetMap Tiles (Auto-loaded)

### Internet Connection
Required for:
- Bootstrap framework
- Leaflet map library
- Font Awesome icons
- OpenStreetMap tiles

---

## 🧪 Troubleshooting Installation

### "Python not found"
**Solution**:
- Check if Python is installed: `python --version`
- Add Python to PATH environment variable
- Reinstall Python and check "Add Python to PATH"

### "pip not found"
**Solution**:
- Update pip: `python -m pip install --upgrade pip`
- Use python -m pip directly: `python -m pip install -r requirements.txt`

### "Flask not installed"
**Solution**:
```bash
pip install --upgrade pip
pip install Flask==2.3.3
```

### "Permission denied" (macOS/Linux)
**Solution**:
```bash
# Use sudo (not recommended for venv)
sudo pip3 install -r requirements.txt

# Or better: use virtual environment
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### "Port 5000 already in use"
**Solution**:
```bash
# Kill the process using port 5000
# See instructions above

# Or use different port
python app.py --port 8000
```

### "Can't access localhost:5000"
**Solution**:
- Make sure Flask server is running
- Try http://127.0.0.1:5000 instead
- Check firewall settings
- Restart Flask server

### "Map not loading"
**Solution**:
- Check internet connection
- Clear browser cache
- Disable VPN
- Check browser console for errors
- Try different browser

### "Styles not loading"
**Solution**:
- Clear browser cache (Ctrl+Shift+Delete)
- Hard refresh page (Ctrl+F5)
- Check if static folder exists
- Restart Flask server

---

## 📋 Post-Installation Checklist

- [ ] Python installed (3.7+)
- [ ] pip installed and updated
- [ ] Flask installed (2.3.3+)
- [ ] Project folder is "UI Design"
- [ ] templates folder exists
- [ ] static folder with css and js exists
- [ ] app.py exists
- [ ] requirements.txt exists
- [ ] Browser supports JavaScript
- [ ] Port 5000 is available

---

## 🚀 Quick Start Command

After installation, single command to run:

**Windows:**
```bash
python app.py
```

**macOS/Linux:**
```bash
python3 app.py
```

Then visit: **http://localhost:5000**

---

## 🔄 Regular Maintenance

### Weekly
- Clear browser cache
- Check for updates: `pip install --upgrade Flask`

### Monthly
- Review logs for errors
- Update dependencies
- Backup configuration files

### Before Deployment
- Test all features
- Clear old sessions
- Update documentation
- Run verification script

---

## 💾 Backup & Recovery

### Backup Important Files
- app.py
- templates/ folder
- static/ folder
- requirements.txt

### Recovery
If something breaks:
1. Delete venv folder (if using virtual env)
2. Recreate: `python -m venv venv`
3. Reinstall: `pip install -r requirements.txt`
4. Run: `python app.py`

---

## 🌐 Network Access

### Local Only (Default)
- Accessible at: http://localhost:5000
- Accessible at: http://127.0.0.1:5000

### Network Access (Advanced)
To allow other computers:
```python
# In app.py, change the last line to:
app.run(debug=True, host='0.0.0.0', port=5000)
```

Then access from other computers at:
```
http://<YOUR_IP_ADDRESS>:5000
```

**⚠️ WARNING**: Only do this on trusted networks!

---

## 🔒 Security Notes

### For Development Only
- Debug mode is ON
- No authentication enforced on backend
- SessionStorage only (no real sessions)
- No HTTPS configured

### Before Production
- Set `debug=False` in app.py
- Implement real authentication
- Set up HTTPS/SSL
- Configure CORS properly
- Add rate limiting
- Implement input validation
- Set up database
- Configure firewall

---

## 📞 Support

### Getting Help

1. **Check Installation**:
   ```bash
   python --version
   pip --version
   python -m pip show Flask
   ```

2. **Check Project Structure**:
   - Verify all files exist
   - Run setup_verify.bat (Windows)
   - Run setup_verify.sh (macOS/Linux)

3. **Check Browser**:
   - Open Developer Tools (F12)
   - Check Console for errors
   - Check Network tab

4. **Check Server Logs**:
   - Look at terminal where Flask is running
   - Check for error messages

---

## ✅ Installation Success Indicators

**You'll know installation is successful when:**

1. ✅ Command `python app.py` runs without errors
2. ✅ Terminal shows "Running on http://127.0.0.1:5000"
3. ✅ Browser opens http://localhost:5000 successfully
4. ✅ You see the DisasterWatch home page
5. ✅ Navigation works
6. ✅ Login form loads
7. ✅ Map displays on dashboard

---

**You're all set! Happy disaster monitoring! 🌍**
