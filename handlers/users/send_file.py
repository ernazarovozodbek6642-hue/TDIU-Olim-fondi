from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from loader import dp, db, bot
from states.states import SendFile
from data.config import ADMINS, STORAGE_CHANNEL
from keyboards.default.Student_DB import bosh_menu_uz, bosh_menu_ru, back_uz, back_ru, main_menu_uz, main_menu_ru
from keyboards.inline.student_IB import confirmation_uz, confirmation_ru
from utils.misc.lang_text import uz_text_1, ru_text_1
from utils.misc.student_list import get_students_keyboard_uz, get_students_keyboard_ru
from datetime import datetime
import pytz


@dp.message_handler(text=["📂Hujjat yuborish", "📂Отправить документ"], state='*')
async def send_file_start(msg: Message, state: FSMContext):
    await state.finish()
    user = await db.select_user(str(msg.from_user.id))
    lang_code = user['language'] if user else 'uz'

    if lang_code == 'uz':
        await msg.answer("📂 Talabalar ro'yxatidan o'zingizni tanlang 👇",
                         reply_markup=get_students_keyboard_uz(page=0))
    else:
        await msg.answer("📂 Выберите себя из списка студентов 👇",
                         reply_markup=get_students_keyboard_ru(page=0))
    await SendFile.student_list.set()


@dp.callback_query_handler(Text(startswith='page:'), state=SendFile.student_list)
async def change_page(call: CallbackQuery, state: FSMContext):
    page = int(call.data.split(":")[1])
    user = await db.select_user(str(call.from_user.id))
    lang_code = user['language'] if user else 'uz'
    if lang_code == 'uz':
        await call.message.edit_reply_markup(reply_markup=get_students_keyboard_uz(page))
    else:
        await call.message.edit_reply_markup(reply_markup=get_students_keyboard_ru(page))


