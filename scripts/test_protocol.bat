@echo off
setlocal
cd /d "%~dp0.."
python -m unittest discover -s tests -v
if errorlevel 1 pause & exit /b 1
start "HZW V860 server" cmd /k "cd /d \"%CD%\" && python server.py --debug"
timeout /t 2 /nobreak >nul
python tools\smoke_client.py
pause
