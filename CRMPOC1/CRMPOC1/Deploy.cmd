@echo off
setlocal
cd /d "%~dp0"
py scripts\deploy.py
if errorlevel 1 (
  echo.
  echo Deploy failed.
  pause
  exit /b 1
)
echo.
pause
