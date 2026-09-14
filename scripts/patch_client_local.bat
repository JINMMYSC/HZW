@echo off
setlocal
cd /d "%~dp0.."
if "%~1"=="" (
  echo Usage: patch_client_local.bat path\to\hzw-touch-360x360.jar
  pause
  exit /b 2
)
python tools\patch_client.py "%~1" --out "%~dpn1-localhost.jar" --host 127.0.0.1
pause
