from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from loader import dp, db
from utils.misc.media import answer_photo_smart


def mgmt_header(lang: str) -> str:
    return "👤 <b>Rahbariyat</b>\n\nQaysi bo'limni ko'rmoqchisiz?" if lang == 'uz' \
        else "👤 <b>Руководство</b>\n\nКакой раздел хотите посмотреть?"


async def mgmt_kb(lang: str) -> InlineKeyboardMarkup:
    children = await db.get_children("mgmt")
    kb = InlineKeyboardMarkup(row_width=1)
    for c in children:
        title = c['title_uz'] if lang == 'uz' else c['title_ru']
        kb.add(InlineKeyboardButton(
            title or c['section_key'],
            callback_data=f"mgmt_sec:{c['section_key']}:{lang}"
        ))
    return kb


async def send_person(msg_obj: Message, person_key: str, lang: str,
                      back_section_key: str = None):
    """
    back_section_key — "Ortga" qayerga qaytishini bildiradi.
    None bo'lsa shaxs parent_key i ishlatiladi.

    Callback format: mgmt_pb|{section_key}|{lang}|{photo_id}
    ('|' separator — section_key va lang hech qachon | ishlatmaydi)
    """
    section = await db.get_section(person_key)
    if not section:
        return

    text = section['text_uz'] if lang == 'uz' else section['text_ru']
    target_key = back_section_key or section['parent_key'] or "mgmt"

    photo_msg = await answer_photo_smart(msg_obj, section['image'])
    photo_id = photo_msg.message_id if photo_msg else 0

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(
        "⬅️ Ortga" if lang == 'uz' else "⬅️ Назад",
        callback_data=f"mgmt_pb|{target_key}|{lang}|{photo_id}"
    ))
    await msg_obj.answer(text or '—', parse_mode='HTML', reply_markup=kb)


async def show_section(msg_obj: Message, section_key: str, lang: str):
    """
    Bo'limni ko'rsatish:
    - 0 bola → "Ma'lumot yo'q" + Ortga tugmasi
    - 1 bola → shaxsni ko'rsat, "Ortga" → grandparent (loop oldini olish)
    - 2+ bola → ro'yxat ko'rsat
    """
    children = await db.get_children(section_key)

    if len(children) == 0:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(
            "⬅️ Ortga" if lang == 'uz' else "⬅️ Назад",
            callback_data=f"mgmt_back:{lang}"
        ))
        await msg_obj.answer(
            "Ma'lumot yo'q." if lang == 'uz' else "Нет данных.",
            reply_markup=kb
        )

    elif len(children) == 1:
        # Bitta shaxs — "Ortga" section ning parent iga qaytsin (loop oldini olish)
        section = await db.get_section(section_key)
        grandparent = section['parent_key'] if section else "mgmt"
        back_target = grandparent or "mgmt"
        await send_person(msg_obj, children[0]['section_key'], lang,
                          back_section_key=back_target)

    else:
        section = await db.get_section(section_key)
        kb = InlineKeyboardMarkup(row_width=1)
        for c in children:
            title = c['title_uz'] if lang == 'uz' else c['title_ru']
            kb.add(InlineKeyboardButton(
                title or c['section_key'],
                callback_data=f"mgmt_p:{c['section_key']}:{lang}"
            ))
        kb.add(InlineKeyboardButton(
            "⬅️ Ortga" if lang == 'uz' else "⬅️ Назад",
            callback_data=f"mgmt_back:{lang}"
        ))
        title = (section['title_uz'] if lang == 'uz' else section['title_ru']) if section else ''
        prompt = "Qaysi shaxs haqida bilmoqchisiz?" if lang == 'uz' else "О ком хотите узнать?"
        await msg_obj.answer(f"<b>{title}</b>\n\n{prompt}", reply_markup=kb, parse_mode='HTML')


# ════════════════════════════════════════
#  HANDLER — "Rahbariyat" tugmasi
# ════════════════════════════════════════

@dp.message_handler(text=['Rahbariyat', "Руководство",
                           '👤 Rahbariyat', '👤 Руководство',
                           '👤Rahbariyat', '👤Руководство'])
async def management_info(msg: Message):
    user = await db.select_user(str(msg.from_user.id))
    lang = user['language'] if user else 'uz'
    kb = await mgmt_kb(lang)
    await msg.answer(mgmt_header(lang), reply_markup=kb, parse_mode='HTML')


# ════════════════════════════════════════
#  HANDLERLAR — inline callback
# ════════════════════════════════════════

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("mgmt_sec:"))
async def mgmt_section(call: CallbackQuery):
    """mgmt_sec:{section_key}:{lang}"""
    parts = call.data.split(":")
    lang = parts[-1]
    section_key = ":".join(parts[1:-1])
    try:
        await call.answer()
    except Exception:
        pass
    await call.message.delete()
    await show_section(call.message, section_key, lang)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("mgmt_p:"))
async def mgmt_person_cb(call: CallbackQuery):
    """mgmt_p:{person_key}:{lang} — ro'yxatdan shaxs tanlash"""
    parts = call.data.split(":")
    lang = parts[-1]
    person_key = ":".join(parts[1:-1])
    try:
        await call.answer()
    except Exception:
        pass
    await call.message.delete()
    section = await db.get_section(person_key)
    parent_key = section['parent_key'] if section else None
    await send_person(call.message, person_key, lang, back_section_key=parent_key)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("mgmt_pb|"))
async def mgmt_person_back(call: CallbackQuery):
    """
    mgmt_pb|{section_key}|{lang}|{photo_id}
    Shaxs sahifasidan ortga: rasm + matnni o'chiradi.
    """
    parts = call.data.split("|")
    # parts = ["mgmt_pb", section_key, lang, photo_id]
    if len(parts) != 4:
        try:
            await call.answer()
        except Exception:
            pass
        return

    _, section_key, lang, photo_id_str = parts
    photo_id = int(photo_id_str) if photo_id_str.isdigit() else 0

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

    if not section_key or section_key == "mgmt":
        kb = await mgmt_kb(lang)
        await call.message.answer(mgmt_header(lang), reply_markup=kb, parse_mode='HTML')
    else:
        await show_section(call.message, section_key, lang)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("mgmt_back:"))
async def mgmt_back(call: CallbackQuery):
    """Asosiy Rahbariyat menyusiga qaytish."""
    lang = call.data.split(":")[1]
    try:
        await call.answer()
    except Exception:
        pass
    await call.message.delete()
    kb = await mgmt_kb(lang)
    await call.message.answer(mgmt_header(lang), reply_markup=kb, parse_mode='HTML')
