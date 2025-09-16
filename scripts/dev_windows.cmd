@echo off
python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt
start cmd /k python luna_simulator\simulator.py --broker 127.0.0.1 --port 1883
python nucleus_client\main.py
