from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, Message

from data.config import ADMINS
from keyboards.inline.admin_kb import (
    arizalar_menu_kb, arizalar_list_kb, ariza_detail_kb, back_to_admin_kb
)
from loader import dp, db, bot
from states.states import AdminArizaStates


async def _delete_admin_msgs(ariza_id: int, skip_chat_id: str = None):
    """Barcha adminlarga yuborilgan ariza xabarlarini o'chirish.
    skip_chat_id — shu chat dagi xabar o'chirilmaydi (allaqachon edit qilingan)."""
    msgs = await db.get_ariza_admin_msgs(ariza_id)
    for m in msgs:
        if skip_chat_id and str(m['chat_id']) == str(skip_chat_id):
            continue
        try:
            await bot.delete_message(m['chat_id'], m['msg_id'])
        except Exception:
            pass


# ════════════════════════════════════════
#  ARIZALAR BO'LIMI
# ════════════════════════════════════════

@dp.callback_query_handler(text='adm:arizalar')
async def admin_arizalar(call: CallbackQuery, state: FSMContext):
    if str(call.from_user.id) not in ADMINS:
        return
    await state.finish()
    pending = await db.count_arizalar('pending')
    approved = await db.count_arizalar('approved')
    rejected = await db.count_arizalar('rejected')
    await call.message.edit_text(
        f"📋 <b>Arizalar</b>\n\n"
        f"⏳ Kutilayotgan: <b>{pending}</b>\n"
        f"✅ Tasdiqlangan: <b>{approved}</b>\n"
        f"❌ Rad etilgan: <b>{rejected}</b>",
        reply_markup=arizalar_menu_kb(), parse_mode='HTML'
    )


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("ariza_list:"))
async def arizalar_list(call: CallbackQuery):
    if str(call.from_user.id) not in ADMINS:
        return
    status = call.data.split(":")[1]
    arizalar = await db.get_all_arizalar(status)
    if not arizalar:
        label = {"pending": "kutilayotgan", "approved": "tasdiqlangan", "rejected": "rad etilgan"}.get(status, "")
        await call.message.edit_text(
            f"📋 Hozircha {label} arizalar yo'q.",
            reply_markup=back_to_admin_kb()
        )
        return
    label = {"pending": "⏳ Kutilayotganlar", "approved": "✅ Tasdiqlangan", "rejected": "❌ Rad etilgan"}.get(status, "")
    await call.message.edit_text(
        f"📋 <b>{label}</b> ({len(arizalar)} ta)",
        reply_markup=arizalar_list_kb(arizalar, status),
        parse_mode='HTML'
    )


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("ariza_page:"))
async def arizalar_page(call: CallbackQuery):
    if str(call.from_user.id) not in ADMINS:
        return
    _, status, page = call.data.split(":")
    page = int(page)
    arizalar = await db.get_all_arizalar(status)
    label = {"pending": "⏳ Kutilayotganlar", "approved": "✅ Tasdiqlangan", "rejected": "❌ Rad etilgan"}.get(status, "")
    await call.message.edit_text(
        f"📋 <b>{label}</b> ({len(arizalar)} ta)",
        reply_markup=arizalar_list_kb(arizalar, status, page=page),
        parse_mode='HTML'
    )


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("ariza:") and c.data.split(":")[1].isdigit())
async def ariza_detail(call: CallbackQuery):
    if str(call.from_user.id) not in ADMINS:
        return
    ariza_id = int(call.data.split(":")[1])
    a = await db.get_ariza_by_id(ariza_id)
    if not a:
        await call.answer("Topilmadi", show_alert=True)
        return

    def bool_str(v): return "Ha ✅" if v else "Yo'q ❌"

    status_label = {"pending": "⏳ Kutilayotgan", "approved": "✅ Tasdiqlangan",
                    "rejected": "❌ Rad etilgan", "cancelled": "🗑 Bekor qilingan"}.get(a['status'], a['status'])

    text = (
        f"📋 <b>Ariza #{a['id']}</b> — {status_label}\n\n"
        f"👤 F.I.SH: <b>{a['fish']}</b>\n"
        f"📅 Tug'ilgan: {a['tugilgan_sana']}\n"
        f"🌍 Millat: {a['millat']}\n"
        f"📍 Manzil: {a['manzil']}\n"
        f"📱 Telefon: {a['telefon']}\n"
        f"📧 Email: {a['email']}\n\n"
        f"🎓 OTM: {a['otm']}\n"
        f"📋 Shakl: {a['talim_shakli']}\n"
        f"📚 Yo'nalish: {a['yonalish']}\n"
        f"📖 Kurs: {a['kurs']}\n"
        f"🔬 Ilmiy tadqiqot: {bool_str(a['ilmiy_tadqiqot'])}\n"
    )
    if a.get('tadqiqot_info'):
        text += f"  ↳ {a['tadqiqot_info']}\n"
    text += (
        f"🎤 Konferensiya: {bool_str(a['konferensiya'])}\n"
        f"📰 Maqolalar: {bool_str(a['maqola'])}\n\n"
        f"💰 Oldin grant: {bool_str(a['oldin_grant'])}\n"
    )
    if a.get('grant_info'):
        text += f"  ↳ {a['grant_info']}\n"
    text += (
        f"💵 Kontrakt: {a['kontrakt_sum']}\n\n"
        f"👨‍👩‍👧‍👦 Oila soni: {a['oila_soni']}\n"
        f"👨 Ota: {a['ota_info']}\n"
        f"👩 Ona: {a['ona_info']}\n"
        f"👫 Aka/opa: {a['aka_opa_info']}\n\n"
        f"📱 Telegram: @{a['username'] or '—'} (ID: <code>{a['user_id']}</code>)"
    )
    if a['status'] == 'rejected' and a.get('rejection_reason'):
        text += f"\n\n❌ Rad sababi: <i>{a['rejection_reason']}</i>"

    await call.message.edit_text(text, reply_markup=ariza_detail_kb(ariza_id, a['status']), parse_mode='HTML')

    # Motivatsion xatni alohida yuborish
    if a.get('motivatsion_xat'):
        await call.message.answer(
            f"📝 <b>Motivatsion xat (#{a['id']}):</b>\n\n{a['motivatsion_xat']}",
            parse_mode='HTML'
        )


