@echo off
REM ============================================================
REM launch_lasercam.bat
REM Starts LaserCam HTTP servers and optionally MeerK40t
REM ============================================================

echo.
echo ========================================
echo  LaserCam Launcher
echo ========================================
echo.

cd /d "%~dp0"

REM --- Check Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    pause
    exit /b 1
)

REM --- Check dependencies ---
python -c "import cv2; import numpy" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install opencv-python numpy pyserial
)

echo Starting Laser Emulator HTTP server on port 8080...
start "Laser Emulator" python -m mvp.plugins.laser_emulator --port 8080

timeout /t 2 /nobreak >nul

echo Starting Camera Emulator HTTP server on port 8081...
start "Camera Emulator" python -m mvp.plugins.camera_emulator --port 8081

timeout /t 2 /nobreak >nul

echo.
echo Verifying servers...
python mvp\plugins\verify_servers.py
if errorlevel 1 (
    echo.
    echo Servers failed to start. Check console windows for errors.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  LaserCam Servers Running!
echo ========================================
echo.
echo  Laser Emulator:  http://127.0.0.1:8080
echo  Camera Emulator: http://127.0.0.1:8081
echo.
echo  To launch MeerK40t alongside:
echo    C:\Users\Mik_ML\AppData\Roaming\Python\Python314\Scripts\meerk40t.exe
echo    (or add that Scripts folder to your PATH)
echo.
echo  To stop servers: Close the console windows
echo ========================================
echo.

REM --- Ask if user wants to launch MeerK40t ---
set /p LAUNCH_MK="Launch MeerK40t now? (y/n): "
if /i "%LAUNCH_MK%"=="y" (
    echo Launching MeerK40t...
    start "" "C:\Users\Mik_ML\AppData\Roaming\Python\Python314\Scripts\meerk40t.exe"
)

echo.
echo Press any key to exit (servers will keep running)...
pause >nul
