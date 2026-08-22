@echo off
setlocal

set "LOCAL=C:\shorts_auto"
set "USBDEST=%~dp0shorts_auto"

echo Exporting from this computer to USB...
echo.

if not exist "%USBDEST%" mkdir "%USBDEST%"

echo [1/4] scripts
robocopy "%LOCAL%\scripts" "%USBDEST%\scripts" /MIR /XD __pycache__ /NFL /NDL /NJH /NJS

echo [2/4] docs
robocopy "%LOCAL%\docs" "%USBDEST%\docs" /MIR /NFL /NDL /NJH /NJS

echo [3/4] input\queue
robocopy "%LOCAL%\input\queue" "%USBDEST%\input\queue" /MIR /NFL /NDL /NJH /NJS

echo [4/4] CLAUDE.md
copy /Y "%LOCAL%\CLAUDE.md" "%USBDEST%\CLAUDE.md" >nul

echo.
echo Done. Plug this USB into the other computer and run sync_from_usb.bat
pause
