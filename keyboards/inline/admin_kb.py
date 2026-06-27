from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
import pytz


def admin_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("📊 Statistika", callback_data="adm:stats"),
            InlineKeyboardButton("📩 Murojaatlar", callback_data="adm:appeals")
        ],
        [
            InlineKeyboardButton("📂 Hujjatlar", callback_data="adm:docs"),
            InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="adm:users")
        ],
        [
            InlineKeyboardButton("📢 Broadcast", callback_data="adm:broadcast"),
            InlineKeyboardButton("📅 Tadbirlar", callback_data="adm:events")
        ],
        [
            InlineKeyboardButton("📋 Arizalar", callback_data="adm:arizalar")
        ],
        [
            InlineKeyboardButton("📝 Bo'limlarni boshqarish", callback_data="cms:main")
        ]
    ])


def back_to_admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("⬅️ Ortga", callback_data="adm:main")]
    ])


# ─── TADBIRLAR ───
def event_date_kb():
    tz = pytz.timezone("Asia/Tashkent")
    today = datetime.now(tz).date()
    buttons = []
    row = []
    for i in range(7):
        day = today + timedelta(days=i)
        label = f"{'Bugun' if i == 0 else 'Ertaga' if i == 1 else ''} {day.strftime('%d.%m')}".strip()
        row.append(InlineKeyboardButton(label, callback_data=f"edate:{day.strftime('%d.%m.%Y')}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("❌ Bekor qilish", callback_data="adm:events")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def event_time_kb():
    times = []
    h, m = 8, 0
    while h < 20 or (h == 20 and m == 0):
        times.append(f"{h:02d}:{m:02d}")
        m += 30
        if m >= 60:
            m = 0
            h += 1
    buttons = []
    row = []
    for t in times:
        row.append(InlineKeyboardButton(t, callback_data=f"etime:{t}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("❌ Bekor qilish", callback_data="adm:events")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def event_confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data="event:confirm")],
        [
            InlineKeyboardButton("✏️ Tahrirlash", callback_data="event:edit"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data="adm:events")
        ]
    ])


def events_list_kb(events):
    buttons = []
    for ev in events:
        buttons.append([InlineKeyboardButton(
            f"📅 {ev['name']} — {ev['event_date']}",
            callback_data=f"ev:{ev['id']}"
        )])
    buttons.append([InlineKeyboardButton("➕ Yangi tadbir", callback_data="event:new")])
    buttons.append([InlineKeyboardButton("⬅️ Ortga", callback_data="adm:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def event_detail_kb(event_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"ev_edit:{event_id}"),
            InlineKeyboardButton("🗑 O'chirish", callback_data=f"ev_del:{event_id}")
        ],
        [InlineKeyboardButton("⬅️ Ortga", callback_data="adm:events")]
    ])


# ─── MUROJAATLAR ───
def appeals_list_kb(appeals):
    buttons = []
    for ap in appeals:
        subject = ap.get('subject') or 'Mavzusiz'
        buttons.append([InlineKeyboardButton(
            f"📩 {subject[:40]}",
            callback_data=f"ap:{ap['id']}"
        )])
    buttons.append([InlineKeyboardButton("⬅️ Ortga", callback_data="adm:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def appeal_detail_kb(appeal_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✉️ Javob berish", callback_data=f"ap_reply:{appeal_id}")],
        [InlineKeyboardButton("⬅️ Ortga", callback_data="adm:appeals")]
    ])


# ─── HUJJATLAR ───
def docs_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📋 Barcha hujjatlar", callback_data="docs:all")],
        [InlineKeyboardButton("🔍 Qidirish", callback_data="docs:search")],
        [InlineKeyboardButton("⬅️ Ortga", callback_data="adm:main")]
    ])


def doc_users_kb(users_list, mode="zip"):
    buttons = []
    for u in users_list:
        name = u.get('real_name') or u.get('full_name') or 'Noma\'lum'
        buttons.append([InlineKeyboardButton(
            f"👤 {name}",
            callback_data=f"docuser:{mode}:{u['id']}"
        )])
    buttons.append([InlineKeyboardButton("⬅️ Ortga", callback_data="adm:docs")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def doc_list_kb(docs, user_id):
    buttons = []
    for doc in docs:
        theme = doc.get('theme') or 'Mavzusiz'
        buttons.append([InlineKeyboardButton(
            f"📄 {theme[:40]}",
            callback_data=f"docview:{doc['id']}"
        )])
    buttons.append([InlineKeyboardButton("⬅️ Ortga", callback_data="docs:search")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ─── FOYDALANUVCHILAR ───
def users_list_kb(users, page=0, per_page=10):
    buttons = []
    start = page * per_page
    chunk = users[start:start + per_page]
    for u in chunk:
        name = u.get('real_name') or u.get('full_name') or 'Noma\'lum'
        buttons.append([InlineKeyboardButton(
            f"{'✅' if u.get('registered') else '⏳'} {name}",
            callback_data=f"chatuser:{u['id']}"
        )])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"usrpage:{page-1}"))
    total_pages = (len(users) + per_page - 1) // per_page
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if start + per_page < len(users):
        nav.append(InlineKeyboardButton("➡️", callback_data=f"usrpage:{page+1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("⬅️ Ortga", callback_data="adm:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def chat_end_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🔴 Chatni yakunlash", callback_data="chat:end")]
    ])


# ─── ARIZALAR ───
def arizalar_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("⏳ Kutilayotganlar", callback_data="ariza_list:pending")],
        [InlineKeyboardButton("✅ Tasdiqlangan", callback_data="ariza_list:approved")],
        [InlineKeyboardButton("❌ Rad etilgan", callback_data="ariza_list:rejected")],
        [InlineKeyboardButton("🔍 Qidirish", callback_data="ariza_search")],
        [InlineKeyboardButton("⬅️ Ortga", callback_data="adm:main")]
    ])


def arizalar_list_kb(arizalar, status, page=0, per_page=8):
    buttons = []
    start = page * per_page
    chunk = arizalar[start:start + per_page]
    for a in chunk:
        icon = "⏳" if a['status'] == 'pending' else "✅" if a['status'] == 'approved' else "❌"
        buttons.append([InlineKeyboardButton(
            f"{icon} {a['fish'][:35]}",
            callback_data=f"ariza:{a['id']}"
        )])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"ariza_page:{status}:{page-1}"))
    total = (len(arizalar) + per_page - 1) // per_page
    nav.append(InlineKeyboardButton(f"{page+1}/{total}", callback_data="noop"))
    if start + per_page < len(arizalar):
        nav.append(InlineKeyboardButton("➡️", callback_data=f"ariza_page:{status}:{page+1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("⬅️ Ortga", callback_data="adm:arizalar")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def ariza_detail_kb(ariza_id, status):
    buttons = []
    if status == 'pending':
        buttons.append([
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"ariza_ok:{ariza_id}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"ariza_rad:{ariza_id}")
        ])
    buttons.append([InlineKeyboardButton("⬅️ Ortga", callback_data="adm:arizalar")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ─── BROADCAST ───
def broadcast_confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Yuborish", callback_data="bc:send")],
        [
            InlineKeyboardButton("✏️ Tahrirlash", callback_data="bc:edit"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data="adm:main")
        ]
    ])
