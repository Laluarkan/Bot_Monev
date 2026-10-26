@echo off
title Monev MagangHub Telegram Bot
echo Menjalankan Monev MagangHub Bot...
cd /d "%~dp0"
call .\venv\Scripts\activate.bat
python -u monev_bot.py
pause
