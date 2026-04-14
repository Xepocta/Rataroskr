@echo off
reg delete "HKCU\Control Panel\Cursors\Schemes" /v "Rat" /f
rd /s /q "%SystemRoot%\Cursors\Rat"
RUNDLL32.EXE user32.dll,UpdatePerUserSystemParameters
pause
