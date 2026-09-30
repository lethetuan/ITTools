@echo off
title IT Tool LTT - Le The Tuan
cd /d "%~dp0bmat_tools"
echo Starting IT Tool LTT...
echo Author: Le The Tuan ^| Phone/Zalo: 0352 194 195
echo Website: https://lethetuanpc.blogspot.com
echo Telegram: https://t.me/lethetuanpc
echo.
python main.py
if errorlevel 1 (
    echo.
    echo Error: Python not found or script failed.
    echo Please install Python 3.8+ and try again.
    pause
)
