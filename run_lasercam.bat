@echo off
REM ============================================================
REM run_lasercam.bat — Quick launch LaserCam MVP
REM ============================================================
echo.
echo ========================================
echo  LaserCam MVP — Simulator Mode
echo ========================================
echo.
echo  Starting LaserCam with simulated camera
echo  and controller (no hardware needed).
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
python -c "import cv2; import numpy; import PIL" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Starting LaserCam...
echo.
echo  Controls:
echo    - Arrow buttons to jog camera
echo    - Step size buttons to change movement precision
echo    - "Go To" to jump to absolute coordinates
echo    - Start button to begin the alignment process
echo.
echo  Workflow:
echo    1. Press Start
echo    2. Jog camera to first marker (M1)
echo    3. When detected, confirm position
echo    4. App navigates to second marker (M2)
echo    5. Confirm M2 position
echo    6. Done — both markers registered
echo.
echo ========================================
echo.

python -m mvp.app

echo.
echo LaserCam closed.
pause
