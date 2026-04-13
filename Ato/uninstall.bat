@echo off
reg delete "HKCU\Control Panel\Cursors\Schemes" /v "ratatoskr" /f
rd /s /q "%SystemRoot%\Cursors\ratatoskr"
RUNDLL32.EXE user32.dll,UpdatePerUserSystemParameters
pause
