from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

lang = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="O'zbekcha🇺🇿", callback_data="lang:uz"),
            InlineKeyboardButton(text="По-русски🇷🇺", callback_data="lang:ru")
        ]
    ]
)

confirmation_uz = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data='conf')
        ],
        [
            InlineKeyboardButton(text="✏️ Tahrirlash", callback_data='again'),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data='cancel')
        ]
    ]
)

confirmation_ru = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data='conf')
        ],
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data='again'),
            InlineKeyboardButton(text="❌ Отмена", callback_data='cancel')
        ]
    ]
)
