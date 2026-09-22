@echo off
cd /d "D:\Ozod\TDIU-TSUE\TDIU Olim fondi\TDIU-Olim-fondi-main"
echo [%date% %time%] Packagelar o'rnatilmoqda... >> run_log.txt 2>&1
pip install -r requirements.txt >> run_log.txt 2>&1
echo [%date% %time%] Bot ishga tushmoqda... >> run_log.txt 2>&1
python app.py >> run_log.txt 2>&1
echo [%date% %time%] Bot to'xtadi. >> run_log.txt 2>&1
