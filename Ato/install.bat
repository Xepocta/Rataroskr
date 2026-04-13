@echo off
set "SCRIPT_DIR=%~dp0"
openfiles >nul 2>&1
if %errorlevel% NEQ 0 (
    pause
    exit /b
)

mkdir "%SystemRoot%\Cursors\ratatoskr"
copy "%SCRIPT_DIR%Ani\*.ani" "%SystemRoot%\Cursors\ratatoskr"
reg add "HKCU\Control Panel\Cursors\Schemes" /v "ratatoskr" /t REG_SZ /d "C:\Windows\Cursors\ratatoskr\arrow.ani,C:\Windows\Cursors\ratatoskr\helpsel.ani,C:\Windows\Cursors\ratatoskr\working.ani,C:\Windows\Cursors\ratatoskr\busy.ani,C:\Windows\Cursors\ratatoskr\cross.ani,C:\Windows\Cursors\ratatoskr\beam.ani,C:\Windows\Cursors\ratatoskr\pen.ani,C:\Windows\Cursors\ratatoskr\unavail.ani,C:\Windows\Cursors\ratatoskr\ns.ani,C:\Windows\Cursors\ratatoskr\ew.ani,C:\Windows\Cursors\ratatoskr\nwse.ani,C:\Windows\Cursors\ratatoskr\nesw.ani,C:\Windows\Cursors\ratatoskr\move.ani,C:\Windows\Cursors\ratatoskr\up.ani,C:\Windows\Cursors\ratatoskr\link.ani,C:\Windows\Cursors\ratatoskr\pin.ani,C:\Windows\Cursors\ratatoskr\person.ani" /f
RUNDLL32.EXE user32.dll,UpdatePerUserSystemParameters
pause
