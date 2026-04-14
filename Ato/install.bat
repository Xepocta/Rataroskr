@echo off
set "SCRIPT_DIR=%~dp0"
openfiles >nul 2>&1
if %errorlevel% NEQ 0 (
    pause
    exit /b
)

mkdir "%SystemRoot%\Cursors\Rat"
copy "%SCRIPT_DIR%anis\*.ani" "%SystemRoot%\Cursors\Rat"
reg add "HKCU\Control Panel\Cursors\Schemes" /v "Rat" /t REG_SZ /d "C:\Windows\Cursors\Rat\arrow.ani,C:\Windows\Cursors\Rat\helpsel.ani,C:\Windows\Cursors\Rat\working.ani,C:\Windows\Cursors\Rat\busy.ani,C:\Windows\Cursors\Rat\cross.ani,C:\Windows\Cursors\Rat\beam.ani,C:\Windows\Cursors\Rat\pen.ani,C:\Windows\Cursors\Rat\unavail.ani,C:\Windows\Cursors\Rat\ns.ani,C:\Windows\Cursors\Rat\ew.ani,C:\Windows\Cursors\Rat\nwse.ani,C:\Windows\Cursors\Rat\nesw.ani,C:\Windows\Cursors\Rat\move.ani,C:\Windows\Cursors\Rat\up.ani,C:\Windows\Cursors\Rat\link.ani,C:\Windows\Cursors\Rat\pin.ani,C:\Windows\Cursors\Rat\person.ani" /f
RUNDLL32.EXE user32.dll,UpdatePerUserSystemParameters
pause
