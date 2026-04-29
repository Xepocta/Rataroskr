@echo off
pyinstaller --onedir --windowed --icon=icon.ico --name Ratatoskr squeaking.pyw
REM 复制外部资源文件夹
xcopy /E /I /Y Rat dist\Ratatoskr\Rat
xcopy /E /I /Y click_left dist\Ratatoskr\click_left
xcopy /E /I /Y click_right dist\Ratatoskr\click_right
xcopy /E /I /Y dialogue_box dist\Ratatoskr\dialogue_box
xcopy /E /I /Y Ato dist\Ratatoskr\Ato
xcopy /E /I /Y licenses dist\Ratatoskr\licenses
copy README.md dist\Ratatoskr\

echo 打包完成！
pause
