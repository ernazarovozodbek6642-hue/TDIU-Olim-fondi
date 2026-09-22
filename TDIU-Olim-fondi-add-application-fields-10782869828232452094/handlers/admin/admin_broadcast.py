from aiogram.types import CallbackQuery, Message
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from loader import dp, db, bot
from utils.misc.admin_access import admin_allowed
from states.states import AdminBroadcastStates
from keyboards.inline.admin_kb import broadcast_confirm_kb, back_to_admin_kb


@dp.callback_query_handler(text='adm:broadcast')
async def admin_broadcast(call: CallbackQuery, state: FSMContext):
    if not await admin_allowed(call.from_user.id, 'users'):
        return
    await call.message.answer("📢 Broadcast mavzusini kiriting:")
    await AdminBroadcastStates.subject.set()


@dp.message_handler(state=AdminBroadcastStates.subject)
async def broadcast_subject(msg: Message, state: FSMContext):
    if not await admin_allowed(msg.from_user.id, 'users'):
        return
    await state.update_data(subject=msg.text)
    await msg.answer("💬 Xabar matnini kiriting:")
    await AdminBroadcastStates.text.set()


@dp.message_handler(state=AdminBroadcastStates.text)
async def broadcast_text(msg: Message, state: FSMContext):
    if not await admin_allowed(msg.from_user.id, 'users'):
        return
    await state.update_data(text=msg.text)
    data = await state.get_data()
    registered_users = await db.select_registered_users()
    total = len(registered_users)
    await msg.answer(
        f"📋 <b>Tasdiqlash</b>\n\n"
        f"📢 Mavzu: <b>{data['subject']}</b>\n"
        f"💬 Matn: <i>{data['text']}</i>\n\n"
        f"👥 Qabul qiluvchilar: <b>{total} ta</b> (ro'yxatdan o'tganlar)",
        reply_markup=broadcast_confirm_kb(), parse_mode='HTML'
    )
    await AdminBroadcastStates.confirm.set()


@dp.callback_query_handler(text='bc:send', state=AdminBroadcastStates.confirm)
async def broadcast_send(call: CallbackQuery, state: FSMContext):
    if not await admin_allowed(call.from_user.id, 'users'):
        return
    data = await state.get_data()
    subject = data.get('subject', '')
    text = data.get('text', '')
    await state.finish()

    users = await db.select_registered_users()
    sent = 0
    blocked = 0
    for user in users:
        try:
            await bot.send_message(
                user['id'],
                f"📢 <b>{subject}</b>\n\n{text}",
                parse_mode='HTML'
            )
            sent += 1
        except Exception:
            blocked += 1

    await call.message.edit_text(
        f"✅ Broadcast yakunlandi!\n\n"
        f"📤 Yuborildi: <b>{sent}</b>\n"
        f"🚫 Blok qilganlar: <b>{blocked}</b>",
        parse_mode='HTML'
    )


@dp.callback_query_handler(text='bc:edit', state=AdminBroadcastStates.confirm)
async def broadcast_edit(call: CallbackQuery, state: FSMContext):
    await call.message.answer("💬 Xabar matnini qayta kiriting:")
    await AdminBroadcastStates.text.set()


@dp.callback_query_handler(text='bc:cancel', state=AdminBroadcastStates.confirm)
@dp.callback_query_handler(text='bc:cancel', state=AdminBroadcastStates.text)
async def broadcast_cancel(call: CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.edit_text("❌ Broadcast bekor qilindi.", reply_markup=back_to_admin_kb())
