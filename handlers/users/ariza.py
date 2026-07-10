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

from data.config import ADMINS
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
                await msg.answer("✅ <b>Tabriklaymiz!</b> Arizangiz tasdiqlangan. Hujjat yuborish bo'limidan foydalanishingiz mumkin.", parse_mode='HTML')
            else:
                await msg.answer("✅ <b>Поздравляем!</b> Ваша заявка одобрена. Вы можете пользоваться разделом отправки документов.", parse_mode='HTML')
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
    kb = await (build_main_kb_uz(db) if lang == 'uz' else build_main_kb_ru(db))
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
    kb = await (build_main_kb_uz(db) if lang == 'uz' else build_main_kb_ru(db))
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


@dp.message_handler(state=ArizaStates.aka_opa_info)
async def get_aka_opa_info(msg: Message, state: FSMContext):
    if msg.text == "❌ Arizani to'xtatish":
        return
    await state.update_data(aka_opa_info=msg.text.strip())
    user = await db.select_user(str(msg.from_user.id))
    lang = user.get('language', 'uz') if user else 'uz'
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

@dp.callback_query_handler(text='ariza:yuborish', state=ArizaStates.confirm)
async def ariza_yuborish(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.finish()
    await call.answer()

    user_id = str(call.from_user.id)
    user = await db.select_user(user_id)
    lang = user.get('language', 'uz') if user else 'uz'

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
        f"💰 <b>Moliya:</b>\n"
        f"• Oldin grant: {bool_str(data.get('oldin_grant'))}\n"
    )
    if data.get('grant_info'):
        admin_text += f"  ↳ {data['grant_info']}\n"
    admin_text += (
        f"• Kontrakt summa: {data['kontrakt_sum']}\n\n"
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
    fish = data.get('fish', 'nomzod')
    docx_filename = f"ariza_{fish.split()[0]}_{ariza['id']}.docx"
    try:
        docx_buf = generate_ariza_docx(data)
    except Exception:
        docx_buf = None

    admin_msgs = []  # har bir adminga yuborilgan asosiy xabarning chat_id + msg_id
    for admin_id in ADMINS:
        try:
            sent = await bot.send_message(admin_id, admin_text, parse_mode='HTML', reply_markup=ariza_action_kb)
            admin_msgs.append({"chat_id": str(admin_id), "msg_id": sent.message_id})
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
        except Exception:
            pass

    if admin_msgs:
        await db.save_ariza_admin_msgs(ariza['id'], admin_msgs)
