@echo off
REM ============================================================
REM start_servers.bat
REM Starts LaserCam HTTP servers for use with MeerK40t
REM ============================================================

echo.
echo ========================================
echo  LaserCam Server Launcher
echo ========================================
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    pause
    exit /b 1
)

echo Starting LaserCam servers...
start "LaserCam Servers" python mvp\plugins\run_servers.py

timeout /t 3 /nobreak >nul

echo.
echo Verifying...
python mvp\plugins\verify_servers.py
if errorlevel 1 (
    echo.
    echo Servers failed to start. Check the LaserCam Servers window for errors.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Servers Running!
echo ========================================
echo.
echo  Laser:  http://127.0.0.1:8080
echo  Camera: http://127.0.0.1:8081
echo.
echo  Now launch MeerK40t:
echo    C:\Users\Mik_ML\AppData\Roaming\Python\Python314\Scripts\meerk40t.exe
echo.
echo  To stop servers: Close the "LaserCam Servers" window
echo ========================================
pause
