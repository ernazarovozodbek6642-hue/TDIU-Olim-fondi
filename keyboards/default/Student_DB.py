from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


async def build_main_kb_uz(db, registered: bool = False) -> ReplyKeyboardMarkup:
    """
    Asosiy UZ menyu — svc:* bo'limlari aktiv/nofaol holatiga qarab quriladi.
    """
    show_hujjat   = await db.is_service_active('svc:hujjat')
    show_ariza    = await db.is_service_active('svc:ariza')
    show_murojaat = await db.is_service_active('svc:murojaat')

    rows = []
    # 1-qator: Rahbariyat + Murojaat (murojaat aktiv bo'lsa)
    row1 = [KeyboardButton(text="👤Rahbariyat")]
    if show_murojaat:
        row1.append(KeyboardButton(text="✍️️Murojaat yuborish"))
    rows.append(row1)

    # 2-qator: Hujjat yuborish + Statistika (hujjat aktiv bo'lsa)
    row2 = []
    if show_hujjat:
        row2.append(KeyboardButton(text="📂Hujjat yuborish"))
    row2.append(KeyboardButton(text="📊 Statistika"))
    rows.append(row2)

    # 3-qator: Haqida + Kabinet
    rows.append([
        KeyboardButton(text="🏛 Olim fondi haqida"),
        KeyboardButton(text="🗂 Shaxsiy kabinet")
    ])

    # 4-qator: Ariza (aktiv bo'lsa)
    if show_ariza:
        rows.append([KeyboardButton(text="📬 2026/2027 o'quv yili uchun\nhujjat topshirish")])

    # 5-qator: Til o'zgartirish
    rows.append([KeyboardButton(text="🇺🇿Tilni o'zgartish🇷🇺")])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


async def build_main_kb_ru(db, registered: bool = False) -> ReplyKeyboardMarkup:
    """
    Asosiy RU menyu — svc:* bo'limlari aktiv/nofaol holatiga qarab quriladi.
    """
    show_hujjat   = await db.is_service_active('svc:hujjat')
    show_ariza    = await db.is_service_active('svc:ariza')
    show_murojaat = await db.is_service_active('svc:murojaat')

    rows = []
    row1 = [KeyboardButton(text="👤Руководство")]
    if show_murojaat:
        row1.append(KeyboardButton(text="✍️Отправить обращение"))
    rows.append(row1)

    row2 = []
    if show_hujjat:
        row2.append(KeyboardButton(text="📂Отправить документ"))
    row2.append(KeyboardButton(text="📊 Статистика"))
    rows.append(row2)

    rows.append([
        KeyboardButton(text="🏛 Об Олим фонде"),
        KeyboardButton(text="🗂 Личный кабинет")
    ])

    if show_ariza:
        rows.append([KeyboardButton(text="📬 Подача документов\n2026/2027 уч. год")])

    rows.append([KeyboardButton(text="🇷🇺Изменить язык🇺🇿")])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


# ─── Statik fallback (db mavjud bo'lmagan holat uchun) ───
lang_uz_main_m = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤Rahbariyat"), KeyboardButton(text="✍️️Murojaat yuborish")],
        [KeyboardButton(text="📂Hujjat yuborish"), KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="🏛 Olim fondi haqida"), KeyboardButton(text="🗂 Shaxsiy kabinet")],
        [KeyboardButton(text="📬 2026/2027 o'quv yili uchun\nhujjat topshirish")],
        [KeyboardButton(text="🇺🇿Tilni o'zgartish🇷🇺")],
    ], resize_keyboard=True
)

lang_ru_main_m = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤Руководство"), KeyboardButton(text="✍️Отправить обращение")],
        [KeyboardButton(text="📂Отправить документ"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="🏛 Об Олим фонде"), KeyboardButton(text="🗂 Личный кабинет")],
        [KeyboardButton(text="📬 Подача документов\n2026/2027 уч. год")],
        [KeyboardButton(text="🇷🇺Изменить язык🇺🇿")],
    ], resize_keyboard=True
)

# Alias — backward compatibility uchun
unreg_uz_menu = lang_uz_main_m
unreg_ru_menu = lang_ru_main_m

# ─── Rahbariyat submenyusi ───
uz_management_list = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="💼 Fond rahbari"),
            KeyboardButton(text="👔 Kuzatuv kengashi"),
        ],
        [
            KeyboardButton(text="🤝 Kuratorlar"),
            KeyboardButton(text="🧠 Ekspertlar")
        ],
        [
            KeyboardButton(text="🙌 Volontyorlar")
        ],
        [
            KeyboardButton(text="⬅️Ortga"),
            KeyboardButton(text="🏠 Bosh menyu")
        ]
    ], resize_keyboard=True
)

ru_management_list = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="💼 Руководитель фонда"),
            KeyboardButton(text="👔 Наблюдательный совет"),
        ],
        [
            KeyboardButton(text="🤝 Кураторы"),
            KeyboardButton(text="🧠 Эксперты")
        ],
        [
            KeyboardButton(text="🙌 Волонтёры")
        ],
        [
            KeyboardButton(text="⬅️Назад"),
            KeyboardButton(text="🏠 Главное меню")
        ]
    ], resize_keyboard=True
)

# ─── Faqat Bosh menyu tugmasi ───
bosh_menu_uz = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🏠 Bosh menyu")]],
    resize_keyboard=True
)

bosh_menu_ru = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🏠 Главное меню")]],
    resize_keyboard=True
)

# ─── Ortga + Bosh menyu ───
back_uz = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="⬅️Ortga"),
            KeyboardButton(text="🏠 Bosh menyu")
        ]
    ], resize_keyboard=True
)

back_ru = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="⬅️Назад"),
            KeyboardButton(text="🏠 Главное меню")
        ]
    ], resize_keyboard=True
)

# ─── Bosh menyu tugmasi (qaytish uchun) ───
main_menu_uz = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🏠 Bosh menyu")]],
    resize_keyboard=True
)

main_menu_ru = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🏠 Главное меню")]],
    resize_keyboard=True
)
