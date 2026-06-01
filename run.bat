@echo off
chcp 65001 >nul
title Video Cutter / Trimmer
cd /d "%~dp0"

echo ========================================
echo    Video Cutter / Trimmer
echo ========================================
echo.

:: ============================================
:: Auto-detect Python
:: ============================================
set PYTHON_CMD=

:: 1) Check if python is already in PATH
where python >nul 2>&1 && (
    for /f "delims=" %%i in ('where python 2^>nul') do set PYTHON_CMD=%%i
    goto :python_found
)

:: 2) Check py launcher
where py >nul 2>&1 && set PYTHON_CMD=py && goto :python_found

:: 3) User's local installs (AppData)
for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%d\python.exe" (
        set PYTHON_CMD=%%d\python.exe
        goto :python_found
    )
)

:: 4) System-wide installs (Program Files)
for /d %%d in ("C:\Program Files\Python3*") do (
    if exist "%%d\python.exe" (
        set PYTHON_CMD=%%d\python.exe
        goto :python_found
    )
)

:: 5) Root C:\Python
for /d %%d in ("C:\Python3*") do (
    if exist "%%d\python.exe" (
        set PYTHON_CMD=%%d\python.exe
        goto :python_found
    )
)

:: 6) scoop / chocolatey
if exist "%USERPROFILE%\scoop\apps\python\current\python.exe" (
    set PYTHON_CMD=%USERPROFILE%\scoop\apps\python\current\python.exe
    goto :python_found
)

:: Not found
echo [Error] Python not found on your computer.
echo.
echo Please install Python 3.x:
echo   1. Download from https://www.python.org/downloads/
echo   2. Run the installer
echo   3. CHECK "Add Python to PATH"
echo.
pause
exit /b 1

:python_found
echo Python: %PYTHON_CMD%
echo Starting...
echo.

%PYTHON_CMD% video_cutter.py

if errorlevel 1 (
    echo.
    echo Failed to start. Check:
    echo   1. Python is working:  %PYTHON_CMD% --version
    echo   2. FFmpeg: place ffmpeg.exe in this folder or install system-wide
    echo.
    pause
)
