@echo off
setlocal
set "TARGET=%~dp0start_background.vbs"
set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\EasyTimeZohoConnector.lnk"

echo Creating Windows Startup shortcut...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%TARGET%'; $s.WorkingDirectory = '%~dp0'; $s.Save()"

if exist "%SHORTCUT%" (
    echo [SUCCESS] Auto-start on boot configured successfully!
    echo EasyTime Zoho Connector will now automatically start in background when Windows starts.
) else (
    echo [ERROR] Failed to create shortcut.
)
pause
