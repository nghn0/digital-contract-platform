@echo off
title Digital Contract Platform - Setup
cls

echo ================================================================
echo       Digital Contract Platform - Project Setup
echo ================================================================
echo.
echo This script will install all dependencies for:
echo   1. Frontend (Next.js)
echo   2. Backend (Node.js/Express)
echo   3. AI Model (Python)
echo.

echo [1/2] Installing Frontend and Backend dependencies via npm workspaces...
call npm install
if %ERRORLEVEL% neq 0 (
    echo [ERROR] npm install failed. Please make sure Node.js is installed.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/2] Setting up Python virtual environment for the AI Model...
cd model

:: Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python.
    pause
    exit /b %ERRORLEVEL%
)

:: Create virtual environment
echo Creating .venv in model directory...
python -m venv .venv

:: Activate and install requirements
echo Installing Python dependencies from requirements.txt...
call .venv\Scripts\pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install Python dependencies.
    pause
    exit /b %ERRORLEVEL%
)

cd ..
echo.
echo ================================================================
echo   Setup Complete!
echo   You can now use 'start_dev.bat' to launch the application.
echo ================================================================
pause
