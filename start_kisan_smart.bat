@echo off
setlocal

echo.
echo ========================================================
echo   Kisan Smart - AI Fertilizer Advisor
echo   Starting Backend and Frontend...
echo ========================================================
echo.

:: Check if virtual environment exists
if exist .venv\Scripts\activate.bat (
    echo [INFO] Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo [WARNING] .venv not found. Using system python.
)

:: Pre-loading check
echo [INFO] Initializing ML models...

:: Start the Flask application
:: We use 'start' to run it in a new window so this window remains open for logs
echo [INFO] Launching server on http://localhost:5005
echo [INFO] Press Ctrl+C in the new window to stop the server.

:: Open browser after a short delay
start /b cmd /c "timeout /t 5 >nul && start http://localhost:5005"

:: Run the app
python app.py

pause
