@echo off
echo Starting Kisan Smart...
pip install -r requirements.txt
start http://localhost:5005
python app.py
pause
