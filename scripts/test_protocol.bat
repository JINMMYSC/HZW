@echo off
setlocal
cd /d "%~dp0.."
python -m unittest discover -s tests -v
if errorlevel 1 pause & exit /b 1
start "HZW V860 Phase3 server" cmd /k "cd /d \"%CD%\" && python phase3_server.py --debug"
timeout /t 2 /nobreak >nul
python tools\smoke_world_client.py
pause
