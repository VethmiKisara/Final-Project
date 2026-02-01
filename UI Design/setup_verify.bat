@echo off
REM DisasterWatch - Setup and Verification Script for Windows

echo.
echo ============================================
echo  DisasterWatch Setup Verification
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python is installed
python --version

REM Check if pip is available
pip --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] pip is not installed
    pause
    exit /b 1
)

echo [OK] pip is available
pip --version
echo.

REM Check if requirements.txt exists
if not exist requirements.txt (
    echo [ERROR] requirements.txt not found
    echo Make sure you're in the DisasterWatch directory
    pause
    exit /b 1
)

echo [OK] requirements.txt found
echo.

REM Check if Flask is already installed
pip show flask >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Flask is already installed
) else (
    echo [INFO] Flask not found, installing dependencies...
    pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo [OK] All dependencies are available
echo.

REM Check if templates and static folders exist
if not exist templates (
    echo [ERROR] templates folder not found
    pause
    exit /b 1
)

if not exist static (
    echo [ERROR] static folder not found
    pause
    exit /b 1
)

echo [OK] Project structure is valid
echo.

REM Check key template files
for %%F in (base.html home.html dashboard.html login.html) do (
    if not exist templates\%%F (
        echo [ERROR] Missing template: templates\%%F
        pause
        exit /b 1
    )
)

echo [OK] All template files found
echo.

REM Check CSS and JS files
for %%F in (css\style.css js\auth.js js\map.js js\dashboard.js) do (
    if not exist static\%%F (
        echo [ERROR] Missing asset: static\%%F
        pause
        exit /b 1
    )
)

echo [OK] All CSS and JavaScript files found
echo.

REM Check app.py
if not exist app.py (
    echo [ERROR] app.py not found
    pause
    exit /b 1
)

echo [OK] app.py found
echo.

echo ============================================
echo  Setup Verification Complete!
echo ============================================
echo.
echo Everything looks good! You can now run:
echo.
echo   python app.py
echo.
echo Then visit: http://localhost:5000
echo.
pause
