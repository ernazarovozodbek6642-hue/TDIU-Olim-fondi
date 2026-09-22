from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from loader import dp, db, bot
from utils.misc.admin_access import admin_allowed
from states.states import AdminChatStates
from keyboards.inline.admin_kb import users_list_kb, chat_end_kb, back_to_admin_kb

# Aktiv chat sessiyalari: {admin_id: user_id, user_id: admin_id}
active_sessions = {}
# Sahifa xotirasi: {admin_id: (users_list, page)}
users_cache = {}


def user_detail_kb(user_id, registered):
    toggle_label = "⏳ Ruxsatni o'chirish" if registered else "✅ Ruxsat berish"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("💬 Chat boshlash", callback_data=f"chat_start:{user_id}"),
            InlineKeyboardButton(toggle_label, callback_data=f"toggle_reg:{user_id}")
        ],
        [InlineKeyboardButton("⬅️ Ortga", callback_data="adm:users")]
    ])


@dp.callback_query_handler(text='adm:users', state='*')
async def admin_users(call: CallbackQuery):
    if not await admin_allowed(call.from_user.id, 'users'):
        return
    await call.answer()
    users = await db.select_all_users()
    users_cache[str(call.from_user.id)] = users
    await call.message.edit_text(
        f"👥 <b>Foydalanuvchilar ({len(users)} ta)</b>\n\nBirini tanlang:",
        reply_markup=users_list_kb(users, page=0), parse_mode='HTML'
    )


@dp.callback_query_handler(Text(startswith='usrpage:'))
async def users_page(call: CallbackQuery):
    if not await admin_allowed(call.from_user.id, 'users'):
        return
    page = int(call.data.split(':')[1])
    users = users_cache.get(str(call.from_user.id), [])
    await call.message.edit_reply_markup(reply_markup=users_list_kb(users, page=page))


@dp.callback_query_handler(Text(startswith='chatuser:'))
async def show_user_details(call: CallbackQuery):
    if not await admin_allowed(call.from_user.id, 'users'):
        return
    target_user_id = call.data.split(':')[1]
    user = await db.select_user(target_user_id)
    if not user:
        await call.answer("Foydalanuvchi topilmadi", show_alert=True)
        return

    name = user.get('real_name') or user.get('full_name') or "Noma'lum"
    phone = user.get('phone') or "Yo'q"
    otm = user.get('otm') or "Yo'q"
    course = user.get('course') or "Yo'q"
    username = f"@{user['username']}" if user.get('username') else "Yo'q"
    registered_status = "Ruxsat berilgan ✅" if user.get('registered') else "Kutilmoqda (Ruxsat berilmagan) ⏳"

    text = (
        f"👤 <b>Foydalanuvchi ma'lumotlari</b>\n\n"
        f"• Telegram: {user['full_name']} ({username})\n"
        f"• F.I.SH: <b>{name}</b>\n"
        f"• Telefon: {phone}\n"
        f"• OTM: {otm}\n"
        f"• Kurs: {course}\n"
        f"• Hujjat topshirish huquqi: <b>{registered_status}</b>\n\n"
        f"Tanlang:"
    )

    await call.message.edit_text(
        text,
        reply_markup=user_detail_kb(target_user_id, user.get('registered', False)),
        parse_mode='HTML'
    )


@dp.callback_query_handler(Text(startswith='toggle_reg:'))
async def toggle_registration(call: CallbackQuery):
    if not await admin_allowed(call.from_user.id, 'users'):
        return
    target_user_id = call.data.split(':')[1]
    user = await db.select_user(target_user_id)
    if not user:
        await call.answer("Foydalanuvchi topilmadi", show_alert=True)
        return

    new_status = not user.get('registered', False)
    await db.execute("UPDATE users SET registered=$2 WHERE id=$1", target_user_id, new_status, execute=True)

    # Foydalanuvchini xabardor qilish
    try:
        if new_status:
            await bot.send_message(
                target_user_id,
                "🎉 <b>Tabriklaymiz!</b>\n\n"
                "Admin sizga «📂 Hujjat yuborish» bo'limidan foydalanishga ruxsat berdi.",
                parse_mode='HTML'
            )
        else:
            await bot.send_message(
                target_user_id,
                "⏳ Admin sizning «📂 Hujjat yuborish» bo'limidan foydalanish ruxsatingizni vaqtincha to'xtatdi.",
                parse_mode='HTML'
            )
    except Exception:
        pass

    # Yangilangan ko'rinishni qayta yuklash
    user = await db.select_user(target_user_id)
    name = user.get('real_name') or user.get('full_name') or "Noma'lum"
    phone = user.get('phone') or "Yo'q"
    otm = user.get('otm') or "Yo'q"
    course = user.get('course') or "Yo'q"
    username = f"@{user['username']}" if user.get('username') else "Yo'q"
    registered_status = "Ruxsat berilgan ✅" if user.get('registered') else "Kutilmoqda (Ruxsat berilmagan) ⏳"

    text = (
        f"👤 <b>Foydalanuvchi ma'lumotlari</b>\n\n"
        f"• Telegram: {user['full_name']} ({username})\n"
        f"• F.I.SH: <b>{name}</b>\n"
        f"• Telefon: {phone}\n"
        f"• OTM: {otm}\n"
        f"• Kurs: {course}\n"
        f"• Hujjat topshirish huquqi: <b>{registered_status}</b>\n\n"
        f"Tanlang:"
    )

    await call.answer("Ruxsat berildi" if new_status else "Ruxsat olindi")
    await call.message.edit_text(
        text,
        reply_markup=user_detail_kb(target_user_id, user.get('registered', False)),
        parse_mode='HTML'
    )