@dp.callback_query_handler(Text(startswith="student:"), state=SendFile.student_list)
async def select_student(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    student = call.data.split(":")[1]
    await state.update_data(student=student)
    user = await db.select_user(str(call.from_user.id))
    lang_code = user['language'] if user else 'uz'
    if lang_code == 'uz':
        await call.message.answer(
            f"✅ Tanlandi: <b>{student}</b>\n\n"
            "📝 Hujjat mavzusini kiriting:",
            reply_markup=back_uz, parse_mode='HTML'
        )
    else:
        await call.message.answer(
            f"✅ Выбрано: <b>{student}</b>\n\n"
            "📝 Введите тему документа:",
            reply_markup=back_ru, parse_mode='HTML'
        )
    await SendFile.theme.set()


@dp.callback_query_handler(text='back_menu', state=SendFile.student_list)
async def back_to_menu_student(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.finish()
    user = await db.select_user(str(call.from_user.id))
    registered = user.get('registered', False) if user else False
    lang_code = user['language'] if user else 'uz'
    if lang_code == 'uz':
        await uz_text_1(call.message, registered=registered)
    else:
        await ru_text_1(call.message, registered=registered)


@dp.message_handler(text=['⬅️Ortga', "⬅️Назад"], state=SendFile.theme)
async def back_student(msg: Message, state: FSMContext):
    user = await db.select_user(str(msg.from_user.id))
    lang_code = user['language'] if user else 'uz'
    if lang_code == 'uz':
        await msg.answer("📂 Talabalar ro'yxatidan o'zingizni tanlang 👇",
                         reply_markup=get_students_keyboard_uz(page=0))
    else:
        await msg.answer("📂 Выберите себя из списка студентов 👇",
                         reply_markup=get_students_keyboard_ru(page=0))
    await SendFile.student_list.set()


@dp.message_handler(text=['⬅️Ortga', "⬅️Назад"], state=SendFile.send_file)
async def back_theme(msg: Message, state: FSMContext):
    data = await state.get_data()
    student = data.get('student', '')
    user = await db.select_user(str(msg.from_user.id))
    lang_code = user['language'] if user else 'uz'
    if lang_code == 'uz':
        await msg.answer(
            f"✅ Tanlandi: <b>{student}</b>\n\n📝 Hujjat mavzusini kiriting:",
            reply_markup=back_uz, parse_mode='HTML'
        )
    else:
        await msg.answer(
            f"✅ Выбрано: <b>{student}</b>\n\n📝 Введите тему документа:",
            reply_markup=back_ru, parse_mode='HTML'
        )
    await SendFile.theme.set()


@dp.message_handler(state=SendFile.theme)
async def theme(msg: Message, state: FSMContext):
    await state.update_data(theme=msg.text)
    user = await db.select_user(str(msg.from_user.id))
    lang_code = user['language'] if user else 'uz'
    if lang_code == 'uz':
        await msg.answer(
            f"✅ Mavzu: <b>{msg.text}</b>\n\n📎 Hujjatingizni yuboring (fayl yoki rasm):",
            reply_markup=back_uz, parse_mode='HTML'
        )
    else:
        await msg.answer(
            f"✅ Тема: <b>{msg.text}</b>\n\n📎 Отправьте ваш документ (файл или фото):",
            reply_markup=back_ru, parse_mode='HTML'
        )
    await SendFile.send_file.set()


@dp.message_handler(content_types=["document"], state=SendFile.send_file)
async def file(msg: Message, state: FSMContext):
    file_id = msg.document.file_id
    await state.update_data(file_id=file_id, file_type='document')
    await _show_confirmation(msg, state)


@dp.message_handler(content_types=["photo"], state=SendFile.send_file)
async def photo(msg: Message, state: FSMContext):
    file_id = msg.photo[-1].file_id
    await state.update_data(file_id=file_id, file_type='photo')
    await _show_confirmation(msg, state)


async def _show_confirmation(msg: Message, state: FSMContext):
    data = await state.get_data()
    theme = data.get('theme', '')
    student = data.get('student', '')
    file_id = data.get('file_id', '')
    file_type = data.get('file_type', '')
    user = await db.select_user(str(msg.from_user.id))
    lang_code = user['language'] if user else 'uz'
    caption = (
        f"📄 Mavzu: <b>{theme}</b>\n🎓 Talaba: <b>{student}</b>"
        if lang_code == 'uz' else
        f"📄 Тема: <b>{theme}</b>\n🎓 Студент: <b>{student}</b>"
    )
    kb = confirmation_uz if lang_code == 'uz' else confirmation_ru
    if file_type == 'photo':
        await msg.answer_photo(photo=file_id, caption=caption, reply_markup=kb, parse_mode='HTML')
    else:
        await msg.answer_document(document=file_id, caption=caption, reply_markup=kb, parse_mode='HTML')


@dp.callback_query_handler(text='conf', state=SendFile.send_file)
async def confirm_document(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    data = await state.get_data()
    theme = data.get('theme', '')
    file_id = data.get('file_id', '')
    student = data.get('student', '')
    file_type = data.get('file_type', '')
    user = await db.select_user(str(call.from_user.id))
    lang_code = user['language'] if user else 'uz'
    tz = pytz.timezone("Asia/Tashkent")
    tashkent_time = datetime.now(tz)

    # Storage channelga yuborish
    channel_message_id = None
    try:
        caption_ch = f"📄 {theme} | 🎓 {student} | 👤 {call.from_user.mention}"
        if file_type == 'photo':
            ch_msg = await bot.send_photo(STORAGE_CHANNEL, photo=file_id, caption=caption_ch)
        else:
            ch_msg = await bot.send_document(STORAGE_CHANNEL, document=file_id, caption=caption_ch)
        channel_message_id = ch_msg.message_id
    except Exception as e:
        print(f"[STORAGE CHANNEL ERROR] {e}")

    # Adminga yuborish
    admin_caption = (
        f"📄 Mavzu: {theme}\n🎓 Talaba: {student}\n👤 {call.from_user.mention}"
        if lang_code == 'uz' else
        f"📄 Тема: {theme}\n🎓 Студент: {student}\n👤 {call.from_user.mention}"
    )
    try:
        if file_type == 'photo':
            await bot.send_photo(ADMINS[0], photo=file_id, caption=admin_caption, parse_mode='HTML')
        else:
            await bot.send_document(ADMINS[0], document=file_id, caption=admin_caption, parse_mode='HTML')
    except Exception as e:
        print(f"[ADMIN SEND ERROR] {e}")

    # Bazaga saqlash
    await db.add_document(
        user_id=str(call.from_user.id),
        theme=theme,
        file_id=file_id,
        file_type=file_type,
        channel_message_id=channel_message_id,
        created_at=tashkent_time.replace(tzinfo=None)
    )
    await state.finish()

    if lang_code == 'uz':
        await call.message.answer("✅ Hujjatingiz mas'ul shaxsga yuborildi!", reply_markup=main_menu_uz)
    else:
        await call.message.answer("✅ Ваш документ отправлен ответственному лицу!", reply_markup=main_menu_ru)


@dp.callback_query_handler(text='again', state=SendFile.send_file)
async def edit_document(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    data = await state.get_data()
    student = data.get('student', '')
    user = await db.select_user(str(call.from_user.id))
    lang_code = user['language'] if user else 'uz'
    if lang_code == 'uz':
        await call.message.answer(
            f"✅ Tanlandi: <b>{student}</b>\n\n📎 Hujjatingizni qayta yuboring:",
            reply_markup=back_uz, parse_mode='HTML'
        )
    else:
        await call.message.answer(
            f"✅ Выбрано: <b>{student}</b>\n\n📎 Отправьте документ заново:",
            reply_markup=back_ru, parse_mode='HTML'
        )


@dp.callback_query_handler(text='cancel', state=SendFile.send_file)
@dp.callback_query_handler(text='cancel', state=SendFile.theme)
@dp.callback_query_handler(text='cancel', state=SendFile.student_list)
async def cancel_document(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.finish()
    user = await db.select_user(str(call.from_user.id))
    registered = user.get('registered', False) if user else False
    lang_code = user['language'] if user else 'uz'
    if lang_code == 'uz':
        await call.message.answer("❌ Bekor qilindi.")
        await uz_text_1(call.message, registered=registered)
    else:
        await call.message.answer("❌ Отменено.")
        await ru_text_1(call.message, registered=registered)
