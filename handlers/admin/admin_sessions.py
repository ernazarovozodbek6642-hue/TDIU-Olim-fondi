from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from loader import dp, db, bot
from utils.misc.admin_access import admin_allowed
from states.states import AdminSessionStates
from keyboards.inline.admin_kb import back_to_admin_kb

def sessions_menu_kb(sessions):
    buttons = []
    for s in sessions:
        status_icon = "🟢" if s['is_active'] else "⚪"
        buttons.append([InlineKeyboardButton(
            f"{status_icon} {s['name']}",
            callback_data=f"session_view:{s['id']}"
        )])
    buttons.append([InlineKeyboardButton("➕ Yangi sessiya yaratish", callback_data="session_new")])
    buttons.append([InlineKeyboardButton("⬅️ Ortga", callback_data="adm:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def session_detail_kb(session_id, is_active):
    buttons = []
    if not is_active:
        buttons.append([InlineKeyboardButton("🟢 Faollashtirish", callback_data=f"session_act:{session_id}")])
    buttons.append([InlineKeyboardButton("⬅️ Ortga", callback_data="adm:sessions")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.callback_query_handler(text='adm:sessions', state='*')
async def admin_sessions(call: CallbackQuery):
    if not await admin_allowed(call.from_user.id, 'applications'):
        return
    await call.answer()
    sessions = await db.get_all_sessions()
    await call.message.edit_text(
        "📅 <b>Sessiyalar boshqaruvi</b>\n\n"
        "Faol sessiya 🟢 belgisi bilan ko'rsatiladi. Botdagi barcha yangi arizalar faqat faol sessiyaga kelib tushadi.\n\n"
        "Tahrirlash yoki faollashtirish uchun birini tanlang:",
        reply_markup=sessions_menu_kb(sessions),
        parse_mode='HTML'
    )


@dp.callback_query_handler(Text(startswith='session_view:'))
async def view_session(call: CallbackQuery):
    if not await admin_allowed(call.from_user.id, 'applications'):
        return
    session_id = int(call.data.split(':')[1])
    s = await db.get_session_by_id(session_id)
    if not s:
        await call.answer("Sessiya topilmadi", show_alert=True)
        return

    status_str = "Faol 🟢" if s['is_active'] else "Nofaol ⚪"
    await call.message.edit_text(
        f"📅 <b>Sessiya ma'lumotlari</b>\n\n"
        f"• Nomi: <b>{s['name']}</b>\n"
        f"• Holati: {status_str}\n"
        f"• Yaratilgan sana: {s['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Tanlang:",
        reply_markup=session_detail_kb(session_id, s['is_active']),
        parse_mode='HTML'
    )


@dp.callback_query_handler(Text(startswith='session_act:'))
async def activate_session(call: CallbackQuery):
    if not await admin_allowed(call.from_user.id, 'applications'):
        return
    session_id = int(call.data.split(':')[1])
    s = await db.get_session_by_id(session_id)
    if not s:
        await call.answer("Sessiya topilmadi", show_alert=True)
        return

    await db.activate_session(session_id)
    await call.answer(f"«{s['name']}» sessiyasi faollashtirildi!")

    # Reload list
    sessions = await db.get_all_sessions()
    await call.message.edit_text(
        "📅 <b>Sessiyalar boshqaruvi</b>\n\n"
        "Faol sessiya 🟢 belgisi bilan ko'rsatiladi. Botdagi barcha yangi arizalar faqat faol sessiyaga kelib tushadi.\n\n"
        "Tahrirlash yoki faollashtirish uchun birini tanlang:",
        reply_markup=sessions_menu_kb(sessions),
        parse_mode='HTML'
    )


@dp.callback_query_handler(text='session_new')
async def create_session_start(call: CallbackQuery):
    if not await admin_allowed(call.from_user.id, 'applications'):
        return
    await call.answer()
    await call.message.answer(
        "➕ <b>Yangi sessiya yaratish</b>\n\n"
        "Yangi sessiya nomini kiriting:\n"
        "<i>Masalan: 2026/2027 Bahorgi</i>",
        parse_mode='HTML'
    )
    await AdminSessionStates.new_session_name.set()


@dp.message_handler(state=AdminSessionStates.new_session_name)
async def create_session_save(msg: Message, state: FSMContext):
    if not await admin_allowed(msg.from_user.id, 'applications'):
        return
    name = msg.text.strip()
    await state.finish()

    new_sess = await db.create_session(name)
    if new_sess:
        await msg.answer(
            f"✅ <b>«{name}» sessiyasi muvaffaqiyatli yaratildi!</b>\n\n"
            "Uni faollashtirish uchun ro'yxatdan tanlang.",
            parse_mode='HTML',
            reply_markup=back_to_admin_kb()
        )
    else:
        await msg.answer(
            "❌ Bunday nomli sessiya allaqachon mavjud yoki xatolik yuz berdi.",
            reply_markup=back_to_admin_kb()
        )
