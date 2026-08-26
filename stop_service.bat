@echo off
echo Stopping EasyTime Zoho Connector on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Terminating PID %%a...
    taskkill /f /pid %%a >nul 2>&1
)
echo Done.
pause
