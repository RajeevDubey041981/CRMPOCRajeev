@echo off
setlocal
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0deploy\deploy-api-service.ps1"
if errorlevel 1 (
  echo.
  echo API service deployment failed.
  pause
  exit /b 1
)
echo.
echo API service deployment completed.
pause
