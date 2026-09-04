@echo off
setlocal EnableExtensions
cd /d "%~dp0\.."

echo ============================================================
echo RAT VISION v1.2.0-beta.1 - One-click Windows build
echo ============================================================
echo.
echo System Python is NOT required.
echo Official CPython 3.13.15 x64 with Tcl/Tk will be installed into this folder.
echo.

where powershell.exe >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Windows PowerShell was not found.
  echo This builder requires the PowerShell included with Windows 10/11.
  echo.
  pause
  exit /b 1
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0build-windows.ps1"
set "BUILD_RC=%ERRORLEVEL%"

if not "%BUILD_RC%"=="0" (
  echo.
  echo ============================================================
  echo [ERROR] RAT VISION build failed.
  echo See build.log in this folder for diagnostics.
  echo ============================================================
  echo.
  pause
  exit /b %BUILD_RC%
)

echo.
echo ============================================================
echo [OK] RAT VISION build completed.
echo Output: dist\RAT VISION\RAT VISION.exe
echo ============================================================
echo.
pause
exit /b 0
