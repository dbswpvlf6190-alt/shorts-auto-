@echo off
setlocal

set "LOCAL=C:\shorts_auto"
set "USBSRC=%~dp0shorts_auto"

echo Importing from USB into this computer...
echo.

if not exist "%USBSRC%" (
    echo No shorts_auto folder found on this USB.
    echo Run sync_to_usb.bat on the other computer first.
    pause
    exit /b 1
)

echo [1/4] scripts
robocopy "%USBSRC%\scripts" "%LOCAL%\scripts" /MIR /XD __pycache__ /NFL /NDL /NJH /NJS

echo [2/4] docs
robocopy "%USBSRC%\docs" "%LOCAL%\docs" /MIR /NFL /NDL /NJH /NJS

echo [3/4] input\queue
robocopy "%USBSRC%\input\queue" "%LOCAL%\input\queue" /MIR /NFL /NDL /NJH /NJS

echo [4/4] CLAUDE.md
copy /Y "%USBSRC%\CLAUDE.md" "%LOCAL%\CLAUDE.md" >nul

echo.
echo Done. This computer is now up to date.
pause
