@echo off
setlocal
cd /d "%~dp0.."
where python >nul 2>nul || (
  echo [ERROR] Python 3 was not found in PATH.
  pause
  exit /b 1
)
echo Starting HZW V860 Phase 3 compatibility server...
echo TCP: 0.0.0.0:5926   HTTP: 0.0.0.0:8080
echo World bootstrap: map + player entity enabled
python phase3_server.py --debug
pause
