import gspread
from google.oauth2.service_account import Credentials
import os

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'credentials.json')
SPREADSHEET_ID = '1sAanq14dNre6bPFURsWcIsuSCyIeSTcZbVRgg1x3qHY'


def get_sheet():
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    return sheet


async def append_registration(full_name: str, username: str, phone: str, otm: str, course: str):
    try:
        from datetime import datetime
        import pytz
        tz = pytz.timezone("Asia/Tashkent")
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")

        sheet = get_sheet()

        # Agar jadval bo'sh bo'lsa sarlavha qo'shamiz
        if sheet.row_count == 0 or sheet.cell(1, 1).value is None:
            sheet.append_row(["Ism Familiya", "Username", "Telefon", "OTM", "Kurs", "Sana"])

        sheet.append_row([full_name, username or "-", phone, otm, course, now])
    except Exception as e:
        print(f"[SHEETS ERROR] {e}")
