@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ========================================
echo  MA Agent - Windows Build Script
echo ========================================

:: Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+ from python.org first.
    pause
    exit /b 1
)

:: Install dependencies
echo [1/4] Installing Python dependencies...
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: Install optional browser engines for camoufox (graceful fallback if skipped)
echo [2/4] Installing browser engines (optional, ~100MB)...
python -m playwright install chromium firefox 2>nul || echo [WARN] Playwright browsers not installed. Camoufox fallback will be skipped.

:: Build executable
echo [3/4] Building Windows executable with PyInstaller...
python -m PyInstaller ma-web.spec --clean --noconfirm
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)

:: Package into zip for easy distribution
echo [4/4] Packaging into dist\ma-agent-windows.zip...
powershell -Command "Compress-Archive -Path 'dist\ma-agent\*' -DestinationPath 'dist\ma-agent-windows.zip' -Force"

echo ========================================
echo  Build complete!
echo  Executable: dist\ma-agent\ma-agent.exe
echo  Zip package: dist\ma-agent-windows.zip
echo ========================================
pause
