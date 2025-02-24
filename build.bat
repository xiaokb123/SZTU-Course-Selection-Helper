@echo off
chcp 65001 > nul
title SZTU Course Builder
color 0A

cls
echo ================================================
echo            SZTU Course Builder v1.0
echo ================================================
echo.

:: Check Python environment
echo [1/4] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
) else (
    echo [OK] Python check passed
)

:: Check PyInstaller
echo.
echo [2/4] Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [WARN] Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] PyInstaller installation failed
        pause
        exit /b 1
    )
)
echo [OK] PyInstaller ready

:: Clean old files
echo.
echo [3/4] Cleaning old build files...
rmdir /s /q build dist 2>nul
del /f /q *.spec 2>nul
echo [OK] Cleanup completed

:: Start building
echo.
echo [4/4] Building executable...
echo Please wait, this may take a few minutes...

:: Build console version
echo Building console version...
pyinstaller --clean ^
    --add-data "requirements.txt;." ^
    --add-data "config.py;." ^
    --add-data "auto_course.py;." ^
    --add-data "README.md;." ^
    --add-data ".env.template;." ^
    --hidden-import selenium ^
    --hidden-import webdriver_manager ^
    --hidden-import python-dotenv ^
    --hidden-import loguru ^
    --hidden-import requests ^
    --hidden-import urllib3 ^
    --hidden-import certifi ^
    --hidden-import charset_normalizer ^
    --name "SZTU_Course_Helper_Console" ^
    --onefile ^
    run.py

:: Build no-console version
echo Building no-console version...
pyinstaller --clean ^
    --add-data "requirements.txt;." ^
    --add-data "config.py;." ^
    --add-data "auto_course.py;." ^
    --add-data "README.md;." ^
    --add-data ".env.template;." ^
    --hidden-import selenium ^
    --hidden-import webdriver_manager ^
    --hidden-import python-dotenv ^
    --hidden-import loguru ^
    --hidden-import requests ^
    --hidden-import urllib3 ^
    --hidden-import certifi ^
    --hidden-import charset_normalizer ^
    --name "SZTU_Course_Helper" ^
    --noconsole ^
    --onefile ^
    run.py

:: Check build result
if exist "dist\SZTU_Course_Helper.exe" (
    echo.
    echo ================================================
    echo                 Build Success!
    echo ================================================
    echo.
    echo Outputs:
    echo - dist\SZTU_Course_Helper.exe (无控制台窗口版本)
    echo - dist\SZTU_Course_Helper_Console.exe (带控制台窗口版本)
    echo.
    echo Usage:
    echo 1. Copy the exe files to a new folder
    echo 2. Create courses.json and .env files
    echo 3. Run the program (choose either version)
    echo.
) else (
    echo.
    echo [ERROR] Build failed, check the error messages
)

echo.
pause 