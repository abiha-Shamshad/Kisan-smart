@echo off
setlocal

:: ── Kisan Smart Startup Script (Windows Optimized) ──────────────────────────
:: This script starts the Flask backend and background services (Celery/Beat).
:: It now uses a SQLite-based broker as a fallback if Redis is not installed.

echo ==========================================================
echo           Starting Kisan Smart — System Launch
echo ==========================================================

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

:: 2. Start Celery Worker + Beat (Unified Command)
:: Note: On Windows, Celery worker requires '-P solo' or '-P eventlet' due to fork issues.
echo [STEP 2] Starting Celery (Automated Alerts & Tasks)...
start "Kisan-Celery" cmd /k "celery -A website.api.v1.pest.services.scheduler worker --beat --loglevel=info -P solo"
timeout /t 3 /nobreak > nul

:: 3. Start Flask Backend
echo [STEP 3] Starting Flask Backend on http://127.0.0.1:5005
echo.
echo Dashboard: http://127.0.0.1:5005/app/dashboard.html
echo Login:     http://127.0.0.1:5005/app/login.html
echo.
python app.py

pause
