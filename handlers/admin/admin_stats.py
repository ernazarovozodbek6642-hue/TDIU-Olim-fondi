from aiogram.types import CallbackQuery
from loader import dp, db
from data.config import ADMINS
from keyboards.inline.admin_kb import back_to_admin_kb


@dp.callback_query_handler(text='adm:stats')
async def admin_stats(call: CallbackQuery):
    if str(call.from_user.id) not in ADMINS:
        return
    total = await db.count_users()
    registered = await db.count_registered_users()
    unregistered = total - registered
    appeals = await db.count_appeals()
    documents = await db.count_documents()

    await call.message.edit_text(
        "📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{total}</b>\n"
        f"✅ Ro'yxatdan o'tganlar: <b>{registered}</b>\n"
        f"⏳ Ro'yxatdan o'tmaganlar: <b>{unregistered}</b>\n\n"
        f"📩 Jami murojaatlar: <b>{appeals}</b>\n"
        f"📂 Jami hujjatlar: <b>{documents}</b>",
        reply_markup=back_to_admin_kb(), parse_mode='HTML'
    )
