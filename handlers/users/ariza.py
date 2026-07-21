import re
from datetime import datetime

import pytz
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InputFile
)

from data.config import ADMINS, STORAGE_CHANNEL
from loader import dp, db, bot
from states.states import ArizaStates
from keyboards.default.Student_DB import build_main_kb_uz, build_main_kb_ru
from utils.misc.ariza_docx import generate_ariza_docx

PHONE_RE = re.compile(r'^\+998\d{9}$')

# ════════════════════════════════════════
#  INLINE KLAVIATURALAR
# ════════════════════════════════════════

def ha_yoq_kb(prefix: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("✅ Ha", callback_data=f"{prefix}:ha"),
            InlineKeyboardButton("❌ Yo'q", callback_data=f"{prefix}:yoq"),
        ]
    ])


def talim_shakli_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("🏫 Kunduzgi", callback_data="ts:kunduzgi"),
            InlineKeyboardButton("📚 Sirtqi", callback_data="ts:sirtqi"),
            InlineKeyboardButton("💻 Masofaviy", callback_data="ts:masofaviy"),
        ]
    ])


def kurs_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("1-kurs", callback_data="kurs:1-kurs"),
            InlineKeyboardButton("2-kurs", callback_data="kurs:2-kurs"),
            InlineKeyboardButton("3-kurs", callback_data="kurs:3-kurs"),
        ],
        [
            InlineKeyboardButton("4-kurs", callback_data="kurs:4-kurs"),
            InlineKeyboardButton("Magistr", callback_data="kurs:Magistr"),
        ]
    ])


def ariza_confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Yuborish", callback_data="ariza:yuborish")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="ariza:cancel_form")]
    ])


def cancel_ariza_kb(ariza_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🗑 Arizani bekor qilish", callback_data=f"ariza_user_cancel:{ariza_id}")]
    ])


# ─── Forma bekor qilish tugmasi (reply) ───
cancel_reply_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton("❌ Arizani to'xtatish")]],
    resize_keyboard=True
)


# ════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════

@dp.message_handler(
    Text(equals=["📬 2026/2027 o'quv yili uchun\nhujjat topshirish",
                 "📬 Подача документов\n2026/2027 уч. год"]),
    state='*'
)
async def ariza_start(msg: Message, state: FSMContext):
    await state.finish()
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'

    # Mavjud arizani tekshirish
    existing = await db.get_ariza_by_user(str(msg.from_user.id))
    if existing:
        status = existing['status']
        if status == 'pending':
            if lang == 'uz':
                await msg.answer(
                    "⏳ <b>Arizangiz ko'rib chiqilmoqda</b>\n\n"
                    f"📋 Yuborilgan sana: {existing['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
                    "Natija e'lon qilinguncha kuting yoki arizani bekor qiling.",
                    reply_markup=cancel_ariza_kb(existing['id']),
                    parse_mode='HTML'
                )
            else:
                await msg.answer(
                    "⏳ <b>Ваша заявка рассматривается</b>\n\n"
                    f"📋 Дата подачи: {existing['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
                    "Ожидайте результата или отмените заявку.",
                    reply_markup=cancel_ariza_kb(existing['id']),
                    parse_mode='HTML'
                )
            return
        elif status == 'approved':
            if lang == 'uz':
                await msg.answer("✅ Arizangiz tasdiqlangan. https://t.me/olimfondi kanalini kuzatib boring.", parse_mode='HTML')
            else:
                await msg.answer("✅ Ваша заявка уже одобрена. Следите за каналом https://t.me/olimfondi.", parse_mode='HTML')
            return
        elif status == 'rejected':
            reason = existing.get('rejection_reason') or '—'
            if lang == 'uz':
                await msg.answer(
                    f"❌ <b>Arizangiz rad etilgan</b>\n\nSabab: <i>{reason}</i>\n\nQayta ariza yubormoqchimisiz?",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton("📝 Qayta ariza yuborish", callback_data="ariza:restart")]
                    ]),
                    parse_mode='HTML'
                )
            else:
                await msg.answer(
                    f"❌ <b>Ваша заявка отклонена</b>\n\nПричина: <i>{reason}</i>\n\nХотите подать заявку снова?",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton("📝 Подать заявку снова", callback_data="ariza:restart")]
                    ]),
                    parse_mode='HTML'
                )
            return

    # Yangi ariza boshlash
    await _start_ariza_form(msg, lang)


