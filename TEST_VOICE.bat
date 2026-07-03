@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Run START_VELVET.bat once before this test.
    pause
    exit /b 1
)
call ".venv\Scripts\activate.bat"
python voice_test.py
pause
