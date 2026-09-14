@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
chcp 65001 >nul 2>nul
if "%~1"=="" (
  echo Usage: scripts\build_windmill_marine_package.bat path\to\hzw-touch-360x360.jar [host]
  pause
  exit /b 1
)
set "HOST=%~2"
if "%HOST%"=="" set "HOST=127.0.0.1"
set "PY="
python -c "import sys" >nul 2>nul && set "PY=python"
if not defined PY py -3 -c "import sys" >nul 2>nul && set "PY=py -3"
if not defined PY (
  echo [ERROR] Python 3 not found.
  pause
  exit /b 1
)
%PY% tools\build_local_package.py "%~1" --host "%HOST%"
set "EC=%ERRORLEVEL%"
if not "%EC%"=="0" (
  echo [ERROR] Package build failed with code %EC%.
) else (
  echo [OK] Package created under dist\HZW-V860-Windmill-Marine
)
pause
exit /b %EC%
