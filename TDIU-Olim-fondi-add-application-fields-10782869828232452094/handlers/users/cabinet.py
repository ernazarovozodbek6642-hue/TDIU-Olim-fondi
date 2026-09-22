from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from loader import dp, db

STATUS_UZ = {
    'pending':   '⏳ Ko\'rib chiqilmoqda',
    'approved':  '✅ Tasdiqlangan',
    'rejected':  '❌ Rad etilgan',
    'cancelled': '🗑 Bekor qilingan',
}
STATUS_RU = {
    'pending':   '⏳ На рассмотрении',
    'approved':  '✅ Одобрена',
    'rejected':  '❌ Отклонена',
    'cancelled': '🗑 Отменена',
}


@dp.callback_query_handler(text='noop')
async def noop(call: CallbackQuery):
    await call.answer()


@dp.message_handler(Text(equals=["🗂 Shaxsiy kabinet", "🗂 Личный кабинет"]), state='*')
async def show_cabinet(msg: Message, state: FSMContext):
    await state.finish()
    user = await db.select_user(str(msg.from_user.id))
    if not user:
        return
    lang = user.get('language', 'uz')

    user_arizalar = await db.select_user_arizalar(str(msg.from_user.id))

    if user_arizalar:
        latest = user_arizalar[0]
        fish = latest['fish'] or user.get('real_name') or user.get('full_name') or '—'
        phone = latest['telefon'] or user.get('phone') or '—'
        otm = latest['otm'] or user.get('otm') or '—'
        course = latest['kurs'] or user.get('course') or '—'

        if lang == 'uz':
            text = (
                "🗂 <b>Shaxsiy kabinet</b>\n\n"
                f"👤 F.I.SH: {fish}\n"
                f"📱 Telefon: {phone}\n"
                f"🏛 OTM: {otm}\n"
                f"📚 Kurs: {course}\n\n"
                f"📝 <b>Arizalar tarixi:</b>\n"
            )
            for a in user_arizalar:
                sess_name = a.get('session_name') or "Legacy"
                created = a['created_at'].strftime('%d.%m.%Y %H:%M') if a.get('created_at') else '—'
                status_label = STATUS_UZ.get(a['status'], a['status'])
                text += f"• <b>{sess_name}</b>: {status_label} <i>({created})</i>\n"
                if a['status'] == 'rejected' and a.get('rejection_reason'):
                    text += f"  ↳ Rad sababi: <i>{a['rejection_reason']}</i>\n"
        else:
            text = (
                "🗂 <b>Личный кабинет</b>\n\n"
                f"👤 Ф.И.О: {fish}\n"
                f"📱 Телефон: {phone}\n"
                f"🏛 Вуз: {otm}\n"
                f"📚 Курс: {course}\n\n"
                f"📝 <b>История заявок:</b>\n"
            )
            for a in user_arizalar:
                sess_name = a.get('session_name') or "Legacy"
                created = a['created_at'].strftime('%d.%m.%Y %H:%M') if a.get('created_at') else '—'
                status_label = STATUS_RU.get(a['status'], a['status'])
                text += f"• <b>{sess_name}</b>: {status_label} <i>({created})</i>\n"
                if a['status'] == 'rejected' and a.get('rejection_reason'):
                    text += f"  ↳ Причина: <i>{a['rejection_reason']}</i>\n"

        await msg.answer(text, parse_mode='HTML')

    else:
        # Ariza yuborilmagan
        active_sess = await db.get_active_session()
        if not active_sess:
            await msg.answer(
                "🗂 <b>Shaxsiy kabinet</b>\n\nHozir grant arizasi uchun faol sessiya yo‘q."
                if lang == 'uz' else
                "🗂 <b>Личный кабинет</b>\n\nСейчас нет активной сессии для подачи заявки.",
                parse_mode='HTML'
            )
            return
        sess_name = active_sess['name']
        if lang == 'uz':
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("📝 Ariza yuborish", callback_data="cab:start_ariza")]
            ])
            await msg.answer(
                "🗂 <b>Shaxsiy kabinet</b>\n\n"
                "Siz hali ariza yubormagansiz.\n\n"
                f"Sessiya: <b>{sess_name}</b> uchun ariza topshirish uchun quyidagi tugmani bosing 👇",
                reply_markup=kb, parse_mode='HTML'
            )
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("📝 Подать заявку", callback_data="cab:start_ariza")]
            ])
            await msg.answer(
                "🗂 <b>Личный кабинет</b>\n\n"
                "Вы ещё не подавали заявку.\n\n"
                f"Нажмите кнопку ниже для подачи заявки на <b>{sess_name}</b> 👇",
                reply_markup=kb, parse_mode='HTML'
            )


@dp.callback_query_handler(text='cab:start_ariza')
async def cabinet_start_ariza(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.delete()
    from handlers.users.ariza import _start_ariza_form
    user = await db.select_user(str(call.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    await _start_ariza_form(call.message, lang)
