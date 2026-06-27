from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

# ─── Yagona UZ menyu (hammaga bir xil) ───
lang_uz_main_m = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="👤Rahbariyat"),
            KeyboardButton(text="✍️️Murojaat yuborish")
        ],
        [
            KeyboardButton(text="📂Hujjat yuborish"),
            KeyboardButton(text="📊 Statistika")
        ],
        [
            KeyboardButton(text="🏛 Olim fondi haqida"),
            KeyboardButton(text="🗂 Shaxsiy kabinet")
        ],
        [
            KeyboardButton(text="📬 2026/2027 o'quv yili uchun\nhujjat topshirish")
        ],
        [
            KeyboardButton(text="🇺🇿Tilni o'zgartish🇷🇺")
        ]
    ], resize_keyboard=True
)

# ─── Yagona RU menyu (hammaga bir xil) ───
lang_ru_main_m = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="👤Руководство"),
            KeyboardButton(text="✍️Отправить обращение")
        ],
        [
            KeyboardButton(text="📂Отправить документ"),
            KeyboardButton(text="📊 Статистика")
        ],
        [
            KeyboardButton(text="🏛 Об Олим фонде"),
            KeyboardButton(text="🗂 Личный кабинет")
        ],
        [
            KeyboardButton(text="📬 Подача документов\n2026/2027 уч. год")
        ],
        [
            KeyboardButton(text="🇷🇺Изменить язык🇺🇿")
        ]
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
