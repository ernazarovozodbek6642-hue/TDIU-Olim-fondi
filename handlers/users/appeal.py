from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from loader import dp, db
from states.states import AppealStates
from keyboards.default.Student_DB import bosh_menu_uz, bosh_menu_ru
from utils.misc.lang_text import uz_text_1, ru_text_1, uz_conf_appeals, ru_conf_appeals
from keyboards.inline.student_IB import confirmation_uz, confirmation_ru
from datetime import datetime
import pytz


@dp.message_handler(text=["✍️️Murojaat yuborish", "✍️Отправить обращение"], state='*')
async def appeal(msg: Message, state: FSMContext):
    await state.finish()
    user = await db.select_user(str(msg.from_user.id))
    lang_code = user['language'] if user else 'uz'
    if lang_code == 'uz':
        await msg.answer(
            "✍️ <b>Murojaat yuborish</b>\n\n"
            "📝 Murojaat mavzusini kiriting:\n"
            "<i>(Masalan: Stipendiya to'lovi)</i>",
            reply_markup=bosh_menu_uz, parse_mode='HTML'
        )
    else:
        await msg.answer(
            "✍️ <b>Отправить обращение</b>\n\n"
            "📝 Введите тему обращения:\n"
            "<i>(Например: Выплата стипендии)</i>",
            reply_markup=bosh_menu_ru, parse_mode='HTML'
        )
    await AppealStates.subject.set()


@dp.message_handler(state=AppealStates.subject)
async def get_subject(msg: Message, state: FSMContext):
    await state.update_data(subject=msg.text)
    user = await db.select_user(str(msg.from_user.id))
    lang_code = user['language'] if user else 'uz'
    if lang_code == 'uz':
        await msg.answer(
            f"✅ Mavzu: <b>{msg.text}</b>\n\n"
            "💬 Murojaatingizni yozing:",
            reply_markup=bosh_menu_uz, parse_mode='HTML'
        )
    else:
        await msg.answer(
            f"✅ Тема: <b>{msg.text}</b>\n\n"
            "💬 Напишите ваше обращение:",
            reply_markup=bosh_menu_ru, parse_mode='HTML'
        )
    await AppealStates.writing.set()


@dp.message_handler(state=AppealStates.writing)
async def writing_appeals(msg: Message, state: FSMContext):
    await state.update_data(text_=msg.text)
    data = await state.get_data()
    subject = data.get('subject', '')
    user = await db.select_user(str(msg.from_user.id))
    lang_code = user['language'] if user else 'uz'
    if lang_code == 'uz':
        await msg.answer(
            f"📋 <b>Tasdiqlash</b>\n\n"
            f"📝 Mavzu: {subject}\n"
            f"💬 Matn: <i>{msg.text}</i>\n\n"
            "To'g'riligini tekshiring!",
            reply_markup=confirmation_uz, parse_mode='HTML'
        )
    else:
        await msg.answer(
            f"📋 <b>Подтверждение</b>\n\n"
            f"📝 Тема: {subject}\n"
            f"💬 Текст: <i>{msg.text}</i>\n\n"
            "Проверьте правильность!",
            reply_markup=confirmation_ru, parse_mode='HTML'
        )


@dp.callback_query_handler(text='conf', state=AppealStates.writing)
async def confirmation_appeals(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    data = await state.get_data()
    text_ = data.get('text_', '')
    subject = data.get('subject', '')
    user = await db.select_user(str(call.from_user.id))
    lang_code = user['language'] if user else 'uz'
    await uz_conf_appeals(call, text_=text_, subject=subject) if lang_code == 'uz' \
        else await ru_conf_appeals(call, text_=text_, subject=subject)
    await state.finish()


@dp.callback_query_handler(text='again', state=AppealStates.writing)
async def edit_appeal(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    user = await db.select_user(str(call.from_user.id))
    lang_code = user['language'] if user else 'uz'
    if lang_code == 'uz':
        await call.message.answer("✏️ Murojaatingizni qayta yozing:", reply_markup=bosh_menu_uz)
    else:
        await call.message.answer("✏️ Перепишите ваше обращение:", reply_markup=bosh_menu_ru)
    await AppealStates.writing.set()


@dp.callback_query_handler(text='cancel', state=AppealStates.writing)
@dp.callback_query_handler(text='cancel', state=AppealStates.subject)
async def cancel_appeal(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.finish()
    user = await db.select_user(str(call.from_user.id))
    registered = user.get('registered', False) if user else False
    lang_code = user['language'] if user else 'uz'
    if lang_code == 'uz':
        await call.message.answer("❌ Murojaat bekor qilindi.")
        await uz_text_1(call.message, registered=registered)
    else:
        await call.message.answer("❌ Обращение отменено.")
        await ru_text_1(call.message, registered=registered)
