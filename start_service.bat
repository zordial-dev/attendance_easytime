@echo off
cd /d "%~dp0"
title EasyTime Zoho Connector
echo Starting EasyTime Zoho Connector...
.\venv\Scripts\python.exe server.py
pause
