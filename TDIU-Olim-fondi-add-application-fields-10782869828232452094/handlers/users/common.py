import time
from aiogram.types import Message
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from handlers.users.start import start
from states.states import AppealStates
from loader import dp, db
from utils.misc.lang_text import uz_text_1, ru_text_1, change_lang_text_uz, change_lang_text_ru
from keyboards.default.Student_DB import build_main_kb_uz, build_main_kb_ru


@dp.message_handler(text=['🏠 Bosh menyu', '🏠 Главное меню', '🏠Bosh Menyu', '🏠Главное меню'], state='*')
async def bosh_menyu(msg: Message, state: FSMContext):
    await state.finish()
    user = await db.select_user(str(msg.from_user.id))
    if not user:
        return
    registered = user.get('registered', False)
    if user['language'] == 'uz':
        await uz_text_1(msg, registered=registered)
    else:
        await ru_text_1(msg, registered=registered)


@dp.message_handler(text=['⬅️Ortga', "⬅️Назад"], state=AppealStates.writing)
@dp.message_handler(text=['⬅️Ortga', "⬅️Назад"])
async def back_to_menu(msg: Message, state: FSMContext):
    await state.finish()
    user = await db.select_user(str(msg.from_user.id))
    if not user:
        return
    registered = user.get('registered', False)
    if user['language'] == 'uz':
        await uz_text_1(msg, registered=registered)
    else:
        await ru_text_1(msg, registered=registered)


@dp.message_handler(text=["🇷🇺Изменить язык🇺🇿", "🇺🇿Tilni o'zgartish🇷🇺"])
async def change_lang(msg: Message, state: FSMContext):
    lang_ = (await db.select_user(str(msg.from_user.id)))['language']
    lang_code = 'ru' if lang_ == 'uz' else 'uz'
    await db.execute(
        "UPDATE users SET language=$1 WHERE id=$2",
        lang_code, str(msg.from_user.id), execute=True
    )
    if lang_ != 'uz':
        await change_lang_text_uz(msg)
    else:
        await change_lang_text_ru(msg)
    time.sleep(1)
    await start(msg, state)


@dp.message_handler(commands=['cancel'], state='*')
@dp.message_handler(Text(equals=['cancel', 'bekor qilish', 'отмена'], ignore_case=True), state='*')
async def global_cancel_handler(msg: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    registered = user.get('registered', False) if user else False
    user_id = str(msg.from_user.id)
    kb = await (
        build_main_kb_uz(db, registered, user_id)
        if lang == 'uz' else build_main_kb_ru(db, registered, user_id)
    )
    if lang == 'uz':
        await msg.answer("❌ Jarayon bekor qilindi.", reply_markup=kb)
    else:
        await msg.answer("❌ Процесс отменен.", reply_markup=kb)
