@echo off
setlocal
cd /d "%~dp0"

echo Creating Python virtual environment...
py -3.10 -m venv .venv
if errorlevel 1 (
    echo Python 3.10 was not found. Install Python 3.10 and try again.
    pause
    exit /b 1
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo Package installation failed. Review the error shown above.
    pause
    exit /b 1
)

if not exist ".env" copy /Y ".env.example" ".env" >nul

echo.
echo Pulling local Ollama models. Ollama must already be installed and running.
ollama pull qwen2.5:3b
ollama pull nomic-embed-text

echo.
echo Setup complete. Run run_windows.bat to start Velvet.
pause
