import re
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import Message, Contact, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from loader import dp, db
from states.states import RegisterStates
from utils.misc.lang_text import uz_text_1, ru_text_1
from utils.misc.sheets import append_registration

PHONE_REGEX = re.compile(r'^\+998\d{9}$')

COURSES_UZ = ["1-kurs", "2-kurs", "3-kurs", "4-kurs", "Magistr"]
COURSES_RU = ["1-й курс", "2-й курс", "3-й курс", "4-й курс", "Магистр"]


def course_keyboard_uz():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(*[KeyboardButton(c) for c in COURSES_UZ])
    return kb


def course_keyboard_ru():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(*[KeyboardButton(c) for c in COURSES_RU])
    return kb


# "📬 2026/2027..." tugmasi endi handlers/users/ariza.py tomonidan boshqariladi


@dp.message_handler(state=RegisterStates.full_name)
async def get_full_name(msg: Message, state: FSMContext):
    await state.update_data(real_name=msg.text)
    user = await db.select_user(str(msg.from_user.id))
    lang_code = user.get('language', 'uz') if user else 'uz'
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if lang_code == 'uz':
        kb.add(KeyboardButton("📱 Telefon raqamni ulashish", request_contact=True))
        await msg.answer(
            "✅ Ism qabul qilindi!\n\n"
            "📱 Telefon raqamingizni ulashing yoki yozing:\n"
            "<i>Format: +998901234567</i>",
            reply_markup=kb, parse_mode='HTML'
        )
    else:
        kb.add(KeyboardButton("📱 Поделиться номером телефона", request_contact=True))
        await msg.answer(
            "✅ Имя принято!\n\n"
            "📱 Поделитесь номером или введите вручную:\n"
            "<i>Формат: +998901234567</i>",
            reply_markup=kb, parse_mode='HTML'
        )
    await RegisterStates.phone.set()


async def _save_phone_and_ask_otm(msg: Message, state: FSMContext, phone: str, lang_code: str):
    await state.update_data(phone=phone)
    if lang_code == 'uz':
        await msg.answer(
            "✅ Telefon raqam qabul qilindi!\n\n"
            "🏛 Qaysi OTMda o'qiysiz?\n"
            "<i>(Universitetingiz nomini yozing)</i>",
            reply_markup=ReplyKeyboardRemove(), parse_mode='HTML'
        )
    else:
        await msg.answer(
            "✅ Номер телефона принят!\n\n"
            "🏛 В каком вузе вы учитесь?\n"
            "<i>(Напишите название вашего университета)</i>",
            reply_markup=ReplyKeyboardRemove(), parse_mode='HTML'
        )
    await RegisterStates.otm.set()


@dp.message_handler(content_types=['contact'], state=RegisterStates.phone)
async def get_phone_contact(msg: Message, state: FSMContext):
    contact: Contact = msg.contact
    user = await db.select_user(str(msg.from_user.id))
    lang_code = user.get('language', 'uz') if user else 'uz'
    if contact.user_id != msg.from_user.id:
        if lang_code == 'uz':
            await msg.answer("❌ Iltimos, o'z telefon raqamingizni ulashing!")
        else:
            await msg.answer("❌ Пожалуйста, поделитесь своим номером телефона!")
        return
    phone = contact.phone_number
    if not phone.startswith('+'):
        phone = '+' + phone
    await _save_phone_and_ask_otm(msg, state, phone, lang_code)


@dp.message_handler(state=RegisterStates.phone)
async def get_phone_text(msg: Message, state: FSMContext):
    user = await db.select_user(str(msg.from_user.id))
    lang_code = user.get('language', 'uz') if user else 'uz'
    phone = msg.text.strip()
    if not PHONE_REGEX.match(phone):
        if lang_code == 'uz':
            await msg.answer(
                "❌ Noto'g'ri format!\n"
                "📱 Telefon raqamni to'g'ri kiriting:\n"
                "<b>+998901234567</b>",
                parse_mode='HTML'
            )
        else:
            await msg.answer(
                "❌ Неверный формат!\n"
                "📱 Введите номер правильно:\n"
                "<b>+998901234567</b>",
                parse_mode='HTML'
            )
        return
    await _save_phone_and_ask_otm(msg, state, phone, lang_code)


@dp.message_handler(state=RegisterStates.otm)
async def get_otm(msg: Message, state: FSMContext):
    await state.update_data(otm=msg.text)
    user = await db.select_user(str(msg.from_user.id))
    lang_code = user.get('language', 'uz') if user else 'uz'
    if lang_code == 'uz':
        await msg.answer("✅ OTM qabul qilindi!\n\n📚 Qaysi kursda o'qiysiz?",
                         reply_markup=course_keyboard_uz())
    else:
        await msg.answer("✅ Вуз принят!\n\n📚 На каком курсе вы учитесь?",
                         reply_markup=course_keyboard_ru())
    await RegisterStates.course.set()


@dp.message_handler(state=RegisterStates.course)
async def get_course(msg: Message, state: FSMContext):
    all_courses = COURSES_UZ + COURSES_RU
    user = await db.select_user(str(msg.from_user.id))
    lang_code = user.get('language', 'uz') if user else 'uz'
    if msg.text not in all_courses:
        if lang_code == 'uz':
            await msg.answer("❌ Iltimos, ro'yxatdan kursni tanlang!", reply_markup=course_keyboard_uz())
        else:
            await msg.answer("❌ Пожалуйста, выберите курс из списка!", reply_markup=course_keyboard_ru())
        return

    data = await state.get_data()
    real_name = data.get('real_name', '')
    phone = data.get('phone', '')
    otm = data.get('otm', '')

    await db.update_user_registration(
        user_id=str(msg.from_user.id),
        real_name=real_name, phone=phone, otm=otm, course=msg.text
    )
    await state.finish()

    await append_registration(
        full_name=real_name, username=msg.from_user.username,
        phone=phone, otm=otm, course=msg.text
    )

    if lang_code == 'uz':
        await msg.answer(
            "🎉 <b>Ro'yxatdan o'tish muvaffaqiyatli yakunlandi!</b>\n\n"
            f"👤 Ism: {real_name}\n📱 Telefon: {phone}\n🏛 OTM: {otm}\n📚 Kurs: {msg.text}",
            reply_markup=ReplyKeyboardRemove(), parse_mode='HTML'
        )
        await uz_text_1(msg, registered=True)
    else:
        await msg.answer(
            "🎉 <b>Регистрация успешно завершена!</b>\n\n"
            f"👤 Имя: {real_name}\n📱 Телефон: {phone}\n🏛 Вуз: {otm}\n📚 Курс: {msg.text}",
            reply_markup=ReplyKeyboardRemove(), parse_mode='HTML'
        )
        await ru_text_1(msg, registered=True)
