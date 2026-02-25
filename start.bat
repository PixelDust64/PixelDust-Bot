@echo off
if not exist venv (
    python -m venv venv
    venv\Scripts\pip install -r req.txt
)
call venv\Scripts\activate
python bot.py
pause
