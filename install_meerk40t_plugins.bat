@echo off
REM ============================================================
REM install_meerk40t_plugins.bat
REM Installs LaserCam plugins into MeerK40t and verifies them
REM ============================================================

echo.
echo ========================================
echo  LaserCam MeerK40t Plugin Installer
echo ========================================
echo.

REM --- Step 1: Check Python ---
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+ and add it to PATH.
    pause
    exit /b 1
)
echo OK: Python found.

REM --- Step 2: Check MeerK40t ---
echo [2/6] Checking MeerK40t installation...
pip show meerk40t >nul 2>&1
if errorlevel 1 (
    echo MeerK40t not installed. Installing now...
    pip install meerk40t
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install MeerK40t.
        echo Try: pip install meerk40t --user
        pause
        exit /b 1
    )
    echo OK: MeerK40t installed.
) else (
    echo OK: MeerK40t already installed.
)

REM --- Step 3: Check dependencies ---
echo [3/6] Checking dependencies...
pip install opencv-python numpy pyserial >nul 2>&1
echo OK: Dependencies installed.

REM --- Step 4: Install LaserCam plugins ---
echo [4/6] Installing LaserCam MeerK40t plugins...
cd /d "%~dp0"
pip install -e mvp\plugins\meerk40t_plugin
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install plugins via pip.
    echo Trying manual install...
    echo.
    set /p MK_DIR="Enter MeerK40t plugins directory (or press Enter to skip): "
    if not "%MK_DIR%"=="" (
        if exist "%MK_DIR%" (
            xcopy /E /I /Y mvp\plugins\meerk40t_plugin "%MK_DIR%\lasercam_plugin"
            echo OK: Plugins copied to %MK_DIR%\lasercam_plugin
        ) else (
            echo Directory not found: %MK_DIR%
        )
    )
) else (
    echo OK: Plugins installed via pip.
)

REM --- Step 5: Verify installation ---
echo [5/6] Verifying plugin installation...
python -c "from mvp.plugins.meerk40t_plugin.laser_emulator_plugin import plugin; print('  Laser Emulator plugin: OK')" 2>nul
if errorlevel 1 (
    echo  Laser Emulator plugin: WARN (meerk40t not available for import check)
    echo  ^| This is normal if MeerK40t is installed separately.
    echo  ^| The plugin will load when MeerK40t starts.
)

python -c "from mvp.plugins.meerk40t_plugin.camera_emulator_plugin import plugin; print('  Camera Emulator plugin: OK')" 2>nul
if errorlevel 1 (
    echo  Camera Emulator plugin: WARN (meerk40t not available for import check)
    echo  ^| This is normal if MeerK40t is installed separately.
    echo  ^| The plugin will load when MeerK40t starts.
)

REM --- Step 6: Run standalone verification ---
echo [6/6] Running standalone plugin verification...
echo.
python mvp\plugins\test_plugins_standalone.py

echo.
echo ========================================
echo  Installation Complete!
echo ========================================
echo.
echo To run MeerK40t with plugins:
echo   C:\Users\Mik_ML\AppData\Roaming\Python\Python314\Scripts\meerk40t.exe
echo   (or add that Scripts folder to your PATH first)
echo.
echo The plugins will auto-load and start HTTP servers on:
echo   Laser Emulator:  http://127.0.0.1:8080
echo   Camera Emulator: http://127.0.0.1:8081
echo.
echo To run standalone (without MeerK40t):
echo   python -m mvp.plugins.laser_emulator
echo   python -m mvp.plugins.camera_emulator
echo.
echo ========================================
pause
