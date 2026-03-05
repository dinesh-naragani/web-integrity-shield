@echo off
setlocal

set "ROOT=%~dp0"
set "LEVEL2_DIR=%ROOT%level2-service"
set "BACKEND_DIR=%ROOT%backend-java"

echo ==========================================
echo   Web Integrity Shield - Start All
echo ==========================================
echo Root: %ROOT%
echo.

where java >nul 2>&1
if errorlevel 1 (
    echo ERROR: Java not found in PATH.
    echo Install JDK 17+ and reopen terminal.
    pause
    exit /b 1
)

where mvn >nul 2>&1
if errorlevel 1 (
    echo ERROR: Maven not found in PATH.
    echo Install Maven 3.6+ and reopen terminal.
    pause
    exit /b 1
)

where py >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python launcher (py) not found in PATH.
    echo Install Python 3.11+ and reopen terminal.
    pause
    exit /b 1
)

echo [1/2] Starting Level-2 Python service in new window...
start "WSI Level2 (8001)" cmd /k "cd /d ""%LEVEL2_DIR%"" && if not exist ""venv311\Scripts\python.exe"" (py -3.11 -m venv venv311) && ""venv311\Scripts\python.exe"" -m pip install -q -r requirements.txt && ""venv311\Scripts\python.exe"" level2_service.py"

echo [2/2] Starting Java backend in new window...
start "WSI Backend (8080)" cmd /k "cd /d ""%BACKEND_DIR%"" && mvn -q clean package -DskipTests && java -jar target\wsi-backend-1.0.0.jar"

echo.
echo Started both services in separate windows:
echo - Level-2 Python: http://localhost:8001/health
echo - Java Backend  : http://localhost:8080/health
echo.
echo Chrome extension folder to load: %ROOT%legacy
echo.
echo Tip: Wait ~20-40 seconds, then test:
echo   powershell -Command "Invoke-RestMethod http://localhost:8080/health"
echo   powershell -Command "Invoke-RestMethod http://localhost:8001/health"
echo.
pause
