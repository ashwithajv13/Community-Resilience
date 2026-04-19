@echo off
REM ResilienceChain AI - Setup Script for Shared Installation
REM Run this on the computer that will run the backend server

echo ======================================
echo ResilienceChain AI - Quick Setup
echo ======================================
echo.

REM Find Python
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

REM Show Python version
echo Found Python:
python --version
echo.

REM Install dependencies
echo Installing required packages...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install packages
    pause
    exit /b 1
)

echo.
echo ======================================
echo Setup Complete!
echo ======================================
echo.
echo Next steps:
echo.
echo 1. Find your computer's IP address:
echo    Command Prompt: ipconfig
echo    Look for IPv4 address (e.g., 192.168.1.100)
echo.
echo 2. Update frontend URLs on other computers:
echo    Edit: frontend/static/js/config.js
echo    Set: const API_BASE = "http://YOUR_IP:5000"
echo.
echo 3. Start the backend server:
echo    Command Prompt: python backend/app.py
echo.
echo 4. Access from other computers:
echo    Browser: http://YOUR_IP:5000/chat
echo.
pause
