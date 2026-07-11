@echo off
title HRES Optimizer
echo Lancement de l'application HRES Optimizer...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo Une erreur est survenue lors de l'execution de l'application.
    echo Veuillez installer les dependances requises: pip install -r requirements.txt
    pause
)
