from aiogram.dispatcher.filters import Text
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from loader import dp, db
from utils.misc.media import answer_photo_smart


async def about_kb(lang: str) -> InlineKeyboardMarkup:
    children = await db.get_children("about")
    kb = InlineKeyboardMarkup(row_width=1)
    for c in children:
        title = c['title_uz'] if lang == 'uz' else c['title_ru']
        kb.add(InlineKeyboardButton(
            title or c['section_key'],
            callback_data=f"about:{c['section_key']}:{lang}"
        ))
    return kb


def back_kb(lang: str, photo_msg_id: int = 0) -> InlineKeyboardMarkup:
    """photo_msg_id — yuborilgan rasm message_id si (0 = rasm yo'q)."""
    kb = InlineKeyboardMarkup()
    label = "⬅️ Ortga" if lang == 'uz' else "⬅️ Назад"
    kb.add(InlineKeyboardButton(label, callback_data=f"about_back:{lang}:{photo_msg_id}"))
    return kb


@dp.message_handler(Text(equals=["🏛 Olim fondi haqida", "🏛 Об Олим фонде"]), state='*')
async def about_fond(msg: Message):
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    header = "🏛 <b>Olim fondi haqida</b>\n\nQaysi bo'limni ko'rmoqchisiz?" if lang == 'uz' \
        else "🏛 <b>Об Олим фонде</b>\n\nКакой раздел хотите посмотреть?"
    kb = await about_kb(lang)
    await msg.answer(header, reply_markup=kb, parse_mode='HTML')


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("about:"))
async def about_section(call: CallbackQuery):
    parts = call.data.split(":")
    lang = parts[-1]
    section_key = ":".join(parts[1:-1])

    try:
        await call.answer()
    except Exception:
        pass
    await call.message.delete()

    section = await db.get_section(section_key)
    if not section:
        return

    text = section['text_uz'] if lang == 'uz' else section['text_ru']
    if not text:
        text = "Ma'lumot hali qo'shilmagan." if lang == 'uz' else "Информация ещё не добавлена."

    photo_msg = await answer_photo_smart(call.message, section['image'])
    photo_id = photo_msg.message_id if photo_msg else 0
    await call.message.answer(text, parse_mode='HTML', reply_markup=back_kb(lang, photo_id))


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("about_back:"))
async def about_back(call: CallbackQuery):
    parts = call.data.split(":")
    lang = parts[1]
    photo_id = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0

    try:
        await call.answer()
    except Exception:
        pass
    await call.message.delete()

    if photo_id:
        try:
            await call.message.bot.delete_message(call.message.chat.id, photo_id)
        except Exception:
            pass

    header = "🏛 <b>Olim fondi haqida</b>\n\nQaysi bo'limni ko'rmoqchisiz?" if lang == 'uz' \
        else "🏛 <b>Об Олим фонде</b>\n\nКакой раздел хотите посмотреть?"
    kb = await about_kb(lang)
    await call.message.answer(header, reply_markup=kb, parse_mode='HTML')
