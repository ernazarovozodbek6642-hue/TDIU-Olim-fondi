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
