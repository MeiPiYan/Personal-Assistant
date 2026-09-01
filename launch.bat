@echo off
title AI Assistant
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python main.py
if errorlevel 1 (
    echo.
    echo [Error] Application exited with error.
    pause
)