# ════════════════════════════════════════
#  TASDIQLASH
# ════════════════════════════════════════

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("ariza_ok:"))
async def ariza_tasdiqlash(call: CallbackQuery):
    if str(call.from_user.id) not in ADMINS:
        return
    ariza_id = int(call.data.split(":")[1])
    a = await db.get_ariza_by_id(ariza_id)
    if not a:
        await call.answer("Topilmadi", show_alert=True)
        return
    if a['status'] != 'pending':
        await call.answer("Bu ariza allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await db.update_ariza_status(ariza_id, 'approved')

    # Foydalanuvchini registered sifatida belgilash
    await db.update_user_registration(
        user_id=a['user_id'],
        real_name=a['fish'],
        phone=a['telefon'],
        otm=a['otm'],
        course=a['kurs']
    )

    await call.message.edit_text(
        f"✅ <b>Ariza #{ariza_id} tasdiqlandi!</b>\n\n"
        f"👤 {a['fish']}\n"
        f"Foydalanuvchi hujjat yuborish bo'limiga qo'shildi.",
        parse_mode='HTML',
        reply_markup=back_to_admin_kb()
    )

    # Qolgan adminlarning xabarlarini o'chirish
    await _delete_admin_msgs(ariza_id, skip_chat_id=str(call.from_user.id))

    # Foydalanuvchiga xabar
    user = await db.select_user(a['user_id'])
    lang = user.get('language', 'uz') if user else 'uz'
    try:
        if lang == 'uz':
            await bot.send_message(
                a['user_id'],
                "🎉 <b>Tabriklaymiz!</b>\n\n"
                "Arizangiz ko'rib chiqildi va <b>tasdiqlandi</b>!\n\n"
                "Endi «📂 Hujjat yuborish» bo'limidan foydalanishingiz mumkin.",
                parse_mode='HTML'
            )
        else:
            await bot.send_message(
                a['user_id'],
                "🎉 <b>Поздравляем!</b>\n\n"
                "Ваша заявка рассмотрена и <b>одобрена</b>!\n\n"
                "Теперь вы можете пользоваться разделом «📂 Отправить документ».",
                parse_mode='HTML'
            )
    except Exception:
        pass


# ════════════════════════════════════════
#  RAD ETISH
# ════════════════════════════════════════

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("ariza_rad:"))
async def ariza_rad_start(call: CallbackQuery, state: FSMContext):
    if str(call.from_user.id) not in ADMINS:
        return
    ariza_id = int(call.data.split(":")[1])
    a = await db.get_ariza_by_id(ariza_id)
    if not a:
        await call.answer("Topilmadi", show_alert=True)
        return
    if a['status'] != 'pending':
        await call.answer("Bu ariza allaqachon ko'rib chiqilgan.", show_alert=True)
        return
    await state.update_data(reject_ariza_id=ariza_id)
    await call.answer()
    await call.message.answer(
        f"❌ Ariza #{ariza_id} ni rad etmoqchisiz.\n\n"
        f"Rad etish sababini yozing:"
    )
    await AdminArizaStates.reject_reason.set()


