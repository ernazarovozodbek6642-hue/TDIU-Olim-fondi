from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

from loader import dp, db
from data.config import ADMINS
from keyboards.inline.admin_kb import admin_main_kb


@dp.message_handler(Command('admin'), state='*')
async def admin_panel(msg: Message, state: FSMContext):
    print(f"[DEBUG] /admin sent by user ID: {msg.from_user.id}, ADMINS: {ADMINS}")
    if str(msg.from_user.id) not in ADMINS:
        await msg.answer(f"⛔ Siz admin emassiz. ID: {msg.from_user.id}")
        return
    await state.finish()
    total = await db.count_users()
    registered = await db.count_registered_users()
    await msg.answer(
        f"🔐 <b>Admin panel</b>\n\n"
        f"👥 Jami: {total} | ✅ Ro'yxatdan o'tgan: {registered}",
        reply_markup=admin_main_kb(), parse_mode='HTML'
    )


@dp.callback_query_handler(text='adm:main', state='*')
async def back_to_admin_main(call: CallbackQuery, state: FSMContext):
    if str(call.from_user.id) not in ADMINS:
        return
    await state.finish()
    total = await db.count_users()
    registered = await db.count_registered_users()
    await call.message.edit_text(
        f"🔐 <b>Admin panel</b>\n\n"
        f"👥 Jami: {total} | ✅ Ro'yxatdan o'tgan: {registered}",
        reply_markup=admin_main_kb(), parse_mode='HTML'
    )
