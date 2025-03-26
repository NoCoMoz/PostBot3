@echo off
echo Downloading latest survey responses...
powershell.exe -ExecutionPolicy Bypass -File "%~dp0download_backups.ps1" -Latest

echo.
echo Backup downloaded to downloaded_backups folder
echo Press any key to exit...
pause > nul
