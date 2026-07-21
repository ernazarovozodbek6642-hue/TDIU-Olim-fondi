from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart, Text
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from loader import dp, db
from keyboards.inline.student_IB import lang
from utils.misc.lang_text import uz_text_1, ru_text_1
from states.states import RegisterStates
from datetime import datetime
import pytz


@dp.message_handler(CommandStart(), state='*')
async def start(msg: Message, state: FSMContext):
    await state.finish()
    user = await db.select_user(str(msg.from_user.id))
    if not user:
        await msg.answer(
            "Assalomu aleykum hurmatli foydalanuvchi!\n"
            "Botdan foydalanish uchun tilni tanlang🤳\n"
            "───────────────────────────────\n"
            "Здравствуйте, уважаемый студент.\n"
            "Выберите язык для использования бота🤳",
            reply_markup=lang
        )
        return

    registered = user.get('registered', False)
    lang_code = user.get('language', 'uz')
    if lang_code == 'uz':
        await uz_text_1(msg, registered=registered)
    else:
        await ru_text_1(msg, registered=registered)


@dp.callback_query_handler(Text(startswith='lang'), state='*')
async def first_step(call: CallbackQuery, state: FSMContext):
    await state.finish()
    tz = pytz.timezone("Asia/Tashkent")
    tashkent_time = datetime.now(tz)
    await call.message.delete()
    lang_code = call.data.split(':')[1]
    await db.add_user(
        id=str(call.from_user.id),
        full_name=call.from_user.full_name,
        username=call.from_user.username,
        date_time=tashkent_time.replace(tzinfo=None),
        language=lang_code
    )
    # Yangi foydalanuvchi → bosh menyuni ko'rsatamiz (ro'yxatdan o'tmaganlar uchun)
    if lang_code == 'uz':
        await uz_text_1(call.message, registered=False)
    else:
        await ru_text_1(call.message, registered=False)
