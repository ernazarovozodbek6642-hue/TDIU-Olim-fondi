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
    ariza = await db.get_ariza_by_user(str(msg.from_user.id))

    if ariza:
        status = ariza['status']
        created = ariza['created_at'].strftime('%d.%m.%Y %H:%M') if ariza.get('created_at') else '—'
        if lang == 'uz':
            text = (
                "🗂 <b>Shaxsiy kabinet</b>\n\n"
                f"👤 F.I.SH: {ariza['fish'] or '—'}\n"
                f"📱 Telefon: {ariza['telefon'] or '—'}\n"
                f"🏛 OTM: {ariza['otm'] or '—'}\n"
                f"📚 Kurs: {ariza['kurs'] or '—'}\n\n"
                f"📅 Ariza yuborilgan: {created}\n"
                f"📋 Holati: <b>{STATUS_UZ.get(status, status)}</b>"
            )
            if status == 'rejected' and ariza.get('rejection_reason'):
                text += f"\n❌ Sabab: <i>{ariza['rejection_reason']}</i>"
        else:
            text = (
                "🗂 <b>Личный кабинет</b>\n\n"
                f"👤 Ф.И.О: {ariza['fish'] or '—'}\n"
                f"📱 Телефон: {ariza['telefon'] or '—'}\n"
                f"🏛 Вуз: {ariza['otm'] or '—'}\n"
                f"📚 Курс: {ariza['kurs'] or '—'}\n\n"
                f"📅 Дата подачи: {created}\n"
                f"📋 Статус: <b>{STATUS_RU.get(status, status)}</b>"
            )
            if status == 'rejected' and ariza.get('rejection_reason'):
                text += f"\n❌ Причина: <i>{ariza['rejection_reason']}</i>"
        await msg.answer(text, parse_mode='HTML')

    else:
        # Ariza yuborilmagan
        if lang == 'uz':
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("📝 Ariza yuborish", callback_data="cab:start_ariza")]
            ])
            await msg.answer(
                "🗂 <b>Shaxsiy kabinet</b>\n\n"
                "Siz hali ariza yubormagansiz.\n\n"
                "2026/2027 o'quv yili uchun ariza topshirish uchun quyidagi tugmani bosing 👇",
                reply_markup=kb, parse_mode='HTML'
            )
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("📝 Подать заявку", callback_data="cab:start_ariza")]
            ])
            await msg.answer(
                "🗂 <b>Личный кабинет</b>\n\n"
                "Вы ещё не подавали заявку.\n\n"
                "Нажмите кнопку ниже для подачи заявки на 2026/2027 учебный год 👇",
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
