@echo off
title DeskRobo — Install Windows Auto-Start
cd /d "D:\DeskRobo"

echo ========================================================
echo   🤖 Installing DeskRobo Silent Background Auto-Start
echo ========================================================
echo.

python -c "from core.autostart import enable_autostart; success = enable_autostart(); print('Shortcut Created:', success)"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo  [OK] DeskRobo is now configured to start automatically on Windows boot!
    echo  [OK] Starting DeskRobo silently in the background right now...
    cscript //nologo launch_silent.vbs
    echo.
    echo  ========================================================
    echo   All set! Press Alt + Q or Alt + N anytime to summon!
    echo   DeskRobo lives silently in your taskbar system tray.
    echo  ========================================================
) else (
    echo.
    echo  [ERROR] Failed to configure Windows startup shortcut.
)

echo.
pause

