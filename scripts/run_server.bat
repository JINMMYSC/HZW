@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
title HZW V860 Windmill + Marine Server
chcp 65001 >nul 2>nul

echo ============================================================
echo HZW V860 - Windmill Village + Marine Base restoration
echo TCP : 0.0.0.0:5926
echo HTTP: 0.0.0.0:8080
echo World: multi-area chapter maps + original V860 resources
echo Move : client-local smooth walk; server sync/correction only
echo Quest: Windmill main + Marine main + 11 Marine side quests
echo Save : data\players\*.json
echo HZW  : Deputy / Battle Skills / Guild
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
  pause
  exit /b 1
)

echo [OK] Python launcher: %PY_CMD%
echo [INFO] Starting two-chapter server...
echo.
%PY_CMD% chapter_server_v2.py --debug
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
