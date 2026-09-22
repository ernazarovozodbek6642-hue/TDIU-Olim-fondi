from aiogram.types import CallbackQuery
from loader import dp, db
from utils.misc.admin_access import admin_allowed
from keyboards.inline.admin_kb import back_to_admin_kb


@dp.callback_query_handler(text='adm:stats', state='*')
async def admin_stats(call: CallbackQuery):
    if not await admin_allowed(call.from_user.id):
        return
    await call.answer()
    total = await db.count_users()
    registered = await db.count_registered_users()
    unregistered = total - registered
    appeals = await db.count_appeals()
    documents = await db.count_documents()
    document_permitted = await db.count_document_permitted_users()

    active_session = await db.get_active_session()

    # Active session stats
    session_text = ""
    if active_session:
        s_id = active_session['id']
        s_name = active_session['name']
        s_total = await db.count_arizalar(session_id=s_id)
        s_pending = await db.count_arizalar(status='pending', session_id=s_id)
        s_approved = await db.count_arizalar(status='approved', session_id=s_id)
        s_rejected = await db.count_arizalar(status='rejected', session_id=s_id)

        session_text = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 <b>Faol kampaniya:</b> {s_name}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📥 Ushbu kampaniyadagi jami arizalar: <b>{s_total} ta</b>\n"
            f"  🟡 Kutilmoqda: <b>{s_pending} ta</b>\n"
            f"  🟢 Tasdiqlandi: <b>{s_approved} ta</b>\n"
            f"  🔴 Rad etildi: <b>{s_rejected} ta</b>\n"
        )
    else:
        session_text = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 <b>Faol kampaniya:</b> Mavjud emas\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
        )

    # All-time application stats
    all_total = await db.count_arizalar()
    all_pending = await db.count_arizalar(status='pending')
    all_approved = await db.count_arizalar(status='approved')
    all_rejected = await db.count_arizalar(status='rejected')

    text = (
        "📊 <b>BOT STRUKTURALI STATISTIKASI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👥 <b>Foydalanuvchilar:</b>\n"
        f"  • Jami obunachilar: <b>{total} ta</b>\n"
        f"  • Hujjat topshirish huquqiga ega: <b>{document_permitted} ta</b>\n"
        f"  • Oddiy obunachilar: <b>{unregistered} ta</b>\n\n"
        "📩 <b>Murojaatlar va Hujjatlar:</b>\n"
        f"  • Jami kelgan murojaatlar: <b>{appeals} ta</b>\n"
        f"  • Jami topshirilgan alohida hujjatlar: <b>{documents} ta</b>\n\n"
        f"{session_text}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📈 <b>Barcha davrlardagi arizalar:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"  • Jami topshirilgan: <b>{all_total} ta</b>\n"
        f"  • Jami kutilayotgan: <b>{all_pending} ta</b>\n"
        f"  • Jami tasdiqlangan: <b>{all_approved} ta</b>\n"
        f"  • Jami rad etilgan: <b>{all_rejected} ta</b>"
    )

    await call.message.edit_text(
        text,
        reply_markup=back_to_admin_kb(),
        parse_mode='HTML'
    )
