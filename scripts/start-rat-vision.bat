@echo off
setlocal
cd /d "%~dp0\.."
set "PYTHONUTF8=1"

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python was not found in PATH.
  echo Install Python 3.13 x64, then run this file again.
  pause
  exit /b 1
)

python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3,13) else 1)"
if errorlevel 1 (
  echo [ERROR] RAT VISION requires Python 3.13 x64.
  python --version
  pause
  exit /b 1
)

python -m ratvision
if errorlevel 1 (
  echo.
  echo [ERROR] RAT VISION exited with an error.
  pause
  exit /b 1
)
endlocal