@dp.callback_query_handler(text='ariza:restart')
async def ariza_restart(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.delete()
    user = await db.select_user(str(call.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    await _start_ariza_form(call.message, lang)


async def _start_ariza_form(msg: Message, lang: str):
    if lang == 'uz':
        await msg.answer(
            "📝 <b>2026/2027 o'quv yili uchun ariza</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👤 <b>1-bo'lim: Shaxsiy ma'lumotlar</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Familiya, Ism va Sharifingizni kiriting:\n"
            "<i>Masalan: Ernazarov Ozodbek Ilhom o'g'li</i>",
            reply_markup=cancel_reply_kb,
            parse_mode='HTML'
        )
    else:
        await msg.answer(
            "📝 <b>Заявка на 2026/2027 учебный год</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👤 <b>Раздел 1: Личные данные</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Введите вашу Фамилию, Имя и Отчество:\n"
            "<i>Например: Алишер Навоий</i>",
            reply_markup=cancel_reply_kb,
            parse_mode='HTML'
        )
    await ArizaStates.fish.set()


# ════════════════════════════════════════
#  BEKOR QILISH (forma to'xtatish)
# ════════════════════════════════════════

@dp.message_handler(Text(equals="❌ Arizani to'xtatish"), state='*')
async def cancel_form(msg: Message, state: FSMContext):
    await state.finish()
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    registered_val = user.get('registered', False) if user else False
    kb = await (build_main_kb_uz(db, registered_val) if lang == 'uz' else build_main_kb_ru(db, registered_val))
    if lang == 'uz':
        await msg.answer("❌ Ariza to'xtatildi.", reply_markup=kb)
    else:
        await msg.answer("❌ Заполнение заявки прервано.", reply_markup=kb)


@dp.callback_query_handler(text='ariza:cancel_form', state='*')
async def cancel_form_cb(call: CallbackQuery, state: FSMContext):
    await state.finish()
    await call.answer()
    user = await db.select_user(str(call.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    registered_val = user.get('registered', False) if user else False
    kb = await (build_main_kb_uz(db, registered_val) if lang == 'uz' else build_main_kb_ru(db, registered_val))
    if lang == 'uz':
        await call.message.answer("❌ Ariza bekor qilindi.", reply_markup=kb)
    else:
        await call.message.answer("❌ Заявка отменена.", reply_markup=kb)


# Foydalanuvchi yuborilgan arizani bekor qilish
@dp.callback_query_handler(lambda c: c.data and c.data.startswith("ariza_user_cancel:"))
async def user_cancel_ariza(call: CallbackQuery):
    ariza_id = int(call.data.split(":")[1])
    ariza = await db.get_ariza_by_id(ariza_id)
    if not ariza or ariza['user_id'] != str(call.from_user.id):
        await call.answer("❌ Ariza topilmadi.", show_alert=True)
        return
    if ariza['status'] != 'pending':
        await call.answer("Bu ariza allaqachon ko'rib chiqilgan.", show_alert=True)
        return
    await db.cancel_ariza(str(call.from_user.id))
    await call.answer("✅ Ariza bekor qilindi.")
    await call.message.edit_text("🗑 <b>Arizangiz bekor qilindi.</b>\n\nQayta ariza yubormoqchi bo'lsangiz, tugmani bosing.", parse_mode='HTML')


# ════════════════════════════════════════
#  SHAXSIY MA'LUMOTLAR
# ════════════════════════════════════════

@dp.message_handler(state=ArizaStates.fish)
async def get_fish(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    await state.update_data(fish=msg.text.strip())
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    if lang == 'uz':
        await msg.answer("📅 Tug'ilgan sanangizni kiriting:\n<i>Format: 01.01.2000</i>", parse_mode='HTML')
    else:
        await msg.answer("📅 Введите дату рождения:\n<i>Формат: 01.01.2000</i>", parse_mode='HTML')
    await ArizaStates.tugilgan_sana.set()


@dp.message_handler(state=ArizaStates.tugilgan_sana)
async def get_tugilgan_sana(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    await state.update_data(tugilgan_sana=msg.text.strip())
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    if lang == 'uz':
        await msg.answer("🌍 Millatingizni kiriting:\n<i>Masalan: O'zbek</i>", parse_mode='HTML')
    else:
        await msg.answer("🌍 Введите вашу национальность:\n<i>Например: Узбек</i>", parse_mode='HTML')
    await ArizaStates.millat.set()


@dp.message_handler(state=ArizaStates.millat)
async def get_millat(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    await state.update_data(millat=msg.text.strip())
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    if lang == 'uz':
        await msg.answer("📍 Doimiy ro'yxatga olingan manzilingizni kiriting:", parse_mode='HTML')
    else:
        await msg.answer("📍 Введите адрес постоянной регистрации:", parse_mode='HTML')
    await ArizaStates.manzil.set()


@dp.message_handler(state=ArizaStates.manzil)
async def get_manzil(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    await state.update_data(manzil=msg.text.strip())
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    if lang == 'uz':
        await msg.answer("📱 Telefon raqamingizni kiriting:\n<i>Format: +998901234567</i>", parse_mode='HTML')
    else:
        await msg.answer("📱 Введите номер телефона:\n<i>Формат: +998901234567</i>", parse_mode='HTML')
    await ArizaStates.telefon.set()


@dp.message_handler(state=ArizaStates.telefon)
async def get_telefon(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    phone = msg.text.strip()
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    if not PHONE_RE.match(phone):
        if lang == 'uz':
            await msg.answer("❌ Noto'g'ri format! +998901234567 shaklida kiriting.")
        else:
            await msg.answer("❌ Неверный формат! Введите в формате +998901234567.")
        return
    await state.update_data(telefon=phone)
    if lang == 'uz':
        await msg.answer("📧 Email manzilingizni kiriting:")
    else:
        await msg.answer("📧 Введите ваш email:")
    await ArizaStates.email.set()


@dp.message_handler(state=ArizaStates.email)
async def get_email(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    await state.update_data(email=msg.text.strip())
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    if lang == 'uz':
        await msg.answer(
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🎓 <b>2-bo'lim: Ta'lim haqida ma'lumot</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Qaysi oliy ta'lim muassasasida o'qiyapsiz?",
            parse_mode='HTML'
        )
    else:
        await msg.answer(
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🎓 <b>Раздел 2: Сведения об образовании</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "В каком высшем учебном заведении вы учитесь?",
            parse_mode='HTML'
        )
    await ArizaStates.otm.set()


# ════════════════════════════════════════
#  TA'LIM
# ════════════════════════════════════════

@dp.message_handler(state=ArizaStates.otm)
async def get_otm(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    await state.update_data(otm=msg.text.strip())
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    if lang == 'uz':
        await msg.answer("📋 Ta'lim shaklini tanlang:", reply_markup=talim_shakli_kb())
    else:
        await msg.answer("📋 Выберите форму обучения:", reply_markup=talim_shakli_kb())
    await ArizaStates.talim_shakli.set()


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("ts:"), state=ArizaStates.talim_shakli)
async def get_talim_shakli(call: CallbackQuery, state: FSMContext):
    shakl_map = {"ts:kunduzgi": "Kunduzgi", "ts:sirtqi": "Sirtqi", "ts:masofaviy": "Masofaviy"}
    shakl = shakl_map.get(call.data, "Kunduzgi")
    await state.update_data(talim_shakli=shakl)
    await call.answer()
    await call.message.delete()
    user = await db.select_user(str(call.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    if lang == 'uz':
        await call.message.answer("📚 Ta'lim yo'nalishingizni (mutaxassislik) kiriting:")
    else:
        await call.message.answer("📚 Введите направление обучения (специальность):")
    await ArizaStates.yonalish.set()


@dp.message_handler(state=ArizaStates.yonalish)
async def get_yonalish(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    await state.update_data(yonalish=msg.text.strip())
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    if lang == 'uz':
        await msg.answer("📖 2026/2027 o'quv yilidagi kursingizni tanlang:", reply_markup=kurs_kb())
    else:
        await msg.answer("📖 Выберите ваш курс в 2026/2027 учебном году:", reply_markup=kurs_kb())
    await ArizaStates.kurs.set()


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("kurs:"), state=ArizaStates.kurs)
async def get_kurs(call: CallbackQuery, state: FSMContext):
    kurs = call.data.split(":")[1]
    await state.update_data(kurs=kurs)
    await call.answer()
    await call.message.delete()
    user = await db.select_user(str(call.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    if lang == 'uz':
        await call.message.answer("🔬 Ilmiy tadqiqotlar bilan shug'ullanasizmi?", reply_markup=ha_yoq_kb("itadq"))
    else:
        await call.message.answer("🔬 Занимаетесь ли вы научными исследованиями?", reply_markup=ha_yoq_kb("itadq"))
    await ArizaStates.ilmiy_tadqiqot.set()


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("itadq:"), state=ArizaStates.ilmiy_tadqiqot)
async def get_ilmiy_tadqiqot(call: CallbackQuery, state: FSMContext):
    val = call.data.split(":")[1] == 'ha'
    await state.update_data(ilmiy_tadqiqot=val)
    await call.answer()
    await call.message.delete()
    user = await db.select_user(str(call.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    if val:
        if lang == 'uz':
            await call.message.answer("📝 Tadqiqot yo'nalishi haqida qisqacha ma'lumot bering:")
        else:
            await call.message.answer("📝 Кратко опишите направление исследования:")
        await ArizaStates.tadqiqot_info.set()
    else:
        await state.update_data(tadqiqot_info='')
        await _ask_konferensiya(call.message, lang)
        await ArizaStates.konferensiya.set()


@dp.message_handler(state=ArizaStates.tadqiqot_info)
async def get_tadqiqot_info(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    await state.update_data(tadqiqot_info=msg.text.strip())
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    await _ask_konferensiya(msg, lang)
    await ArizaStates.konferensiya.set()


async def _ask_konferensiya(target, lang):
    if lang == 'uz':
        await target.answer("🎤 Ilmiy konferensiya, seminar yoki tanlovlarda ishtirok etganmisiz?", reply_markup=ha_yoq_kb("konf"))
    else:
        await target.answer("🎤 Участвовали ли вы в научных конференциях, семинарах или конкурсах?", reply_markup=ha_yoq_kb("konf"))


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("konf:"), state=ArizaStates.konferensiya)
async def get_konferensiya(call: CallbackQuery, state: FSMContext):
    val = call.data.split(":")[1] == 'ha'
    await state.update_data(konferensiya=val)
    await call.answer()
    await call.message.delete()
    user = await db.select_user(str(call.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    if lang == 'uz':
        await call.message.answer("📰 Sizda ilmiy maqola yoki nashrlar bormi?", reply_markup=ha_yoq_kb("maqola"))
    else:
        await call.message.answer("📰 Есть ли у вас научные статьи или публикации?", reply_markup=ha_yoq_kb("maqola"))
    await ArizaStates.maqola.set()


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("maqola:"), state=ArizaStates.maqola)
async def get_maqola(call: CallbackQuery, state: FSMContext):
    val = call.data.split(":")[1] == 'ha'
    await state.update_data(maqola=val)
    await call.answer()
    await call.message.delete()
    user = await db.select_user(str(call.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    if lang == 'uz':
        await call.message.answer(
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💰 <b>3-bo'lim: Moliya va qo'llab-quvvatlash</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Oldin Olim fondidan yoki boshqa grantlardan foydalanganmisiz?",
            reply_markup=ha_yoq_kb("grant"),
            parse_mode='HTML'
        )
    else:
        await call.message.answer(
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💰 <b>Раздел 3: Финансы и поддержка</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Пользовались ли вы ранее грантами Олим фонда или других организаций?",
            reply_markup=ha_yoq_kb("grant"),
            parse_mode='HTML'
        )
    await ArizaStates.oldin_grant.set()


# ════════════════════════════════════════
#  MOLIYA
# ════════════════════════════════════════

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("grant:"), state=ArizaStates.oldin_grant)
async def get_oldin_grant(call: CallbackQuery, state: FSMContext):
    val = call.data.split(":")[1] == 'ha'
    await state.update_data(oldin_grant=val)
    await call.answer()
    await call.message.delete()
    user = await db.select_user(str(call.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    if val:
        if lang == 'uz':
            await call.message.answer("📋 Qaysi grant va qachon? Qisqacha yozing:")
        else:
            await call.message.answer("📋 Какой грант и когда? Напишите кратко:")
        await ArizaStates.grant_info.set()
    else:
        await state.update_data(grant_info='')
        await _ask_kontrakt_sum(call.message, lang)
        await ArizaStates.kontrakt_sum.set()


@dp.message_handler(state=ArizaStates.grant_info)
async def get_grant_info(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    await state.update_data(grant_info=msg.text.strip())
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    await _ask_kontrakt_sum(msg, lang)
    await ArizaStates.kontrakt_sum.set()


async def _ask_kontrakt_sum(target, lang):
    if lang == 'uz':
        await target.answer("💵 Kontrakt sumangiz qancha? (stipendiyasiz hisoblanganda):")
    else:
        await target.answer("💵 Какова сумма вашего контракта? (без учёта стипендии):")


@dp.message_handler(state=ArizaStates.kontrakt_sum)
async def get_kontrakt_sum(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    await state.update_data(kontrakt_sum=msg.text.strip())
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    if lang == 'uz':
        await msg.answer(
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👨‍👩‍👧‍👦 <b>4-bo'lim: Oila a'zolari haqida ma'lumot</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Oilangiz necha kishidan iborat?",
            parse_mode='HTML'
        )
    else:
        await msg.answer(
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👨‍👩‍👧‍👦 <b>Раздел 4: Сведения о членах семьи</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Из скольких человек состоит ваша семья?",
            parse_mode='HTML'
        )
    await ArizaStates.oila_soni.set()


# ════════════════════════════════════════
#  OILA
# ════════════════════════════════════════

@dp.message_handler(state=ArizaStates.oila_soni)
async def get_oila_soni(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    await state.update_data(oila_soni=msg.text.strip())
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    if lang == 'uz':
        await msg.answer(
            "👨 Otangiz haqida ma'lumot kiriting:\n"
            "<i>F.I.Sh. | Ish joyi | Lavozimi | Tug'ilgan sana</i>",
            parse_mode='HTML'
        )
    else:
        await msg.answer(
            "👨 Введите сведения об отце:\n"
            "<i>Ф.И.О. | Место работы | Должность | Дата рождения</i>",
            parse_mode='HTML'
        )
    await ArizaStates.ota_info.set()


@dp.message_handler(state=ArizaStates.ota_info)
async def get_ota_info(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    await state.update_data(ota_info=msg.text.strip())
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    if lang == 'uz':
        await msg.answer(
            "👩 Onangiz haqida ma'lumot kiriting:\n"
            "<i>F.I.Sh. | Ish joyi | Lavozimi | Tug'ilgan sana</i>",
            parse_mode='HTML'
        )
    else:
        await msg.answer(
            "👩 Введите сведения о матери:\n"
            "<i>Ф.И.О. | Место работы | Должность | Дата рождения</i>",
            parse_mode='HTML'
        )
    await ArizaStates.ona_info.set()


@dp.message_handler(state=ArizaStates.ona_info)
async def get_ona_info(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    await state.update_data(ona_info=msg.text.strip())
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    if lang == 'uz':
        await msg.answer(
            "👫 Aka/uka/opa/singillaringiz haqida ma'lumot kiriting:\n"
            "<i>F.I.Sh. | Ishlash/o'qish joyi | Lavozimi/kursi | Shakli | Shartnoma turi | Tug'ilgan sana</i>\n\n"
            "Yo'q bo'lsa: <b>Yo'q</b> deb yozing.",
            parse_mode='HTML'
        )
    else:
        await msg.answer(
            "👫 Введите сведения о братьях/сёстрах:\n"
            "<i>Ф.И.О. | Место работы/учёбы | Должность/курс | Форма | Тип договора | Дата рождения</i>\n\n"
            "Если нет — напишите: <b>Нет</b>",
            parse_mode='HTML'
        )
    await ArizaStates.aka_opa_info.set()


ariza_step_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("⬅️ Ortga"), KeyboardButton("❌ Arizani to'xtatish")]
    ],
    resize_keyboard=True
)


async def _ask_transkript(target, lang):
    if lang == 'uz':
        await target.answer(
            "🎓 <b>Transkript</b>\n\n"
            "Iltimos, transkriptingizni rasm yoki fayl (PDF/Word/etc.) ko'rinishida yuboring:",
            reply_markup=ariza_step_kb,
            parse_mode='HTML'
        )
    else:
        await target.answer(
            "🎓 <b>Транскрипт</b>\n\n"
            "Пожалуйста, отправьте ваш транскрипт в виде фото или файла (PDF/Word/и др.):",
            reply_markup=ariza_step_kb,
            parse_mode='HTML'
        )


async def _ask_passport_oldi(target, lang):
    if lang == 'uz':
        await target.answer(
            "🪪 <b>Pasport (Oldi tomoni)</b>\n\n"
            "Iltimos, pasportingizning oldi tomonini (rasmli qismi) rasm yoki fayl ko'rinishida yuboring:",
            reply_markup=ariza_step_kb,
            parse_mode='HTML'
        )
    else:
        await target.answer(
            "🪪 <b>Паспорт (Лицевая сторона)</b>\n\n"
            "Пожалуйста, отправьте лицевую сторону вашего паспорта (с фотографией) в виде фото или файла:",
            reply_markup=ariza_step_kb,
            parse_mode='HTML'
        )


async def _ask_passport_orqa(target, lang):
    if lang == 'uz':
        await target.answer(
            "🪪 <b>Pasport (Orqa tomoni)</b>\n\n"
            "Iltimos, pasportingizning orqa tomonini (manzil ro'yxati yoki ID karta orqasi) rasm yoki fayl ko'rinishida yuboring:",
            reply_markup=ariza_step_kb,
            parse_mode='HTML'
        )
    else:
        await target.answer(
            "🪪 <b>Паспорт (Обратная сторона)</b>\n\n"
            "Пожалуйста, отправьте обратную сторону вашего паспорта (регистрация или обратная сторона ID-карты) в виде фото или файла:",
            reply_markup=ariza_step_kb,
            parse_mode='HTML'
        )


async def _ask_cv(target, lang):
    if lang == 'uz':
        await target.answer(
            "📄 <b>CV / Rezyume</b>\n\n"
            "Iltimos, CV yoki Rezyumeingizni fayl yoki rasm ko'rinishida yuboring:",
            reply_markup=ariza_step_kb,
            parse_mode='HTML'
        )
    else:
        await target.answer(
            "📄 <b>CV / Резюме</b>\n\n"
            "Пожалуйста, отправьте ваше CV или резюме в виде файла или фото:",
            reply_markup=ariza_step_kb,
            parse_mode='HTML'
        )


def get_imtiyoz_kb(lang):
    no_text = "Yo'q" if lang == 'uz' else "Нет"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("⬅️ Ortga"), KeyboardButton(no_text)],
            [KeyboardButton("❌ Arizani to'xtatish")]
        ],
        resize_keyboard=True
    )


async def _ask_imtiyozi(target, lang):
    if lang == 'uz':
        await target.answer(
            "🏅 <b>Imtiyozingiz bormi?</b>\n\n"
            "Agar sizda imtiyoz bo'lsa (ijtimoiy himoya, chin yetim va h.k.), tegishli tasdiqlovchi hujjatni (rasm yoki fayl ko'rinishida) yuklang.\n"
            "Hujjatni <a href=\"https://my.gov.uz/\">my.gov.uz</a> portali orqali yuklab olishingiz mumkin.\n\n"
            "Agar imtiyozingiz bo'lmasa, quyidagi tugmani bosing yoki <b>Yo'q</b> deb yozing:",
            reply_markup=get_imtiyoz_kb('uz'),
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    else:
        await target.answer(
            "🏅 <b>Есть ли у вас льготы?</b>\n\n"
            "Если у вас есть льготы (социальная защита, статус сироты и т.д.), загрузите подтверждающий документ (в виде фото или файла).\n"
            "Вы можете скачать документ через портал <a href=\"https://my.gov.uz/\">my.gov.uz</a>.\n\n"
            "Если у вас нет льгот, нажмите на кнопку ниже или напишите <b>Нет</b>:",
            reply_markup=get_imtiyoz_kb('ru'),
            parse_mode='HTML',
            disable_web_page_preview=True
        )


async def _ask_oqish_joyi(target, lang):
    if lang == 'uz':
        await target.answer(
            "🏫 <b>O'qish joyidan ma'lumotnoma</b>\n\n"
            "Iltimos, o'qish joyingizdan ma'lumotnomani rasm yoki fayl (PDF/Word/etc.) ko'rinishida yuboring.\n"
            "Ma'lumotnomani <a href=\"https://my.gov.uz/\">my.gov.uz</a> portali orqali yuklab olishingiz mumkin:",
            reply_markup=ariza_step_kb,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    else:
        await target.answer(
            "🏫 <b>Справка с места учёбы</b>\n\n"
            "Пожалуйста, отправьте справку с места вашей учёбы в виде фото или файла (PDF/Word/и др.).\n"
            "Вы можете скачать справку через портал <a href=\"https://my.gov.uz/\">my.gov.uz</a>:",
            reply_markup=ariza_step_kb,
            parse_mode='HTML',
            disable_web_page_preview=True
        )


@dp.message_handler(state=ArizaStates.aka_opa_info)
async def get_aka_opa_info(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    await state.update_data(aka_opa_info=msg.text.strip())
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
    await _ask_transkript(msg, lang)
    await ArizaStates.transkript.set()


# ─── TRANSKRIPT ───
@dp.message_handler(state=ArizaStates.transkript, content_types=["photo", "document", "text"])
async def get_transkript(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'

    if msg.text == "⬅️ Ortga":
        if lang == 'uz':
            await msg.answer(
                "👫 Aka/uka/opa/singillaringiz haqida ma'lumot kiriting:\n"
                "<i>F.I.Sh. | Ishlash/o'qish joyi | Lavozimi/kursi | Shakli | Shartnoma turi | Tug'ilgan sana</i>\n\n"
                "Yo'q bo'lsa: <b>Yo'q</b> deb yozing.",
                reply_markup=cancel_reply_kb,
                parse_mode='HTML'
            )
        else:
            await msg.answer(
                "👫 Введите сведения о братьях/сёстрах:\n"
                "<i>Ф.И.О. | Место работы/учёбы | Должность/курс | Форма | Тип договора | Дата рождения</i>\n\n"
                "Если нет — напишите: <b>Нет</b>",
                reply_markup=cancel_reply_kb,
                parse_mode='HTML'
            )
        await ArizaStates.aka_opa_info.set()
        return

    file_id = None
    file_type = None
    if msg.photo:
        file_id = msg.photo[-1].file_id
        file_type = 'photo'
    elif msg.document:
        file_id = msg.document.file_id
        file_type = 'document'

    if not file_id:
        if lang == 'uz':
            await msg.answer("❌ Iltimos, transkriptingizni rasm yoki fayl shaklida yuboring!")
        else:
            await msg.answer("❌ Пожалуйста, отправьте ваш транскрипт в виде фото или файла!")
        return

    await state.update_data(transkript_file_id=file_id, transkript_file_type=file_type)
    await _ask_passport_oldi(msg, lang)
    await ArizaStates.passport_oldi.set()


# ─── PASSPORT OLDI ───
@dp.message_handler(state=ArizaStates.passport_oldi, content_types=["photo", "document", "text"])
async def get_passport_oldi(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'

    if msg.text == "⬅️ Ortga":
        await _ask_transkript(msg, lang)
        await ArizaStates.transkript.set()
        return

    file_id = None
    file_type = None
    if msg.photo:
        file_id = msg.photo[-1].file_id
        file_type = 'photo'
    elif msg.document:
        file_id = msg.document.file_id
        file_type = 'document'

    if not file_id:
        if lang == 'uz':
            await msg.answer("❌ Iltimos, pasportingizning oldi tomonini rasm yoki fayl shaklida yuboring!")
        else:
            await msg.answer("❌ Пожалуйста, отправьте лицевую сторону вашего паспорта в виде фото или файла!")
        return

    await state.update_data(passport_oldi_file_id=file_id, passport_oldi_file_type=file_type)
    await _ask_passport_orqa(msg, lang)
    await ArizaStates.passport_orqa.set()


# ─── PASSPORT ORQA ───
@dp.message_handler(state=ArizaStates.passport_orqa, content_types=["photo", "document", "text"])
async def get_passport_orqa(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'

    if msg.text == "⬅️ Ortga":
        await _ask_passport_oldi(msg, lang)
        await ArizaStates.passport_oldi.set()
        return

    file_id = None
    file_type = None
    if msg.photo:
        file_id = msg.photo[-1].file_id
        file_type = 'photo'
    elif msg.document:
        file_id = msg.document.file_id
        file_type = 'document'

    if not file_id:
        if lang == 'uz':
            await msg.answer("❌ Iltimos, pasportingizning orqa tomonini rasm yoki fayl shaklida yuboring!")
        else:
            await msg.answer("❌ Пожалуйста, отправьте обратную сторону вашего паспорта в виде фото или файла!")
        return

    await state.update_data(passport_orqa_file_id=file_id, passport_orqa_file_type=file_type)
    await _ask_cv(msg, lang)
    await ArizaStates.cv.set()


# ─── CV / REZYUME ───
@dp.message_handler(state=ArizaStates.cv, content_types=["photo", "document", "text"])
async def get_cv(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'

    if msg.text == "⬅️ Ortga":
        await _ask_passport_orqa(msg, lang)
        await ArizaStates.passport_orqa.set()
        return

    file_id = None
    file_type = None
    if msg.photo:
        file_id = msg.photo[-1].file_id
        file_type = 'photo'
    elif msg.document:
        file_id = msg.document.file_id
        file_type = 'document'

    if not file_id:
        if lang == 'uz':
            await msg.answer("❌ Iltimos, CV yoki Rezyumeingizni fayl yoki rasm shaklida yuboring!")
        else:
            await msg.answer("❌ Пожалуйста, отправьте ваше CV или резюме в виде файла или фото!")
        return

    await state.update_data(cv_file_id=file_id, cv_file_type=file_type)
    await _ask_imtiyozi(msg, lang)
    await ArizaStates.imtiyozi.set()


# ─── IMTIYOZ ───
@dp.message_handler(state=ArizaStates.imtiyozi, content_types=["photo", "document", "text"])
async def get_imtiyozi(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'

    if msg.text == "⬅️ Ortga":
        await _ask_cv(msg, lang)
        await ArizaStates.cv.set()
        return

    # Check if they skipped/have no privileges
    if msg.text and msg.text.strip().lower() in ["yo'q", "yoq", "нет", "net", "no", "skip"]:
        await state.update_data(imtiyozi=None, imtiyozi_file_type=None)
        await _ask_oqish_joyi(msg, lang)
        await ArizaStates.oqish_joyi.set()
        return

    file_id = None
    file_type = None
    if msg.photo:
        file_id = msg.photo[-1].file_id
        file_type = 'photo'
    elif msg.document:
        file_id = msg.document.file_id
        file_type = 'document'

    if not file_id:
        if lang == 'uz':
            await msg.answer("❌ Iltimos, imtiyozingizni tasdiqlovchi hujjatni (rasm yoki fayl shaklida) yuboring yoki «Yo'q» tugmasini bosing!")
        else:
            await msg.answer("❌ Пожалуйста, отправьте документ, подтверждающий льготу (в виде фото или файла), или нажмите кнопку «Нет»!")
        return

    await state.update_data(imtiyozi=file_id, imtiyozi_file_type=file_type)
    await _ask_oqish_joyi(msg, lang)
    await ArizaStates.oqish_joyi.set()


# ─── OQISH JOYIDAN MA'LUMOTNOMA ───
@dp.message_handler(state=ArizaStates.oqish_joyi, content_types=["photo", "document", "text"])
async def get_oqish_joyi(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'

    if msg.text == "⬅️ Ortga":
        await _ask_imtiyozi(msg, lang)
        await ArizaStates.imtiyozi.set()
        return

    file_id = None
    file_type = None
    if msg.photo:
        file_id = msg.photo[-1].file_id
        file_type = 'photo'
    elif msg.document:
        file_id = msg.document.file_id
        file_type = 'document'

    if not file_id:
        if lang == 'uz':
            await msg.answer("❌ Iltimos, o'qish joyidan ma'lumotnomani rasm yoki fayl shaklida yuboring!")
        else:
            await msg.answer("❌ Пожалуйста, отправьте справку с места учёбы в виде фото или файла!")
        return

    await state.update_data(oqish_joyi_file_id=file_id, oqish_joyi_file_type=file_type)

    if lang == 'uz':
        await msg.answer(
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📝 <b>5-bo'lim: Motivatsion xat</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Quyidagi savollarga javob berib, motivatsion xat yozing:\n\n"
            "• Yaqin kelajak uchun belgilgan rejalaringiz\n"
            "• Oliy ma'lumot sizga, oilangizga va jamiyatga qanday yordam ko'rsatadi?\n"
            "• Fond sizning maqsadlaringizga qanday yordam ko'rsatadi?\n"
            "• O'zingizni haqiqatan munosibman deb o'ylaysizmi?\n"
            "• Nima uchun aynan siz stipendiya g'olibi bo'lishingiz kerak?\n\n"
            "<i>Barcha savollarga javob berib, bir xabarda yozing.</i>",
            reply_markup=ariza_step_kb,
            parse_mode='HTML'
        )
    else:
        await msg.answer(
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📝 <b>Раздел 5: Мотивационное письмо</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Напишите мотивационное письмо, ответив на следующие вопросы:\n\n"
            "• Ваши планы на ближайшее будущее\n"
            "• Как высшее образование поможет вам, семье и обществу?\n"
            "• Как фонд поможет достижению ваших целей?\n"
            "• Считаете ли вы себя достойным кандидатом?\n"
            "• Почему именно вы должны стать стипендиатом?\n\n"
            "<i>Ответьте на все вопросы в одном сообщении.</i>",
            reply_markup=ariza_step_kb,
            parse_mode='HTML'
        )
    await ArizaStates.motivatsion_xat.set()


# ════════════════════════════════════════
#  MOTIVATSION XAT → TASDIQLASH
# ════════════════════════════════════════

@dp.message_handler(state=ArizaStates.motivatsion_xat)
async def get_motivatsion_xat(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'

    if msg.text == "⬅️ Ortga":
        await _ask_oqish_joyi(msg, lang)
        await ArizaStates.oqish_joyi.set()
        return

    await state.update_data(motivatsion_xat=msg.text.strip())
    data = await state.get_data()
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'

    # ─── Word hujjat hosil qilish ───
    try:
        buf = generate_ariza_docx(data)
        fish = data.get('fish', 'ariza')
        filename = f"ariza_{fish.split()[0] if fish else 'nomzod'}.docx"

        if lang == 'uz':
            caption = (
                "📄 <b>Arizangiz tayyor!</b>\n\n"
                "Yuqoridagi hujjatni ko'rib chiqing.\n"
                "Hammasi to'g'rimi? Tasdiqlang yoki bekor qiling."
            )
        else:
            caption = (
                "📄 <b>Ваша заявка готова!</b>\n\n"
                "Ознакомьтесь с документом выше.\n"
                "Всё верно? Подтвердите или отмените."
            )

        await msg.answer_document(
            document=InputFile(buf, filename=filename),
            caption=caption,
            reply_markup=ariza_confirm_kb(),
            parse_mode='HTML'
        )
    except Exception as e:
        # Agar python-docx o'rnatilmagan bo'lsa — matnli tasdiqlash
        if lang == 'uz':
            await msg.answer(
                "📋 <b>Arizangizni tasdiqlaysizmi?</b>\n\n"
                f"👤 {data.get('fish')}\n"
                f"🏛 {data.get('otm')}\n"
                f"📚 {data.get('yonalish')} — {data.get('kurs')}",
                reply_markup=ariza_confirm_kb(), parse_mode='HTML'
            )
        else:
            await msg.answer(
                "📋 <b>Подтвердить отправку?</b>\n\n"
                f"👤 {data.get('fish')}\n"
                f"🏛 {data.get('otm')}\n"
                f"📚 {data.get('yonalish')} — {data.get('kurs')}",
                reply_markup=ariza_confirm_kb(), parse_mode='HTML'
            )

    await ArizaStates.confirm.set()


# ════════════════════════════════════════
#  YUBORISH
# ════════════════════════════════════════

async def upload_to_storage_channel(file_id: str, file_type: str, caption: str) -> str:
    """Uploads file to storage channel and returns the file_id from the channel's sent message"""
    try:
        if file_type == 'photo':
            sent_msg = await bot.send_photo(STORAGE_CHANNEL, photo=file_id, caption=caption)
            return sent_msg.photo[-1].file_id
        else:
            sent_msg = await bot.send_document(STORAGE_CHANNEL, document=file_id, caption=caption)
            return sent_msg.document.file_id
    except Exception as e:
        print(f"[Storage Channel Upload Error] {e}")
        return file_id


@dp.callback_query_handler(text='ariza:yuborish', state=ArizaStates.confirm)
async def ariza_yuborish(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.finish()
    await call.answer()

    user_id = str(call.from_user.id)
    user = await db.select_user(user_id)
    lang = user.get('language', 'uz') if user else 'uz'

    # Upload files to STORAGE_CHANNEL and get stored file_ids
    fish = data.get('fish', 'nomzod')
    transkript_stored_id = await upload_to_storage_channel(
        data['transkript_file_id'], data['transkript_file_type'],
        f"🎓 Transkript | 👤 {fish} (ID: {user_id})"
    )
    passport_oldi_stored_id = await upload_to_storage_channel(
        data['passport_oldi_file_id'], data['passport_oldi_file_type'],
        f"🪪 Pasport (Oldi) | 👤 {fish} (ID: {user_id})"
    )
    passport_orqa_stored_id = await upload_to_storage_channel(
        data['passport_orqa_file_id'], data['passport_orqa_file_type'],
        f"🪪 Pasport (Orqa) | 👤 {fish} (ID: {user_id})"
    )
    cv_stored_id = await upload_to_storage_channel(
        data['cv_file_id'], data['cv_file_type'],
        f"📄 CV/Rezyume | 👤 {fish} (ID: {user_id})"
    )

    imtiyozi_stored_id = None
    if data.get('imtiyozi'):
        imtiyozi_stored_id = await upload_to_storage_channel(
            data['imtiyozi'], data['imtiyozi_file_type'],
            f"🏅 Imtiyoz hujjati | 👤 {fish} (ID: {user_id})"
        )

    oqish_joyi_stored_id = await upload_to_storage_channel(
        data['oqish_joyi_file_id'], data['oqish_joyi_file_type'],
        f"🏫 O'qish joyidan ma'lumotnoma | 👤 {fish} (ID: {user_id})"
    )

    data['transkript_file_id'] = transkript_stored_id
    data['passport_oldi_file_id'] = passport_oldi_stored_id
    data['passport_orqa_file_id'] = passport_orqa_stored_id
    data['cv_file_id'] = cv_stored_id
    data['imtiyozi'] = imtiyozi_stored_id
    data['oqish_joyi_file_id'] = oqish_joyi_stored_id

    tz = pytz.timezone("Asia/Tashkent")
    now = datetime.now(tz).replace(tzinfo=None)

    ariza = await db.add_ariza(user_id=user_id, data=data, created_at=now)

    kb = await (build_main_kb_uz(db) if lang == 'uz' else build_main_kb_ru(db))

    if lang == 'uz':
        await call.message.answer(
            "✅ <b>Arizangiz muvaffaqiyatli yuborildi!</b>\n\n"
            "Tez orada ko'rib chiqiladi. Natija haqida xabar olasiz.",
            reply_markup=kb, parse_mode='HTML'
        )
    else:
        await call.message.answer(
            "✅ <b>Ваша заявка успешно отправлена!</b>\n\n"
            "Она будет рассмотрена в ближайшее время. Вы получите уведомление о результате.",
            reply_markup=kb, parse_mode='HTML'
        )

    # Admin xabarnomasi
    def bool_str(v): return "Ha ✅" if v else "Yo'q ❌"

    admin_text = (
        f"📋 <b>YANGI ARIZA #{ariza['id']}</b>\n\n"
        f"👤 F.I.SH: <b>{data['fish']}</b>\n"
        f"📅 Tug'ilgan sana: {data['tugilgan_sana']}\n"
        f"🌍 Millat: {data['millat']}\n"
        f"📍 Manzil: {data['manzil']}\n"
        f"📱 Telefon: {data['telefon']}\n"
        f"📧 Email: {data['email']}\n\n"
        f"🎓 <b>Ta'lim:</b>\n"
        f"• OTM: {data['otm']}\n"
        f"• Shakl: {data['talim_shakli']}\n"
        f"• Yo'nalish: {data['yonalish']}\n"
        f"• Kurs: {data['kurs']}\n"
        f"• Ilmiy tadqiqot: {bool_str(data.get('ilmiy_tadqiqot'))}\n"
    )
    if data.get('tadqiqot_info'):
        admin_text += f"  ↳ {data['tadqiqot_info']}\n"
    admin_text += (
        f"• Konferensiya: {bool_str(data.get('konferensiya'))}\n"
        f"• Maqolalar: {bool_str(data.get('maqola'))}\n\n"
        f"💰 <b>Moliya va Imtiyozlar:</b>\n"
        f"• Oldin grant: {bool_str(data.get('oldin_grant'))}\n"
    )
    if data.get('grant_info'):
        admin_text += f"  ↳ {data['grant_info']}\n"

    imtiyozi_status_user = "Yuklangan ✅" if data.get('imtiyozi') else "Yo'q ❌"

    admin_text += (
        f"• Kontrakt summa: {data['kontrakt_sum']}\n"
        f"• Imtiyozi: {imtiyozi_status_user}\n"
        f"• O'qish joyidan ma'lumotnoma: Yuklangan ✅\n\n"
        f"👨‍👩‍👧‍👦 <b>Oila:</b>\n"
        f"• Soni: {data['oila_soni']}\n"
        f"• Ota: {data['ota_info']}\n"
        f"• Ona: {data['ona_info']}\n"
        f"• Aka/opa/singil: {data['aka_opa_info']}\n\n"
        f"📱 Telegram: {call.from_user.mention} (ID: <code>{user_id}</code>)"
    )

    ariza_action_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"ariza_ok:{ariza['id']}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"ariza_rad:{ariza['id']}")
        ]
    ])

    # Word hujjat tayyorlash
    docx_filename = f"ariza_{fish.split()[0]}_{ariza['id']}.docx"
    try:
        docx_buf = generate_ariza_docx(data)
    except Exception:
        docx_buf = None

    admin_msgs = []  # har bir adminga yuborilgan asosiy xabarning chat_id + msg_id
    for admin_id in ADMINS:
        try:
            # Send Transcript
            if data.get('transkript_file_type') == 'photo':
                await bot.send_photo(admin_id, photo=transkript_stored_id, caption=f"🎓 <b>Transkript</b> (#{ariza['id']}) — {fish}", parse_mode='HTML')
            else:
                await bot.send_document(admin_id, document=transkript_stored_id, caption=f"🎓 <b>Transkript</b> (#{ariza['id']}) — {fish}", parse_mode='HTML')

            # Send Passport Front
            if data.get('passport_oldi_file_type') == 'photo':
                await bot.send_photo(admin_id, photo=passport_oldi_stored_id, caption=f"🪪 <b>Pasport (Oldi tomoni)</b> (#{ariza['id']}) — {fish}", parse_mode='HTML')
            else:
                await bot.send_document(admin_id, document=passport_oldi_stored_id, caption=f"🪪 <b>Pasport (Oldi tomoni)</b> (#{ariza['id']}) — {fish}", parse_mode='HTML')

            # Send Passport Back
            if data.get('passport_orqa_file_type') == 'photo':
                await bot.send_photo(admin_id, photo=passport_orqa_stored_id, caption=f"🪪 <b>Pasport (Orqa tomoni)</b> (#{ariza['id']}) — {fish}", parse_mode='HTML')
            else:
                await bot.send_document(admin_id, document=passport_orqa_stored_id, caption=f"🪪 <b>Pasport (Orqa tomoni)</b> (#{ariza['id']}) — {fish}", parse_mode='HTML')

            # Send CV
            if data.get('cv_file_type') == 'photo':
                await bot.send_photo(admin_id, photo=cv_stored_id, caption=f"📄 <b>CV / Rezyume</b> (#{ariza['id']}) — {fish}", parse_mode='HTML')
            else:
                await bot.send_document(admin_id, document=cv_stored_id, caption=f"📄 <b>CV / Rezyume</b> (#{ariza['id']}) — {fish}", parse_mode='HTML')

            # Send Privilege file (if exists)
            if imtiyozi_stored_id:
                if data.get('imtiyozi_file_type') == 'photo':
                    await bot.send_photo(admin_id, photo=imtiyozi_stored_id, caption=f"🏅 <b>Imtiyoz hujjati</b> (#{ariza['id']}) — {fish}", parse_mode='HTML')
                else:
                    await bot.send_document(admin_id, document=imtiyozi_stored_id, caption=f"🏅 <b>Imtiyoz hujjati</b> (#{ariza['id']}) — {fish}", parse_mode='HTML')

            # Send Study Certificate
            if data.get('oqish_joyi_file_type') == 'photo':
                await bot.send_photo(admin_id, photo=oqish_joyi_stored_id, caption=f"🏫 <b>O'qish joyidan ma'lumotnoma</b> (#{ariza['id']}) — {fish}", parse_mode='HTML')
            else:
                await bot.send_document(admin_id, document=oqish_joyi_stored_id, caption=f"🏫 <b>O'qish joyidan ma'lumotnoma</b> (#{ariza['id']}) — {fish}", parse_mode='HTML')

            # Send text and action buttons
            sent = await bot.send_message(admin_id, admin_text, parse_mode='HTML', reply_markup=ariza_action_kb)
            admin_msgs.append({"chat_id": str(admin_id), "msg_id": sent.message_id})

            # Send Word doc
            if docx_buf:
                docx_buf.seek(0)
                await bot.send_document(
                    admin_id,
                    InputFile(docx_buf, filename=docx_filename),
                    caption=f"📄 Rasmiy ariza hujjati — {fish}"
                )
            else:
                motivatsion_text = f"📝 <b>Motivatsion xat (#{ariza['id']}):</b>\n\n{data['motivatsion_xat']}"
                await bot.send_message(admin_id, motivatsion_text, parse_mode='HTML')
        except Exception as ex:
            print(f"[Admin Send Error] {ex}")

    if admin_msgs:
        await db.save_ariza_admin_msgs(ariza['id'], admin_msgs)
