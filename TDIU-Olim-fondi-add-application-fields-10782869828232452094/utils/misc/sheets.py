try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

import os

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CREDENTIALS_FILE = BASE_DIR / 'credentials.json'
SPREADSHEET_ID = '1sAanq14dNre6bPFURsWcIsuSCyIeSTcZbVRgg1x3qHY'


def get_sheet():
    if not GSPREAD_AVAILABLE:
        return None
    if not os.path.exists(CREDENTIALS_FILE):
        return None
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        return sheet
    except Exception:
        return None


async def append_registration(full_name: str, username: str, phone: str, otm: str, course: str):
    if not GSPREAD_AVAILABLE:
        return
    try:
        from datetime import datetime
        import pytz
        tz = pytz.timezone("Asia/Tashkent")
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")

        sheet = get_sheet()
        if sheet is None:
            return

        if sheet.row_count == 0 or sheet.cell(1, 1).value is None:
            sheet.append_row(["Ism Familiya", "Username", "Telefon", "OTM", "Kurs", "Sana"])

        sheet.append_row([full_name, username or "-", phone, otm, course, now])
    except Exception as e:
        print(f"[SHEETS ERROR] {e}")
