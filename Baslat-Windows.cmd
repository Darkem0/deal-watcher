@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_windows.ps1" -ProjectRoot "%~dp0." %*
set "dw_exit=%ERRORLEVEL%"
if /I "%~1"=="-Check" exit /b %dw_exit%
pause
exit /b %dw_exit%
