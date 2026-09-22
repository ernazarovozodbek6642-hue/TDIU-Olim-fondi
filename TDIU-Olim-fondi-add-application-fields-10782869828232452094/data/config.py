import os
import sys
from environs import Env

# environs kutubxonasidan foydalanish
env = Env()
env.read_env()

# .env fayl ichidan quyidagilarni o'qiymiz
BOT_TOKEN = "8280117262:AAE6TR1cRngZqLf2mX1T_Kk9ZSi9EXbJmSk"  # Bot token
ADMINS = ['1428562070', '-1002605246735', '5589013665']  # adminlar ro'yxati
STORAGE_CHANNEL = '-1003658983979'  # Hujjatlar arxiv kanali
IP = 'localhost'  # Xosting ip manzili


DB_HOST = 'ep-soft-shadow-adiix24b-pooler.c-2.us-east-1.aws.neon.tech'
DB_NAME = 'neondb'
DB_USER = 'neondb_owner'
DB_PASS = 'npg_MjOB5CokvDF8'


# Startup validation checks for environment and dependencies
missing_vars = []
if not BOT_TOKEN:
    missing_vars.append("BOT_TOKEN")
if not DB_HOST:
    missing_vars.append("DB_HOST")
if not DB_NAME:
    missing_vars.append("DB_NAME")
if not DB_USER:
    missing_vars.append("DB_USER")
if not DB_PASS:
    missing_vars.append("DB_PASS")

if missing_vars:
    print(f"❌ CRITICAL ERROR: Key environment variables are missing: {', '.join(missing_vars)}", file=sys.stderr)
    sys.exit(1)

# Validate credentials.json path
credentials_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'credentials.json')
if not os.path.exists(credentials_path):
    print(f"⚠️ WARNING: Google API credentials file '{credentials_path}' is missing! Google Sheets synchronization may be limited.", file=sys.stderr)
