import io
import zipfile
from aiogram.types import CallbackQuery, InputFile
from aiogram.dispatcher.filters import Text
from loader import dp, db, bot
from data.config import ADMINS, STORAGE_CHANNEL
from keyboards.inline.admin_kb import docs_menu_kb, doc_users_kb, doc_list_kb, back_to_admin_kb
from datetime import datetime
import pytz


@dp.callback_query_handler(text='adm:docs')
async def admin_docs(call: CallbackQuery):
    if str(call.from_user.id) not in ADMINS:
        return
    total = await db.count_documents()
    await call.message.edit_text(
        f"📂 <b>Hujjatlar</b>\n\nJami: <b>{total}</b> ta",
        reply_markup=docs_menu_kb(), parse_mode='HTML'
    )


# ─── BARCHA HUJJATLAR (ZIP) ───
@dp.callback_query_handler(text='docs:all')
async def docs_all_users(call: CallbackQuery):
    if str(call.from_user.id) not in ADMINS:
        return
    users = await db.get_users_with_documents()
    if not users:
        await call.answer("Hujjat yuborgan foydalanuvchi yo'q", show_alert=True)
        return
    await call.message.edit_text(
        "👥 Foydalanuvchini tanlang — barcha hujjatlari ZIP yuboriladi:",
        reply_markup=doc_users_kb(users, mode='zip')
    )


@dp.callback_query_handler(Text(startswith='docuser:zip:'))
async def zip_user_docs(call: CallbackQuery):
    if str(call.from_user.id) not in ADMINS:
        return
    user_id = call.data.split(':')[2]
    user = await db.select_user(user_id)
    name = user.get('real_name') or user.get('full_name') or user_id if user else user_id
    docs = await db.select_user_documents(user_id)
    if not docs:
        await call.answer("Hujjat topilmadi", show_alert=True)
        return

    await call.answer("⏳ ZIP tayyorlanmoqda...")

    zip_buffer = io.BytesIO()
    errors = 0
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, doc in enumerate(docs, 1):
            try:
                tg_file = await bot.get_file(doc['file_id'])
                file_data = await bot.download_file(tg_file.file_path)
                # Kengaytmani aniqlash
                ext = tg_file.file_path.split('.')[-1] if '.' in tg_file.file_path else \
                    ('jpg' if doc['file_type'] == 'photo' else 'pdf')
                theme = (doc.get('theme') or 'hujjat').replace('/', '_')[:30]
                filename = f"{i:02d}_{theme}.{ext}"
                zf.writestr(filename, file_data.read())
            except Exception as e:
                errors += 1
                print(f"[ZIP ERROR] doc {doc['id']}: {e}")

    zip_buffer.seek(0)
    safe_name = name.replace(' ', '_')[:20]
    caption = f"📦 {name} — {len(docs)} ta hujjat"
    if errors:
        caption += f"\n⚠️ {errors} ta fayl yuklashda xatolik"
    await bot.send_document(
        call.from_user.id,
        InputFile(zip_buffer, filename=f"{safe_name}_hujjatlar.zip"),
        caption=caption
    )


# ─── QIDIRISH ───
@dp.callback_query_handler(text='docs:search')
async def docs_search(call: CallbackQuery):
    if str(call.from_user.id) not in ADMINS:
        return
    users = await db.get_users_with_documents()
    if not users:
        await call.answer("Hujjat yuborgan foydalanuvchi yo'q", show_alert=True)
        return
    await call.message.edit_text(
        "🔍 Foydalanuvchini tanlang:",
        reply_markup=doc_users_kb(users, mode='view')
    )


@dp.callback_query_handler(Text(startswith='docuser:view:'))
async def view_user_docs(call: CallbackQuery):
    if str(call.from_user.id) not in ADMINS:
        return
    user_id = call.data.split(':')[2]
    user = await db.select_user(user_id)
    name = user.get('real_name') or user.get('full_name') or user_id if user else user_id
    docs = await db.select_user_documents(user_id)
    if not docs:
        await call.answer("Hujjat topilmadi", show_alert=True)
        return
    await call.message.edit_text(
        f"📂 <b>{name}</b> ning hujjatlari ({len(docs)} ta):",
        reply_markup=doc_list_kb(docs, user_id), parse_mode='HTML'
    )


@dp.callback_query_handler(Text(startswith='docview:'))
async def view_single_doc(call: CallbackQuery):
    if str(call.from_user.id) not in ADMINS:
        return
    doc_id = int(call.data.split(':')[1])
    doc = await db.get_document_by_id(doc_id)
    if not doc:
        await call.answer("Topilmadi", show_alert=True)
        return
    name = doc.get('real_name') or doc.get('full_name') or '-'
    theme = doc.get('theme') or '-'
    created = doc.get('created_at')
    date_str = created.strftime('%d.%m.%Y %H:%M') if created else '-'

    caption = (
        f"📄 <b>Hujjat ma'lumotlari</b>\n\n"
        f"👤 Talaba: {name}\n"
        f"📝 Mavzu: {theme}\n"
        f"📅 Sana: {date_str}"
    )
    try:
        if doc['file_type'] == 'photo':
            await call.message.answer_photo(doc['file_id'], caption=caption, parse_mode='HTML')
        else:
            await call.message.answer_document(doc['file_id'], caption=caption, parse_mode='HTML')
    except Exception:
        # file_id eskirgan bo'lsa, kanaldan forward qilish
        if doc.get('channel_message_id'):
            await bot.forward_message(
                call.from_user.id, STORAGE_CHANNEL, doc['channel_message_id']
            )
        else:
            await call.answer("❌ Fayl mavjud emas", show_alert=True)
