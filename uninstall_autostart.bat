@echo off
title DeskRobo — Remove Windows Auto-Start
cd /d "D:\DeskRobo"

echo ========================================================
echo   🤖 Removing DeskRobo from Windows Startup
echo ========================================================
echo.

python -c "from core.autostart import disable_autostart; success = disable_autostart(); print('Shortcut Removed:', success)"

echo.
echo  [OK] DeskRobo startup shortcut removed.
echo.
pause

