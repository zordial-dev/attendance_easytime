@echo off
echo ==========================================
echo  EasyTime Zoho Connector Status Check
echo ==========================================
echo.
powershell -Command "try { $res = Invoke-RestMethod -Uri 'http://127.0.0.1:8000' -TimeoutSec 3; Write-Host '[STATUS: RUNNING]' -ForegroundColor Green; Write-Host 'Service:' $res.service; Write-Host 'Sync Cutoff:' $res.sync_cutoff; } catch { Write-Host '[STATUS: NOT RUNNING]' -ForegroundColor Red; }"
echo.
echo Recent Logs (Last 10 lines):
echo ------------------------------------------
if exist easytime_zoho.log (
    powershell -Command "Get-Content easytime_zoho.log -Tail 10"
) else (
    echo No log file found yet.
)
echo.
pause
