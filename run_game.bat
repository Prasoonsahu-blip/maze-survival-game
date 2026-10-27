@echo off
title Maze Survival: 3 Killers
echo Launching Maze Survival: 3 Killers...
cd /d "%~dp0"
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Game exited with error code %ERRORLEVEL%.
    pause
)
