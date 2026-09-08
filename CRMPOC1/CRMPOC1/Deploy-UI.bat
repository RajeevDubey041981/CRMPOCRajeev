@echo off
setlocal
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0deploy\deploy-ui.ps1"
if errorlevel 1 (
  echo.
  echo UI deployment failed.
  pause
  exit /b 1
)
echo.
echo UI deployment completed.
pause
