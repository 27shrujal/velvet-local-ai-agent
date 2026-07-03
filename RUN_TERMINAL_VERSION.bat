@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    echo Virtual environment not found. Run START_VELVET.bat first.
    pause
    exit /b 1
)
call .venv\Scripts\activate
python terminal_main.py
pause
