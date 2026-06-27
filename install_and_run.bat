@echo off
cd /d "D:\Ozod\TDIU-TSUE\TDIU Olim fondi\TDIU-Olim-fondi-main"
echo Installing packages...
pip install aiogram==2.25.2 aiohttp==3.8.6 aiosignal==1.4.0 asyncpg==0.30.0 environs python-dotenv pytz
echo.
echo Starting bot...
python app.py
pause