@dp.message_handler(state=AdminArizaStates.reject_reason)
async def ariza_rad_reason(msg: Message, state: FSMContext):
    if str(msg.from_user.id) not in ADMINS:
        return
    data = await state.get_data()
    ariza_id = data.get('reject_ariza_id')
    reason = msg.text.strip()
    await state.finish()

    a = await db.get_ariza_by_id(ariza_id)
    if not a:
        await msg.answer("❌ Ariza topilmadi.")
        return

    await db.update_ariza_status(ariza_id, 'rejected', rejection_reason=reason)

    # Barcha adminlarning ariza xabarlarini o'chirish
    await _delete_admin_msgs(ariza_id)

    await msg.answer(
        f"✅ Ariza #{ariza_id} rad etildi.\nSabab: <i>{reason}</i>",
        parse_mode='HTML',
        reply_markup=back_to_admin_kb()
    )

    # Foydalanuvchiga xabar
    user = await db.select_user(a['user_id'])
    lang = user.get('language', 'uz') if user else 'uz'
    try:
        if lang == 'uz':
            await bot.send_message(
                a['user_id'],
                f"❌ <b>Arizangiz ko'rib chiqildi</b>\n\n"
                f"Afsuski, arizangiz rad etildi.\n\n"
                f"<b>Sabab:</b> <i>{reason}</i>\n\n"
                f"Savollaringiz bo'lsa, murojaat yuborishingiz mumkin.",
                parse_mode='HTML'
            )
        else:
            await bot.send_message(
                a['user_id'],
                f"❌ <b>Ваша заявка рассмотрена</b>\n\n"
                f"К сожалению, ваша заявка была отклонена.\n\n"
                f"<b>Причина:</b> <i>{reason}</i>\n\n"
                f"Если есть вопросы — напишите обращение.",
                parse_mode='HTML'
            )
    except Exception:
        pass


# ════════════════════════════════════════
#  QIDIRISH
# ════════════════════════════════════════

@dp.callback_query_handler(text='ariza_search')
async def ariza_search_start(call: CallbackQuery, state: FSMContext):
    if str(call.from_user.id) not in ADMINS:
        return
    await call.answer()
    await call.message.answer("🔍 Nomzodning F.I.SH ni kiriting:")
    await AdminArizaStates.search.set()


@dp.message_handler(state=AdminArizaStates.search)
async def ariza_search_result(msg: Message, state: FSMContext):
    if str(msg.from_user.id) not in ADMINS:
        return
    query = msg.text.strip()
    await state.finish()
    results = await db.search_arizalar(query)
    if not results:
        await msg.answer(f"❌ «{query}» bo'yicha ariza topilmadi.", reply_markup=back_to_admin_kb())
        return
    await msg.answer(
        f"🔍 <b>«{query}»</b> bo'yicha {len(results)} ta natija:",
        reply_markup=arizalar_list_kb(results, 'all'),
        parse_mode='HTML'
    )
