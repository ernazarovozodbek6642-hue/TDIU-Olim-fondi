import time

from states.states import AppealStates
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart, Text
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from keyboards.inline.student_IB import lang
from utils.misc.lang_text import uz_text_1, ru_text_1, uz_management_info, ru_management_info, uz_appeals, ru_appeals, \
    uz_appeals_conf, ru_appeals_conf, uz_conf_appeals, ru_conf_appeals, again_write_uz, again_write_ru, fond_rah_uz, \
    fond_rah_ru, kuz_keng_rais_uz, kuz_keng_raisi_ru, cordinator_uz, cordinato_ru, change_lang_text_uz, \
    change_lang_text_ru, expert_uz, expert_ru
from loader import dp, db
from datetime import datetime
import pytz


@dp.message_handler(CommandStart())
async def start(msg: Message):
    user = await db.select_user(str(msg.from_user.id))
    if not user:
        await msg.answer(
            "Assalomu aleykum hurmatli foydalanuvchi!\n"
            "Botdan foydalanish uchun tilni tanlang🤳\n"
            "-----------------------------------------------\n"
            "Здравствуйте, уважаемый студент.\n"
            "Выберите язык для использования бота🤳",
            reply_markup=lang
        )
        return

    lang_code = user.get('language', 'uz')
    if lang_code == 'uz':
        await uz_text_1(msg)
    else:
        await ru_text_1(msg)


@dp.callback_query_handler(Text(startswith='lang'))
async def first_step(call: CallbackQuery, state: FSMContext):
    tz = pytz.timezone("Asia/Tashkent")
    tashkent_time = datetime.now(tz)
    await call.message.delete()
    await db.add_user(id=str(call.from_user.id), full_name=call.from_user.full_name,
                      username=call.from_user.username, date_time=tashkent_time.replace(tzinfo=None),
                      language=(call.data.split(':')[1]))
    if (await db.select_user(str(call.from_user.id)))['language'] == 'uz':
        await uz_text_1(call.message)
    else:
        await ru_text_1(call.message)


@dp.message_handler(text=['👤Rahbariyat', "👤Руководство"])
async def management_info(msg: Message, state: FSMContext):
    user = await db.select_user(str(msg.from_user.id))
    if user['language'] == 'uz':
        await uz_management_info(msg)
    else:
        await ru_management_info(msg)


@dp.message_handler(text=["✍️️Murojaat yuborish", "✍️Отправить обращение"])
async def appeal(msg: Message, state: FSMContext):
    if (await db.select_user(str(msg.from_user.id)))['language'] == 'uz':
        await uz_appeals(msg)
    else:
        await ru_appeals(msg)
    await AppealStates.writing.set()


@dp.message_handler(text=['⬅️Ortga', '⬅️Назад'], state=AppealStates.writing)
async def back_to_menu(msg: Message, state: FSMContext):
    if (await db.select_user(str(msg.from_user.id)))['language'] == 'uz':
        await uz_text_1(msg)
    else:
        await ru_text_1(msg)
    await state.finish()


@dp.message_handler(state=AppealStates.writing)
async def writing_appeals(msg: Message, state: FSMContext):
    await state.update_data(
        {
            'text_': msg.text
        }
    )
    if (await db.select_user(str(msg.from_user.id)))['language'] == 'uz':
        await uz_appeals_conf(msg)
    else:
        await ru_appeals_conf(msg)


@dp.callback_query_handler(text='conf', state=AppealStates.writing)
async def confirmation_appeals(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    data = await state.get_data()
    if (await db.select_user(str(call.from_user.id)))['language'] == 'uz':
        await uz_conf_appeals(call, text_=data['text_'])
    else:
        await ru_conf_appeals(call, text_=data['text_'])
    await state.finish()


@dp.callback_query_handler(text='again', state=AppealStates.writing)
async def again(call: CallbackQuery):
    await call.message.delete()
    if (await db.select_user(str(call.from_user.id)))['language'] == 'uz':
        await again_write_uz(call)
    else:
        await again_write_ru(call)


@dp.message_handler(text=['🏠Главное меню', '🏠Bosh Menyu', '⬅️Ortga', "⬅️Назад"], state='*')
async def back_to_menu(msg: Message):
    if (await db.select_user(str(msg.from_user.id)))['language'] == 'uz':
        await uz_text_1(msg)
    else:
        await ru_text_1(msg)


@dp.message_handler(text=['💼 Fond rahbari', '💼 Руководитель фонда'])
async def dekan__info(msg: Message):
    if (await db.select_user(str(msg.from_user.id)))['language'] == 'uz':
        await fond_rah_uz(msg)
    else:
        await fond_rah_ru(msg)


@dp.message_handler(text=['👔 Kuzatuv kengashi raisi', '👔 Председатель наблюдательного совета'])
async def zam_dekan__info(msg: Message):
    if (await db.select_user(str(msg.from_user.id)))['language'] == 'uz':
        await kuz_keng_rais_uz(msg)
    else:
        await kuz_keng_raisi_ru(msg)


@dp.message_handler(text=['🤝 Koordinator', '🤝 Координатор'])
async def yoshlar_yetakchisi(msg: Message):
    if (await db.select_user(str(msg.from_user.id)))['language'] == 'uz':
        await cordinator_uz(msg)
    else:
        await cordinato_ru(msg)


@dp.message_handler(text=['🧠 Ekspert', '🧠 Эксперт'])
async def expert(msg: Message):
    if (await db.select_user(str(msg.from_user.id)))['language'] == 'uz':
        await expert_uz(msg)
    else:
        await expert_ru(msg)


@dp.message_handler(text=['🇷🇺Изменить язык🇺🇿', "🇺🇿Tilni o'zgartish🇷🇺"])
async def change_lang(msg: Message):
    lang_ = (await db.select_user(str(msg.from_user.id)))['language']
    if lang_ == 'uz':
        lang_code = 'ru'
    else:
        lang_code = "uz"
    await db.execute(
        "UPDATE users SET language=$1 WHERE id=$2",
        lang_code,
        str(msg.from_user.id),
        execute=True
    )
    if lang_ != 'uz':
        await change_lang_text_uz(msg)
    else:
        await change_lang_text_ru(msg)
    time.sleep(1)
    await start(msg)


@dp.message_handler(content_types=['photo'])
async def photo_id(msg: Message):
    print(msg.photo[-1].file_id)
