@echo off
cd /d "D:\Ozod\TDIU-TSUE\TDIU Olim fondi\TDIU-Olim-fondi-main"
echo ===== TDIU Olim Fondi Bot =====
echo.
echo [1] APScheduler va pytz o'rnatilmoqda...
pip install apscheduler pytz
echo.
echo [2] Bot ishga tushmoqda...
python app.py
pause
