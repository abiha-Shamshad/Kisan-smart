@echo off
echo Starting Kisan Smart...
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)
pip install -r requirements.txt
start http://localhost:5005
python app.py
pause
