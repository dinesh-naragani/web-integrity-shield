@echo off
REM Start Level-2 Deep Analysis Service (Windows)

echo ==========================================
echo Level-2 Deep Analysis Service
echo Web Integrity Shield - Phase 3
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo OK: %PYTHON_VERSION%

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat
echo OK: Virtual environment activated

REM Install/upgrade dependencies
echo Installing dependencies...
pip install -q -r requirements.txt
echo OK: Dependencies installed

REM Start service
echo.
echo Starting Level-2 Service on port 8001...
echo API Docs: http://localhost:8001/docs
echo Health: http://localhost:8001/health
echo.
echo Press Ctrl+C to stop the service
echo.

python level2_service.py
pause
