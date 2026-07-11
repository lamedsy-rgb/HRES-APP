@echo off
title HRES Optimizer
echo Starting HRES Optimizer GUI Application...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo An error occurred while running the application.
    echo Please make sure all requirements are installed: pip install -r requirements.txt
    pause
)
