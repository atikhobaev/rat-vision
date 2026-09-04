@echo off
setlocal
cd /d "%~dp0\.."
set "PYTHONUTF8=1"

echo [1/3] Checking Python...
python --version || exit /b 1

echo [2/3] Running tests...
python -m pytest -q || exit /b 1

echo [3/3] Compiling Python sources...
python -m compileall -q ratvision || exit /b 1

echo [OK] RAT VISION verification passed.
endlocal
