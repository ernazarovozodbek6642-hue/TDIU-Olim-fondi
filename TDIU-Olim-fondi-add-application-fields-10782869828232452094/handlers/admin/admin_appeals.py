from aiogram.types import CallbackQuery, Message
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from loader import dp, db, bot
from utils.misc.admin_access import admin_allowed
from states.states import AdminAppealReplyStates
from keyboards.inline.admin_kb import appeals_list_kb, appeal_detail_kb, back_to_admin_kb
from datetime import datetime
import pytz


@dp.callback_query_handler(text='adm:appeals')
async def admin_appeals(call: CallbackQuery):
    if not await admin_allowed(call.from_user.id, 'users'):
        return
    appeals = await db.get_unanswered_appeals()
    if not appeals:
        await call.message.edit_text(
            "📩 <b>Javob berilmagan murojaatlar yo'q</b>",
            reply_markup=back_to_admin_kb(), parse_mode='HTML'
        )
        return
    await call.message.edit_text(
        f"📩 <b>Javob berilmagan murojaatlar: {len(appeals)} ta</b>\n\nBirini tanlang:",
        reply_markup=appeals_list_kb(appeals), parse_mode='HTML'
    )


@dp.callback_query_handler(Text(startswith='ap:'))
async def appeal_detail(call: CallbackQuery):
    if not await admin_allowed(call.from_user.id, 'users'):
        return
    appeal_id = int(call.data.split(':')[1])
    appeal = await db.get_appeal_by_id(appeal_id)
    if not appeal:
        await call.answer("Murojaat topilmadi")
        return
    name = appeal.get('real_name') or appeal.get('full_name') or 'Noma\'lum'
    subject = appeal.get('subject') or 'Mavzusiz'
    message = appeal.get('message') or ''
    created = appeal.get('created_at')
    date_str = created.strftime('%d.%m.%Y %H:%M') if created else '-'

    await call.message.edit_text(
        f"📩 <b>Murojaat #{appeal_id}</b>\n\n"
        f"👤 Foydalanuvchi: <b>{name}</b>\n"
        f"📝 Mavzu: {subject}\n"
        f"💬 Matn: <i>{message}</i>\n"
        f"📅 Sana: {date_str}",
        reply_markup=appeal_detail_kb(appeal_id), parse_mode='HTML'
    )


@dp.callback_query_handler(Text(startswith='ap_reply:'))
async def start_reply(call: CallbackQuery, state: FSMContext):
    if not await admin_allowed(call.from_user.id, 'users'):
        return
    appeal_id = int(call.data.split(':')[1])
    await state.update_data(appeal_id=appeal_id)
    await call.message.answer("✉️ Javob matnini yozing:")
    await AdminAppealReplyStates.reply.set()


@dp.message_handler(state=AdminAppealReplyStates.reply)
async def send_reply(msg: Message, state: FSMContext):
    if not await admin_allowed(msg.from_user.id, 'users'):
        return
    data = await state.get_data()
    appeal_id = data.get('appeal_id')
    appeal = await db.get_appeal_by_id(appeal_id)
    await state.finish()

    if not appeal:
        await msg.answer("❌ Murojaat topilmadi")
        return

    tz = pytz.timezone("Asia/Tashkent")
    now = datetime.now(tz)
    await db.add_answer(appeal_id=appeal_id, answer_text=msg.text,
                        created_at=now.replace(tzinfo=None))
    await db.mark_appeal_answered(appeal_id)

    # Foydalanuvchiga yuborish
    lang = appeal.get('language', 'uz')
    subject = appeal.get('subject') or 'Mavzusiz'
    original = appeal.get('message') or ''
    user_id = appeal.get('user_id')

    try:
        if lang == 'uz':
            await bot.send_message(
                user_id,
                f"📩 <b>Murojaatingizga javob keldi!</b>\n\n"
                f"📝 Mavzu: {subject}\n"
                f"💬 Sizning murojaatingiz: <i>{original}</i>\n\n"
                f"✅ Javob: <i>{msg.text}</i>",
                parse_mode='HTML'
            )
        else:
            await bot.send_message(
                user_id,
                f"📩 <b>Получен ответ на ваше обращение!</b>\n\n"
                f"📝 Тема: {subject}\n"
                f"💬 Ваше обращение: <i>{original}</i>\n\n"
                f"✅ Ответ: <i>{msg.text}</i>",
                parse_mode='HTML'
            )
        await msg.answer(f"✅ Javob yuborildi!")
    except Exception as e:
        await msg.answer(f"❌ Xatolik: {e}")
