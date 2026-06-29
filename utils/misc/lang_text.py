from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery, InputMediaPhoto

from data.config import ADMINS
from keyboards.default.Student_DB import (
    build_main_kb_uz, build_main_kb_ru,
    uz_management_list, ru_management_list,
    main_menu_uz, main_menu_ru, back_uz, back_ru
)
from loader import db as _db
from keyboards.inline.student_IB import confirmation_uz, confirmation_ru
from loader import bot, db
from datetime import datetime
import pytz

from states.states import SendFile
from utils.misc.student_list import get_students_keyboard_ru, get_students_keyboard_uz


async def uz_text_1(msg: Message, registered: bool = True):
    text = "Asosiy Menyu\n\nKerakli bo'limni tanlang"
    kb = await build_main_kb_uz(_db, registered)
    await msg.answer(text=text, reply_markup=kb)


async def ru_text_1(msg: Message, registered: bool = True):
    text = "Главное меню\n\nВыберите нужный раздел"
    kb = await build_main_kb_ru(_db, registered)
    await msg.answer(text=text, reply_markup=kb)


async def uz_management_info(msg: Message):
    text = ("Rahbariyat\n\n"
            "Kerakli bo'limni tanlang")
    await msg.answer(text=text, reply_markup=uz_management_list)


async def ru_management_info(msg: Message):
    text = ("Руководство\n\n"
            "Выберите нужный раздел")
    await msg.answer(text=text, reply_markup=ru_management_list)


async def uz_appeals(msg: Message):
    text = "Xurmatli talaba siz o'z murojaatingizni yozib qoldiring"
    await msg.answer(text=text, reply_markup=back_uz)


async def ru_appeals(msg: Message):
    text = "Уважаемый студент, пожалуйста, оставьте своё обращение"
    await msg.answer(text=text, reply_markup=back_ru)


async def uz_appeals_conf(msg: Message):
    text = (f"<b><i>{msg.text}</i></b>\n\n"
            f"Murojaat matningiz tog'riligini tekshiring!")
    await msg.answer(text=text, reply_markup=confirmation_uz, parse_mode='HTML')


async def ru_appeals_conf(msg: Message):
    text = (f"<b><i>{msg.text}</i></b>\n\n"
            f"Пожалуйста, проверьте правильность вашего обращения!")
    await msg.answer(text=text, reply_markup=confirmation_ru, parse_mode='HTML')


