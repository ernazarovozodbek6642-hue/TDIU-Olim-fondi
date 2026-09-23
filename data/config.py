import os
import sys
import json
from environs import Env

# environs kutubxonasidan foydalanish
env = Env()
env.read_env()

# .env fayl ichidan quyidagilarni o'qiymiz
BOT_TOKEN = env.str("BOT_TOKEN", default="")


def _parse_admins(raw_value: str):
    """ADMINS uchun JSON array va oddiy vergulli formatni qo'llab-quvvatlaydi."""
    raw_value = (raw_value or "").strip()
    if not raw_value:
        return []
    try:
        parsed = json.loads(raw_value)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except (json.JSONDecodeError, TypeError):
        pass
    return [
        item.strip().strip("[]\"'")
        for item in raw_value.split(",")
        if item.strip().strip("[]\"'")
    ]


ADMINS = _parse_admins(os.getenv("ADMINS", ""))
STORAGE_CHANNEL = env.str("STORAGE_CHANNEL", default="")
IP = env.str("IP", default="localhost")

DB_HOST = env.str("DB_HOST", default="")
DB_NAME = env.str("DB_NAME", default="")
DB_USER = env.str("DB_USER", default="")
# Hostinglarda ikkala nomdan biri ishlatilishi mumkin.
DB_PASS = env.str("DB_PASS", default=env.str("DB_PASSWORD", default=""))


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
