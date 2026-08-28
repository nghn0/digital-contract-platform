@echo off
title Digital Contract Platform - Development Launcher
cls

echo ================================================================
echo       Digital Contract Platform - Development Environment
echo ================================================================
echo.

:: Clean up old / existing processes occupying the required ports
echo [0/3] Clearing any existing processes on ports 3000, 5001, 50051...

for /f "tokens=5" %%a in ('netstat -aon ^| findstr /r ":3000\>"') do (
    taskkill /F /PID %%a >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -aon ^| findstr /r ":5001\>"') do (
    taskkill /F /PID %%a >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -aon ^| findstr /r ":50051\>"') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo Existing port conflicts cleared!
echo.
echo Starting services in separate terminal windows:
echo   1. AI Model Server (Python gRPC on port 50051)
echo   2. Backend Server  (Node.js / Express on port 5001)
echo   3. Frontend Server (Next.js on http://localhost:3000)
echo.
echo ================================================================

:: 1. Start AI Model gRPC Server
echo [1/3] Launching AI Model gRPC Server...
start "AI Model Server (Port 50051)" cmd /k "cd /d ""%~dp0model"" && echo [AI Model Server] Starting... && (if exist venv\Scripts\python.exe (venv\Scripts\python.exe grpc_server.py) else if exist .venv\Scripts\python.exe (.venv\Scripts\python.exe grpc_server.py) else (python grpc_server.py || py grpc_server.py))"

:: Give the gRPC server a short moment to initialize
timeout /t 2 /nobreak >nul

:: 2. Start Backend (Express with nodemon)
echo [2/3] Launching Node.js Backend Server...
start "Backend API Server (Port 5001)" cmd /k "cd /d ""%~dp0backend"" && echo [Backend Server] Starting... && npm run dev"

:: Give backend a short moment
timeout /t 2 /nobreak >nul

:: 3. Start Frontend (Next.js dev server with hot reload)
echo [3/3] Launching Next.js Frontend...
start "Frontend Next.js (Port 3000)" cmd /k "cd /d ""%~dp0frontend"" && echo [Frontend Server] Starting... && npm run dev"

echo.
echo ================================================================
echo   All services have been launched!
echo   - Frontend: http://localhost:3000
echo   - Backend:  http://localhost:5001
echo   - Model:    127.0.0.1:50051
echo.
echo   Hot-reloading is active: any changes in /frontend or /backend
echo   will update automatically without restarting.
echo ================================================================
echo.
echo Waiting 5 seconds before opening browser...
timeout /t 5 /nobreak >nul

start http://localhost:3000

echo.
echo Services are running. You can close this launcher window at any time.
