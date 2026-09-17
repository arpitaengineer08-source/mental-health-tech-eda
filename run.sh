#!/usr/bin/env bash
# One-click launch for the dashboard.
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Creating a virtual environment in .venv ..."
  python3 -m venv .venv
fi
source .venv/bin/activate
echo "Installing requirements (first run only, takes a minute) ..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "Starting the dashboard at http://localhost:8501 ..."
streamlit run app.py
