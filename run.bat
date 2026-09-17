@echo off
REM One-click launch for the dashboard.
cd /d "%~dp0"

if not exist ".venv" (
  echo Creating a virtual environment in .venv ...
  python -m venv .venv
)
call .venv\Scripts\activate.bat
echo Installing requirements (first run only, takes a minute) ...
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt
echo Starting the dashboard at http://localhost:8501 ...
streamlit run app.py
pause
