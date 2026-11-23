@echo off
title HRES Optimizer — Web Application
echo ============================================================
echo   HRES Optimizer v2.0 — Modern Web Interface
echo   Server: http://127.0.0.1:8000
echo ============================================================
echo.
python web_app.py --open
if %errorlevel% neq 0 (
    echo.
    echo Une erreur est survenue lors du lancement du serveur web.
    echo Veuillez installer les dependances: pip install -r requirements.txt
    pause
)
