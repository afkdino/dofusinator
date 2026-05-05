@echo off
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)
cd src
python main.py
pause
