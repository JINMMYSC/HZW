@echo off
setlocal
cd /d "%~dp0.."
where python >nul 2>nul || (
  echo [ERROR] Python 3 was not found in PATH.
  pause
  exit /b 1
)
echo Starting HZW V860 compatibility server...
echo TCP: 0.0.0.0:5926   HTTP: 0.0.0.0:8080
python server.py --debug
pause
