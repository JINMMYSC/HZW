@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
title HZW V860 Compatibility Server
chcp 65001 >nul 2>nul

echo ============================================================
echo HZW V860 Phase 6 compatibility server
echo TCP : 0.0.0.0:5926
echo HTTP: 0.0.0.0:8080
echo World: corrected cell3 walkability + type7 position sync
echo NPC  : key 5 dialogue enabled near guide
echo HZW terminology: Deputy / Battle Skills / Guild
echo ============================================================
echo.

set "PY_CMD="
python -c "import sys; print(sys.version)" >nul 2>nul
if not errorlevel 1 set "PY_CMD=python"

if not defined PY_CMD (
  py -3 -c "import sys; print(sys.version)" >nul 2>nul
  if not errorlevel 1 set "PY_CMD=py -3"
)

if not defined PY_CMD (
  echo [ERROR] Python 3 could not be started.
  echo Install Python 3 and enable Add Python to PATH.
  echo.
  echo This window will stay open so the error can be photographed.
  pause
  exit /b 1
)

echo [OK] Python launcher: %PY_CMD%
echo [INFO] Starting server...
echo.

%PY_CMD% phase3_server.py --debug
set "SERVER_EXIT=%ERRORLEVEL%"

echo.
echo ============================================================
if "%SERVER_EXIT%"=="0" (
  echo [INFO] Server stopped normally.
) else (
  echo [ERROR] Server exited with code %SERVER_EXIT%.
  echo Possible causes: ports 5926/8080 already in use, Python/import error,
  echo or a startup exception. Photograph everything above this line.
)
echo ============================================================
echo.
pause
exit /b %SERVER_EXIT%
