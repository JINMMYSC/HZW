@echo off
setlocal
cd /d "%~dp0.."
if "%~2"=="" (
  echo Usage: patch_client_lan.bat path\to\hzw-touch-360x360.jar COMPUTER_LAN_IP
  echo Example: patch_client_lan.bat hzw-touch-360x360.jar 192.168.1.50
  pause
  exit /b 2
)
python tools\patch_client.py "%~1" --out "%~dpn1-lan.jar" --host "%~2"
pause
