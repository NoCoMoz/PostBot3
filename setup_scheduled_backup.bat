@echo off
echo Setting up daily backup task...
powershell.exe -ExecutionPolicy Bypass -File "%~dp0setup_backup_task.ps1"

echo.
echo Press any key to exit...
pause > nul
