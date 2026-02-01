#!/bin/bash

# DisasterWatch - Setup and Verification Script for macOS/Linux

echo ""
echo "============================================"
echo "  DisasterWatch Setup Verification"
echo "============================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.7+ from https://www.python.org/"
    exit 1
fi

echo "[OK] Python 3 is installed"
python3 --version
echo ""

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "[ERROR] pip3 is not installed"
    exit 1
fi

echo "[OK] pip3 is available"
pip3 --version
echo ""

# Check if requirements.txt exists
if [ ! -f requirements.txt ]; then
    echo "[ERROR] requirements.txt not found"
    echo "Make sure you're in the DisasterWatch directory"
    exit 1
fi

echo "[OK] requirements.txt found"
echo ""

# Check if Flask is already installed
if python3 -c "import flask" &> /dev/null; then
    echo "[OK] Flask is already installed"
else
    echo "[INFO] Flask not found, installing dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install dependencies"
        exit 1
    fi
fi

echo ""
echo "[OK] All dependencies are available"
echo ""

# Check if templates and static folders exist
if [ ! -d templates ]; then
    echo "[ERROR] templates folder not found"
    exit 1
fi

if [ ! -d static ]; then
    echo "[ERROR] static folder not found"
    exit 1
fi

echo "[OK] Project structure is valid"
echo ""

# Check key template files
for file in templates/base.html templates/home.html templates/dashboard.html templates/login.html; do
    if [ ! -f "$file" ]; then
        echo "[ERROR] Missing template: $file"
        exit 1
    fi
done

echo "[OK] All template files found"
echo ""

# Check CSS and JS files
for file in static/css/style.css static/js/auth.js static/js/map.js static/js/dashboard.js; do
    if [ ! -f "$file" ]; then
        echo "[ERROR] Missing asset: $file"
        exit 1
    fi
done

echo "[OK] All CSS and JavaScript files found"
echo ""

# Check app.py
if [ ! -f app.py ]; then
    echo "[ERROR] app.py not found"
    exit 1
fi

echo "[OK] app.py found"
echo ""

echo "============================================"
echo "  Setup Verification Complete!"
echo "============================================"
echo ""
echo "Everything looks good! You can now run:"
echo ""
echo "  python3 app.py"
echo ""
echo "Then visit: http://localhost:5000"
echo ""
