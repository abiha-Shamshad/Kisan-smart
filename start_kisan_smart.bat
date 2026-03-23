@echo off
setlocal
cd /d "%~dp0"

:: ── Kisan Smart Startup Script (Windows Optimized) ──────────────────────────
:: This script starts the Flask backend and background services (Celery/Beat).
:: It now uses a SQLite-based broker as a fallback if Redis is not installed.

echo ==========================================================
echo           Starting Kisan Smart — System Launch
echo ==========================================================

:: Set Python path to current directory to ensure modules are found
set PYTHONPATH=.

:: 1. Try to start Redis (Optional)
echo [STEP 1] Checking for Redis...
where redis-server >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Redis found! Starting...
    start "Kisan-Redis" cmd /k "redis-server"
) else (
    echo Redis not found. System will fallback to Database Broker (SQLite).
)
timeout /t 2 /nobreak > nul

:: 2. Start Celery Worker
echo [STEP 2] Starting Celery Worker...
start "Kisan-Worker" cmd /k "celery -A website.api.v1.pest.services.scheduler worker --loglevel=info -P solo"

:: 3. Start Celery Beat
echo [STEP 3] Starting Celery Beat (Scheduler)...
start "Kisan-Beat" cmd /k "celery -A website.api.v1.pest.services.scheduler beat --loglevel=info"
timeout /t 3 /nobreak > nul

:: 4. Start Flask Backend
echo [STEP 4] Starting Flask Backend on http://127.0.0.1:5005
echo.
echo Dashboard: http://127.0.0.1:5005/app/dashboard.html
echo Login:     http://127.0.0.1:5005/app/login.html
echo.
python app.py
if %ERRORLEVEL% NEQ 0 (
    echo Flask failed to start. 
    pause
)

pause
