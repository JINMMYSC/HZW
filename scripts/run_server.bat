@echo off
setlocal
cd /d "%~dp0.."
where python >nul 2>nul || (
  echo [ERROR] Python 3 was not found in PATH.
  pause
  exit /b 1
)
echo Starting HZW V860 Phase 4 compatibility server...
echo TCP: 0.0.0.0:5926   HTTP: 0.0.0.0:8080
echo Visible world: bundled ground tiles + character sprite enabled
echo HZW terminology: 副官 / 战斗技能 / 公会
python phase3_server.py --debug
pause
