@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Velvet AI Agent GUI

echo ==============================================
echo       VELVET - PRIVATE AI AGENT STARTER
echo ==============================================
echo.

where py >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python launcher was not found.
    echo Install Python 3.10 and select "Add Python to PATH".
    pause
    exit /b 1
)

where ollama >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Ollama is not installed or is not available in PATH.
    echo Install Ollama for Windows, restart Antigravity, and run this file again.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/5] Creating Python 3.10 virtual environment...
    py -3.10 -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Python 3.10 was not found.
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate

echo [2/5] Installing or updating Python packages...
python -m pip install --upgrade pip
if errorlevel 1 goto :package_error
pip install -r requirements.txt
if errorlevel 1 goto :package_error

if not exist ".env" copy /Y ".env.example" ".env" >nul

echo [3/5] Starting Ollama...
start "Ollama Server" /min ollama serve >nul 2>&1
timeout /t 3 /nobreak >nul

echo [4/5] Checking local AI models...
ollama list | findstr /I /C:"qwen2.5:3b" >nul
if errorlevel 1 (
    echo Downloading qwen2.5:3b...
    ollama pull qwen2.5:3b
    if errorlevel 1 goto :ollama_error
)

ollama list | findstr /I /C:"nomic-embed-text" >nul
if errorlevel 1 (
    echo Downloading nomic-embed-text...
    ollama pull nomic-embed-text
    if errorlevel 1 goto :ollama_error
)

echo [5/5] Opening Velvet GUI...
start "Velvet AI Agent" ".venv\Scripts\pythonw.exe" main.py
exit /b 0

:package_error
echo.
echo [ERROR] Python package installation failed.
echo Review the error above and run START_VELVET.bat again.
pause
exit /b 1

:ollama_error
echo.
echo [ERROR] Ollama could not download or start the required model.
echo Check internet and make sure Ollama is running.
pause
exit /b 1