async def uz_conf_appeals(call: CallbackQuery, text_, subject: str = ''):
    tz = pytz.timezone("Asia/Tashkent")
    tashkent_time = datetime.now(tz)
    appeal = await db.add_appeal(
        user_id=str(call.from_user.id),
        message=text_,
        subject=subject,
        created_at=tashkent_time.replace(tzinfo=None)
    )
    for admin_id in ADMINS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=(
                    f"<b>Yangi murojaat!</b>\n\n"
                    f"Mavzu: {subject}\n"
                    f"Matn: <i>{text_}</i>\n\n"
                    f"Yuboruvchi: {call.from_user.mention}\n"
                    f"ID: <code>{call.from_user.id}</code>\n"
                    f"Murojaat ID: <code>{appeal['id']}</code>\n"
                    f"Til: O'zbek"
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass
    await call.message.answer(
        text="Sizning murojaatingiz anonim tarzda mas'ul shaxsga yuborildi",
        reply_markup=main_menu_uz
    )


async def ru_conf_appeals(call: CallbackQuery, text_, subject: str = ''):
    tz = pytz.timezone("Asia/Tashkent")
    tashkent_time = datetime.now(tz)
    appeal = await db.add_appeal(
        user_id=str(call.from_user.id),
        message=text_,
        subject=subject,
        created_at=tashkent_time.replace(tzinfo=None)
    )
    for admin_id in ADMINS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=(
                    f"<b>Yangi murojaat!</b>\n\n"
                    f"Тема: {subject}\n"
                    f"Текст: <i>{text_}</i>\n\n"
                    f"Отправитель: {call.from_user.mention}\n"
                    f"ID: <code>{call.from_user.id}</code>\n"
                    f"ID обращения: <code>{appeal['id']}</code>\n"
                    f"Язык: Русский"
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass
    await call.message.answer(
        text='Ваше обращение анонимно отправлено ответственному лицу',
        reply_markup=main_menu_ru
    )


async def again_write_uz(call: CallbackQuery):
    text = "Bemalol murojaatingizni qayta yozishingiz mumkin"
    await call.message.answer(text=text)


async def again_write_ru(call: CallbackQuery):
    text = "Вы можете спокойно переписать своё обращение"
    await call.message.answer(text=text)


async def fond_rah_uz(msg: Message):
    text = ("💼 <b>Fond ta'sischisi</b>\n\n"
            " \t<i><b>ZUHRA SHARIPOVA</b></i>")
    await msg.answer(text=text, reply_markup=main_menu_uz, parse_mode="HTML")


async def fond_rah_ru(msg: Message):
    text = ("💼 <b>Основатель фонда</b>\n\n"
            " \t<i><b>ZUHRA SHARIPOVA</b></i>")
    await msg.answer(text=text, reply_markup=main_menu_ru, parse_mode="HTML")


async def kuz_keng_rais_uz(msg: Message):
    text = ("👔 <b>Kuzatuv kengashi a'zolari</b>\n\n"
            "\t<i><b>1. ODIL XASANOV</b></i>\n\n"
            "\t<i><b>2. XASAN XASANOV</b></i>")
    await msg.answer(text=text, reply_markup=main_menu_uz, parse_mode="HTML")


async def kuz_keng_raisi_ru(msg: Message):
    text = ("👔 <b>Члены Наблюдательного совета</b>\n\n"
            "\t<i><b>1. ОДИЛ ХАСАНОВ</b></i>\n\n"
            "\t<i><b>2. ХАСАН ХАСАНОВ</b></i>")
    await msg.answer(text=text, reply_markup=main_menu_ru, parse_mode="HTML")


async def cordinator_uz(msg: Message):
    text = ("🤝 <b>Kuratorlar</b>\n\n"
            " \t<i><b>1. ZEBO SHARIPOVA</b></i>\n\n"
            " \t<i><b>2. BEKZOD ISTAMOV</b></i>\n\n"
            " \t<i><b>3. OZODBEK YO'LDOSHEV</b></i>\n\n"
            " \t<i><b>4. SHAXZODA ABBOSOVA</b></i>")
    await msg.answer(text=text, reply_markup=main_menu_uz, parse_mode="HTML")


async def cordinator_ru(msg: Message):
    text = ("🤝 <b>Кураторы</b>\n\n"
            "\t<i><b>1. ЗЕБО ШАРИПОВА</b></i>\n\n"
            "\t<i><b>2. БЕКЗОД ИСТАМОВ</b></i>\n\n"
            "\t<i><b>3. OZODBEK YO'LDOSHEV</b></i>\n\n"
            "\t<i><b>4. ШАХЗОДА АББОСОВА</b></i>")
    await msg.answer(text=text, reply_markup=main_menu_ru, parse_mode="HTML")


async def expert_uz(msg: Message):
    text = ("🧠 <b>Ekspertlar</b>\n\n"
            "Akademik faoliyat eksperti\n"
            " \t<i><b>ZARIFA MUMINOVA</b></i>\n\n"
            "Strategik rivojlantirish eksperti\n"
            " \t<i><b>AZAMAT AKBAROV</b></i>\n\n"
            "Moliyaviy ishlar eksperti\n"
            " \t<i><b>JAVOHIR BATIROV</b></i>")
    await msg.answer(text=text, reply_markup=main_menu_uz, parse_mode="HTML")


async def expert_ru(msg: Message):
    text = ("🧠 <b>Эксперты</b>\n\n"
            "Эксперт по академической деятельности\n"
            "\t<i><b>ЗАРИФА МУМИНОВА</b></i>\n\n"
            "Эксперт по стратегическому развитию\n"
            "\t<i><b>АЗАМАТ АКБАРОВ</b></i>\n\n"
            "Эксперт по финансовым вопросам\n"
            "\t<i><b>ЖАВОХИР БАТИРОВ</b></i>")
    await msg.answer(text=text, reply_markup=main_menu_ru, parse_mode="HTML")


async def volunteer_uz(msg: Message):
    text = ("🙌 <b>Volontyorlar</b>\n\n"
            " \t<i><b>1. FAXRIDDIN BURXONOV</b></i>\n\n"
            " \t<i><b>2. JURABEK SODIKOV</b></i>")
    await msg.answer(text=text, reply_markup=main_menu_uz, parse_mode="HTML")


async def volunteer_ru(msg: Message):
    text = ("🙌 <b>Волонтёры</b>\n\n"
            "\t<i><b>1. ФАХРИДДИН БУРХОНОВ</b></i>\n\n"
            "\t<i><b>2. ЖУРАБЕК СОДИКОВ</b></i>")
    await msg.answer(text=text, reply_markup=main_menu_ru, parse_mode="HTML")


async def change_lang_text_uz(msg: Message):
    text = "Til muvaffaqiyatli o'zgartirildi"
    await msg.answer(text=text, reply_markup=ReplyKeyboardRemove())


async def change_lang_text_ru(msg: Message):
    text = "Язык успешно изменён"
    await msg.answer(text=text, reply_markup=ReplyKeyboardRemove())


async def student_name_uz(msg):
    text_ = "O'zingizni F.I.SH tanlang!"
    msg_ = await msg.answer("...", reply_markup=back_uz)
    await msg_.delete()
    await msg.answer(text=text_, reply_markup=get_students_keyboard_uz(page=0))


async def student_name_ru(msg):
    text_ = "Выберите своё Ф.И.О!"
    msg_ = await msg.answer("...", reply_markup=back_ru)
    await msg_.delete()
    await msg.answer(text=text_, reply_markup=get_students_keyboard_ru(page=0))


async def file_theme_uz(msg: Message, student):
    text = f"Hurmatli {student} siz yubormoqchi bo'lgan hujjat mavzusini kiriting"
    await msg.answer(text=text, reply_markup=back_uz)
    await SendFile.theme.set()


async def file_theme_ru(msg: Message, student):
    text = f"Уважаемый(ая) {student}, введите тему документа"
    await msg.answer(text=text, reply_markup=back_ru)
    await SendFile.theme.set()


async def theme_next_uz(msg: Message, theme):
    text = f"<b><i>{theme}</i></b> ushbu mavzudagi hujjatingizni yuboring"
    await msg.answer(text=text, reply_markup=back_uz)


async def theme_next_ru(msg: Message, theme):
    text = f"<b><i>{theme}</i></b> Отправьте ваш документ по этой теме"
    await msg.answer(text=text, reply_markup=back_ru)


async def conf_file_uz(msg: Message, state: FSMContext):
    data = await state.get_data()
    theme = data['theme']
    file_id = data["file_id"]
    student = data['student']
    msg_ = await msg.answer("...", reply_markup=back_ru)
    await msg_.delete()
    text = (f"Hujjat Mavzusi: {theme}\n\n"
            f"Talaba: {student}")
    await msg.answer_document(document=file_id, caption=text, reply_markup=confirmation_uz)


async def conf_file_ru(msg: Message, state: FSMContext):
    data = await state.get_data()
    theme = data['theme']
    file_id = data["file_id"]
    student = data['student']
    msg_ = await msg.answer("...", reply_markup=back_ru)
    await msg_.delete()
    text = (f"Tema dokumenta: {theme}\n\n"
            f"Student: {student}")
    await msg.answer_document(document=file_id, caption=text, reply_markup=confirmation_ru)


async def conf_photo_uz(msg: Message, state: FSMContext):
    data = await state.get_data()
    theme = data['theme']
    file_id = data["file_id"]
    student = data['student']
    msg_ = await msg.answer("...", reply_markup=back_ru)
    await msg_.delete()
    text = (f"Hujjat Mavzusi: {theme}\n\n"
            f"Talaba: {student}")
    await msg.answer_photo(photo=file_id, caption=text, reply_markup=confirmation_uz)


async def conf_photo_ru(msg: Message, state: FSMContext):
    data = await state.get_data()
    theme = data['theme']
    file_id = data["file_id"]
    student = data['student']
    msg_ = await msg.answer("...", reply_markup=back_ru)
    await msg_.delete()
    text = (f"Tema dokumenta: {theme}\n\n"
            f"Student: {student}")
    await msg.answer_photo(photo=file_id, caption=text, reply_markup=confirmation_ru)


async def uz_conf_document(call: CallbackQuery, state: FSMContext):
    tz = pytz.timezone("Asia/Tashkent")
    tashkent_time = datetime.now(tz)
    data = await state.get_data()
    theme = data['theme']
    file_id = data['file_id']
    student = data['student']
    file_type = data['file_type']
    if file_type == 'photo':
        await bot.send_photo(
            chat_id=ADMINS[0], photo=file_id,
            caption=f"Hujjat mavzusi: <i><b>{theme}</b></i>\nTalaba: <i><b>{student}</b></i>\nYuboruvchi: {call.from_user.mention}"
        )
    elif file_type == 'document':
        await bot.send_document(
            chat_id=ADMINS[0], document=file_id,
            caption=f"Hujjat mavzusi: <i><b>{theme}</b></i>\nTalaba: <i><b>{student}</b></i>\nYuboruvchi: {call.from_user.mention}"
        )
    await call.message.answer(text="Sizning hujjatingiz mas'ul shaxsga yuborildi", reply_markup=main_menu_uz)
    await db.add_document(
        user_id=str(call.from_user.id), theme=theme,
        file_id=file_id, file_type=file_type,
        created_at=tashkent_time.replace(tzinfo=None)
    )


async def ru_conf_document(call: CallbackQuery, state: FSMContext):
    tz = pytz.timezone("Asia/Tashkent")
    tashkent_time = datetime.now(tz)
    data = await state.get_data()
    theme = data['theme']
    file_id = data['file_id']
    student = data['student']
    file_type = data['file_type']
    if file_type == 'photo':
        await bot.send_photo(
            chat_id=ADMINS[0], photo=file_id,
            caption=f"Тема документа: <i><b>{theme}</b></i>\nСтудент: <i><b>{student}</b></i>\nОтправитель: {call.from_user.mention}"
        )
    elif file_type == 'document':
        await bot.send_document(
            chat_id=ADMINS[0], document=file_id,
            caption=f"Тема документа: <i><b>{theme}</b></i>\nСтудент: <i><b>{student}</b></i>\nОтправитель: {call.from_user.mention}"
        )
    await call.message.answer(text="Ваш документ отправлен ответственному лицу", reply_markup=main_menu_ru)
    await db.add_document(
        user_id=str(call.from_user.id), theme=theme,
        file_id=file_id, file_type=file_type,
        created_at=tashkent_time.replace(tzinfo=None)
    )
