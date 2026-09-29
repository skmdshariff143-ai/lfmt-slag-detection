@echo off
title LFMT Live Thermography Lab Launcher
echo ===============================================================================
echo       LFMT LIVE THERMOGRAPHY LAB - SUB-SURFACE SLAG DETECTION IN MILD STEEL
echo ===============================================================================
echo.
echo Locating MATLAB executable...

set MATLAB_EXE=E:\MATLAB\bin\matlab.exe

if not exist "%MATLAB_EXE%" (
    where matlab.exe >nul 2>nul
    if %errorlevel% equ 0 (
        for /f "delims=" %%i in ('where matlab.exe') do set MATLAB_EXE=%%i
    ) else (
        if exist "C:\Program Files\MATLAB\R2026a\bin\matlab.exe" set MATLAB_EXE=C:\Program Files\MATLAB\R2026a\bin\matlab.exe
        if exist "C:\Program Files\MATLAB\bin\matlab.exe" set MATLAB_EXE=C:\Program Files\MATLAB\bin\matlab.exe
    )
)

echo Found MATLAB at: "%MATLAB_EXE%"
echo.
echo Starting LFMT Live Lab Interactive Application...
echo.

set PROJECT_DIR=%~dp0matlab

start "" "%MATLAB_EXE%" -nosplash -r "cd('%PROJECT_DIR%'); LFMTLiveLab;"

echo Launch command sent to MATLAB.
timeout /t 3 >nul
exit
