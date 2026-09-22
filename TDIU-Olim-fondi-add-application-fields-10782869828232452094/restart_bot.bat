@echo off
echo Stopping old bot process...
taskkill /f /im python.exe 2>nul
timeout /t 2 /nobreak >nul
echo Starting bot...
cd /d "D:\Ozod\TDIU-TSUE\TDIU Olim fondi\TDIU-Olim-fondi-main"
python app.py
pause