@dp.callback_query_handler(Text(startswith='chat_start:'))
async def start_chat(call: CallbackQuery, state: FSMContext):
    if not await admin_allowed(call.from_user.id, 'users'):
        return
    target_user_id = call.data.split(':')[1]
    user = await db.select_user(target_user_id)
    name = user.get('real_name') or user.get('full_name') or target_user_id if user else target_user_id

    # Sessiya ochish
    admin_id = str(call.from_user.id)
    active_sessions[admin_id] = target_user_id
    active_sessions[target_user_id] = admin_id

    await state.update_data(target_user_id=target_user_id)
    await AdminChatStates.chatting.set()

    await call.message.answer(
        f"💬 <b>{name}</b> bilan chat boshlandi.\n"
        "Xabar yozing — foydalanuvchiga yuboriladi.",
        reply_markup=chat_end_kb(), parse_mode='HTML'
    )

    # Foydalanuvchiga xabar
    try:
        await bot.send_message(
            target_user_id,
            "💬 Admin siz bilan chat boshladi. Xabaringizni yozing."
        )
    except Exception as e:
        print(f"[CHAT START ERROR] {e}")


@dp.callback_query_handler(text='chat:end', state=AdminChatStates.chatting)
async def end_chat(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    target_user_id = data.get('target_user_id')
    admin_id = str(call.from_user.id)

    # Sessiyani yopish
    active_sessions.pop(admin_id, None)
    active_sessions.pop(target_user_id, None)
    await state.finish()

    await call.message.answer("🔴 Chat yakunlandi.")
    try:
        await bot.send_message(target_user_id, "🔴 Admin chat yakunladi.")
    except Exception:
        pass


# ─── ADMIN XABAR YUBORGANDA → USERGA ───
@dp.message_handler(state=AdminChatStates.chatting)
async def admin_send_message(msg: Message, state: FSMContext):
    if not await admin_allowed(msg.from_user.id, 'users'):
        return
    data = await state.get_data()
    target_user_id = data.get('target_user_id')
    if not target_user_id:
        return

    try:
        if msg.reply_to_message and msg.reply_to_message.text:
            await bot.send_message(
                target_user_id,
                f"💬 <b>Asl xabar:</b> <i>{msg.reply_to_message.text[:100]}</i>\n"
                f"↩️ <b>Javob:</b> {msg.text}",
                parse_mode='HTML'
            )
        else:
            await bot.send_message(target_user_id, f"👨‍💼 Admin: {msg.text}")
    except Exception as e:
        await msg.answer(f"❌ Xabar yuborilmadi: {e}")


# ─── USER XABAR YUBORGANDA → ADMINGA ───
async def route_user_message_to_admin(msg: Message):
    """Agar foydalanuvchi aktiv chat sessiyasida bo'lsa, xabarni adminga yo'naltiradi."""
    user_id = str(msg.from_user.id)
    if user_id not in active_sessions:
        return False

    admin_id = active_sessions[user_id]
    user = await db.select_user(user_id)
    name = user.get('real_name') or user.get('full_name') or user_id if user else user_id

    try:
        if msg.reply_to_message and msg.reply_to_message.text:
            await bot.send_message(
                admin_id,
                f"👤 <b>{name}:</b>\n"
                f"💬 <b>Asl xabar:</b> <i>{msg.reply_to_message.text[:100]}</i>\n"
                f"↩️ <b>Javob:</b> {msg.text}",
                parse_mode='HTML'
            )
        else:
            await bot.send_message(admin_id, f"👤 <b>{name}:</b> {msg.text}", parse_mode='HTML')
    except Exception as e:
        print(f"[ROUTE ERROR] {e}")
    return True
