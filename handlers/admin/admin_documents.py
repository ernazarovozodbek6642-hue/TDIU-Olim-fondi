import io
import zipfile
from datetime import datetime, timedelta

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, Message, InputFile, InlineKeyboardMarkup, InlineKeyboardButton

from data.config import STORAGE_CHANNEL
from keyboards.default.Student_DB import build_main_kb_uz, build_main_kb_ru
from keyboards.inline.admin_kb import back_to_admin_kb
from loader import dp, db, bot
from states.states import AdminDocumentStates, AdminAccessStates


PER_PAGE = 10


async def _allowed(user_id):
    return await db.has_admin_permission(str(user_id), 'documents')


def sessions_kb(sessions, prefix):
    rows = [[InlineKeyboardButton(
        f"{'🟢' if s['is_active'] else '⚪'} {s['name']}",
        callback_data=f"{prefix}:{s['id']}"
    )] for s in sessions]
    rows.append([InlineKeyboardButton("⬅️ Ortga", callback_data="adm:docs")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def document_status_kb(session_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("⏳ Yangi", callback_data=f"docs_list:{session_id}:pending:0")],
        [InlineKeyboardButton("✅ Tasdiqlangan", callback_data=f"docs_list:{session_id}:approved:0")],
        [InlineKeyboardButton("❌ Rad etilgan", callback_data=f"docs_list:{session_id}:rejected:0")],
        [InlineKeyboardButton("📋 Barchasi", callback_data=f"docs_list:{session_id}:all:0")],
        [InlineKeyboardButton("🔍 Ism yoki mavzu", callback_data=f"docs_search:{session_id}")],
        [InlineKeyboardButton("📅 Sana oralig‘i", callback_data=f"docs_date:{session_id}")],
        [InlineKeyboardButton("⬅️ Sessiyalar", callback_data="docs:sessions")],
    ])


def documents_kb(docs, session_id, status, page, zip_date_from=None, zip_date_to=None):
    total_pages = max(1, (len(docs) + PER_PAGE - 1) // PER_PAGE)
    page = max(0, min(page, total_pages - 1))
    start = page * PER_PAGE
    rows = []
    icons = {'pending': '⏳', 'approved': '✅', 'rejected': '❌'}
    for doc in docs[start:start + PER_PAGE]:
        name = doc.get('real_name') or doc.get('full_name') or doc.get('user_id')
        rows.append([InlineKeyboardButton(
            f"{icons.get(doc.get('status'), '📄')} {name} — {(doc.get('theme') or 'Mavzusiz')[:25]}",
            callback_data=f"docview:{doc['id']}:{session_id}:{status}:{page}"
        )])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"docs_list:{session_id}:{status}:{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page + 1 < total_pages:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"docs_list:{session_id}:{status}:{page+1}"))
    rows.append(nav)
    if zip_date_from and zip_date_to:
        zip_callback = f"docs_zip_date:{session_id}:{zip_date_from}:{zip_date_to}"
    else:
        zip_callback = f"docs_zip:{session_id}:{status}"
    rows.append([InlineKeyboardButton("📦 ZIP yuklash", callback_data=zip_callback)])
    rows.append([InlineKeyboardButton("⬅️ Holatlar", callback_data=f"docs_session:{session_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def document_detail_kb(doc_id, session_id, status, page, current_status):
    rows = []
    if current_status == 'pending':
        rows.append([
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"doc_ok:{doc_id}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"doc_reject:{doc_id}"),
        ])
    rows.append([InlineKeyboardButton(
        "⬅️ Ro‘yxat", callback_data=f"docs_list:{session_id}:{status}:{page}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def permission_users_kb(users, session_id, page=0):
    total_pages = max(1, (len(users) + PER_PAGE - 1) // PER_PAGE)
    page = max(0, min(page, total_pages - 1))
    rows = []
    for user in users[page * PER_PAGE:(page + 1) * PER_PAGE]:
        name = user.get('real_name') or user.get('full_name') or user['id']
        rows.append([InlineKeyboardButton(
            f"{'✅' if user['is_allowed'] else '🚫'} {name}",
            callback_data=f"docperm_toggle:{session_id}:{user['id']}:{page}"
        )])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"docperm_page:{session_id}:{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page + 1 < total_pages:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"docperm_page:{session_id}:{page+1}"))
    rows.append(nav)
    rows.append([InlineKeyboardButton("🔍 Talabani qidirish", callback_data=f"docperm_search:{session_id}")])
    rows.append([InlineKeyboardButton("⬅️ Sessiyalar", callback_data="docs:permissions")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@dp.callback_query_handler(text='adm:docs', state='*')
async def admin_docs(call: CallbackQuery, state: FSMContext):
    if not await _allowed(call.from_user.id):
        return
    await state.finish()
    await call.answer()
    total = await db.count_documents()
    await call.message.edit_text(
        f"📂 <b>Hujjatlar boshqaruvi</b>\n\nJami: <b>{total}</b> ta",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("📂 Hujjatlarni ko‘rish", callback_data="docs:sessions")],
            [InlineKeyboardButton("🔐 Talabalarga ruxsat", callback_data="docs:permissions")],
            [InlineKeyboardButton("⬅️ Ortga", callback_data="adm:main")],
        ]), parse_mode='HTML'
    )


@dp.callback_query_handler(text='docs:sessions', state='*')
async def choose_document_session(call: CallbackQuery):
    if not await _allowed(call.from_user.id):
        return
    sessions = await db.get_all_sessions()
    await call.message.edit_text(
        "📅 Hujjatlarni ko‘rish uchun sessiyani tanlang:",
        reply_markup=sessions_kb(sessions, 'docs_session')
    )


@dp.callback_query_handler(Text(startswith='docs_session:'), state='*')
async def document_session_menu(call: CallbackQuery):
    if not await _allowed(call.from_user.id):
        return
    session_id = int(call.data.split(':')[1])
    session = await db.get_session_by_id(session_id)
    await call.message.edit_text(
        f"📅 <b>{session['name']}</b>\n\nHujjatlar holatini tanlang:",
        reply_markup=document_status_kb(session_id), parse_mode='HTML'
    )


@dp.callback_query_handler(Text(startswith='docs_list:'), state='*')
async def list_documents(call: CallbackQuery):
    if not await _allowed(call.from_user.id):
        return
    _, session_id, status, page = call.data.split(':')
    docs = await db.get_documents_filtered(int(session_id), None if status == 'all' else status)
    await call.message.edit_text(
        f"📋 Hujjatlar: <b>{len(docs)}</b> ta",
        reply_markup=documents_kb(docs, int(session_id), status, int(page)),
        parse_mode='HTML'
    )


@dp.callback_query_handler(Text(startswith='docview:'), state='*')
async def view_single_doc(call: CallbackQuery):
    if not await _allowed(call.from_user.id):
        return
    _, doc_id, session_id, status, page = call.data.split(':')
    doc = await db.get_document_by_id(int(doc_id))
    if not doc:
        await call.answer("Topilmadi", show_alert=True)
        return
    name = doc.get('real_name') or doc.get('full_name') or '-'
    created = doc.get('created_at')
    caption = (
        f"📄 <b>Hujjat #{doc['id']}</b>\n\n"
        f"👤 Talaba: {name}\n📅 Sessiya: {doc.get('session_name') or '—'}\n"
        f"📝 Mavzu: {doc.get('theme') or '—'}\n"
        f"📌 Holat: {doc.get('status') or 'pending'}\n"
        f"🕓 Sana: {created.strftime('%d.%m.%Y %H:%M') if created else '—'}"
    )
    if doc.get('rejection_reason'):
        caption += f"\n❌ Sabab: {doc['rejection_reason']}"
    try:
        if doc['file_type'] == 'photo':
            await call.message.answer_photo(doc['file_id'], caption=caption, parse_mode='HTML')
        else:
            await call.message.answer_document(doc['file_id'], caption=caption, parse_mode='HTML')
    except Exception:
        if doc.get('channel_message_id'):
            await bot.forward_message(call.from_user.id, STORAGE_CHANNEL, doc['channel_message_id'])
    await call.message.answer(
        "Amalni tanlang:",
        reply_markup=document_detail_kb(int(doc_id), int(session_id), status, int(page), doc.get('status'))
    )


@dp.callback_query_handler(Text(startswith='doc_ok:'), state='*')
async def approve_document(call: CallbackQuery):
    if not await _allowed(call.from_user.id):
        return
    doc_id = int(call.data.split(':')[1])
    doc = await db.get_document_by_id(doc_id)
    if not doc or doc.get('status') != 'pending':
        await call.answer("Hujjat allaqachon ko‘rib chiqilgan", show_alert=True)
        return
    await db.update_document_status(doc_id, 'approved', str(call.from_user.id))
    await call.answer("✅ Tasdiqlandi")
    try:
        await bot.send_message(
            doc['user_id'],
            f"✅ <b>Hujjatingiz tasdiqlandi</b>\n\n📅 {doc.get('session_name') or '—'}\n📝 {doc.get('theme') or '—'}",
            parse_mode='HTML'
        )
    except Exception:
        pass
    await call.message.edit_text("✅ Hujjat tasdiqlandi.", reply_markup=back_to_admin_kb())


@dp.callback_query_handler(Text(startswith='doc_reject:'), state='*')
async def reject_document_start(call: CallbackQuery, state: FSMContext):
    if not await _allowed(call.from_user.id):
        return
    doc_id = int(call.data.split(':')[1])
    await state.update_data(reject_document_id=doc_id)
    await call.message.answer("❌ Rad etish sababini yozing:")
    await AdminDocumentStates.reject_reason.set()


@dp.message_handler(state=AdminDocumentStates.reject_reason)
async def reject_document_save(msg: Message, state: FSMContext):
    if not await _allowed(msg.from_user.id):
        return
    data = await state.get_data()
    await state.finish()
    doc = await db.get_document_by_id(data.get('reject_document_id'))
    if not doc or doc.get('status') != 'pending':
        await msg.answer("Hujjat topilmadi yoki allaqachon ko‘rib chiqilgan.")
        return
    reason = msg.text.strip()
    await db.update_document_status(doc['id'], 'rejected', str(msg.from_user.id), reason)
    try:
        await bot.send_message(
            doc['user_id'],
            f"❌ <b>Hujjatingiz rad etildi</b>\n\n📅 {doc.get('session_name') or '—'}\n"
            f"📝 {doc.get('theme') or '—'}\nSabab: <i>{reason}</i>",
            parse_mode='HTML'
        )
    except Exception:
        pass
    await msg.answer("✅ Rad etildi va talabaga xabar yuborildi.", reply_markup=back_to_admin_kb())


async def _send_documents_zip(call, docs, filename_label):
    if not docs:
        await call.answer("Hujjat topilmadi", show_alert=True)
        return
    await call.answer("⏳ ZIP tayyorlanmoqda...")
    for part_index, start in enumerate(range(0, len(docs), 20), 1):
        chunk = docs[start:start + 20]
        buffer = io.BytesIO()
        errors = 0
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
            for doc in chunk:
                try:
                    tg_file = await bot.get_file(doc['file_id'])
                    file_data = await bot.download_file(tg_file.file_path)
                    ext = tg_file.file_path.rsplit('.', 1)[-1] if '.' in tg_file.file_path else ('jpg' if doc['file_type'] == 'photo' else 'bin')
                    name = (doc.get('real_name') or doc.get('full_name') or doc['user_id']).replace('/', '_')
                    theme = (doc.get('theme') or 'hujjat').replace('/', '_')
                    archive.writestr(f"{name[:30]}_{doc['id']}_{theme[:25]}.{ext}", file_data.read())
                except Exception:
                    errors += 1
        buffer.seek(0)
        await bot.send_document(
            call.from_user.id,
            InputFile(buffer, filename=f"hujjatlar_{filename_label}_{part_index}.zip"),
            caption=f"📦 {part_index}-qism — {len(chunk)-errors} ta fayl" + (f"\n⚠️ {errors} ta xato" if errors else "")
        )


@dp.callback_query_handler(Text(startswith='docs_zip:'), state='*')
async def export_documents_zip(call: CallbackQuery):
    if not await _allowed(call.from_user.id):
        return
    _, session_id, status = call.data.split(':')
    docs = await db.get_documents_filtered(int(session_id), None if status == 'all' else status)
    await _send_documents_zip(call, docs, f"{session_id}_{status}")


@dp.callback_query_handler(Text(startswith='docs_zip_date:'), state='*')
async def export_date_filtered_documents_zip(call: CallbackQuery):
    if not await _allowed(call.from_user.id):
        return
    try:
        _, session_id, date_from_token, date_to_token = call.data.split(':')
        date_from = datetime.strptime(date_from_token, '%Y%m%d')
        date_to_inclusive = datetime.strptime(date_to_token, '%Y%m%d')
    except (ValueError, TypeError):
        await call.answer("Sana oralig‘i noto‘g‘ri", show_alert=True)
        return
    docs = await db.get_documents_filtered(
        int(session_id),
        date_from=date_from,
        date_to=date_to_inclusive + timedelta(days=1)
    )
    await _send_documents_zip(
        call,
        docs,
        f"{session_id}_{date_from_token}_{date_to_token}"
    )


@dp.callback_query_handler(text='docs:permissions', state='*')
async def permission_sessions(call: CallbackQuery):
    if not await _allowed(call.from_user.id):
        return
    sessions = await db.get_all_sessions()
    await call.message.edit_text(
        "🔐 Ruxsat berish uchun sessiyani tanlang. Faol va nofaol sessiyalarning barchasi ko‘rsatiladi:",
        reply_markup=sessions_kb(sessions, 'docperm_session')
    )


@dp.callback_query_handler(Text(startswith='docperm_session:'), state='*')
async def permission_users(call: CallbackQuery):
    if not await _allowed(call.from_user.id):
        return
    session_id = int(call.data.split(':')[1])
    users = await db.get_document_permission_users(session_id)
    session = await db.get_session_by_id(session_id)
    await call.message.edit_text(
        f"🔐 <b>{session['name']}</b>\n\nTalabani bosing — ruxsat beriladi yoki olib tashlanadi:",
        reply_markup=permission_users_kb(users, session_id), parse_mode='HTML'
    )


@dp.callback_query_handler(Text(startswith='docperm_page:'), state='*')
async def permission_users_page(call: CallbackQuery):
    if not await _allowed(call.from_user.id):
        return
    _, session_id, page = call.data.split(':')
    users = await db.get_document_permission_users(int(session_id))
    await call.message.edit_reply_markup(reply_markup=permission_users_kb(users, int(session_id), int(page)))


@dp.callback_query_handler(Text(startswith='docperm_toggle:'), state='*')
async def toggle_document_permission(call: CallbackQuery):
    if not await _allowed(call.from_user.id):
        return
    _, session_id, user_id, page = call.data.split(':')
    users = await db.get_document_permission_users(int(session_id))
    target = next((u for u in users if str(u['id']) == user_id), None)
    if not target:
        await call.answer("Talaba topilmadi", show_alert=True)
        return
    new_value = not bool(target['is_allowed'])
    await db.set_document_permission(user_id, int(session_id), new_value, str(call.from_user.id))
    await call.answer("✅ Ruxsat berildi" if new_value else "🚫 Ruxsat olib tashlandi")
    target_user = await db.select_user(user_id)
    session = await db.get_session_by_id(int(session_id))
    if target_user:
        lang = target_user.get('language', 'uz')
        kb = await (
            build_main_kb_uz(db, target_user.get('registered', False), user_id)
            if lang == 'uz' else
            build_main_kb_ru(db, target_user.get('registered', False), user_id)
        )
        try:
            await bot.send_message(
                user_id,
                (f"✅ Sizga <b>{session['name']}</b> sessiyasi uchun hujjat yuborish ruxsati berildi."
                 if new_value and lang == 'uz' else
                 f"✅ Вам разрешена отправка документов для сессии <b>{session['name']}</b>."
                 if new_value else
                 f"🚫 <b>{session['name']}</b> sessiyasi uchun hujjat yuborish ruxsatingiz olib tashlandi."
                 if lang == 'uz' else
                 f"🚫 Разрешение на отправку документов для сессии <b>{session['name']}</b> отозвано."),
                reply_markup=kb, parse_mode='HTML'
            )
        except Exception:
            pass
    users = await db.get_document_permission_users(int(session_id))
    await call.message.edit_reply_markup(reply_markup=permission_users_kb(users, int(session_id), int(page)))


@dp.callback_query_handler(Text(startswith='docperm_search:'), state='*')
async def permission_search_start(call: CallbackQuery, state: FSMContext):
    if not await _allowed(call.from_user.id):
        return
    session_id = int(call.data.split(':')[1])
    await state.update_data(permission_search_session=session_id)
    await call.message.answer("🔍 Talabaning F.I.Sh. yoki Telegram ID raqamini kiriting:")
    await AdminAccessStates.search_student.set()


@dp.message_handler(state=AdminAccessStates.search_student)
async def permission_search_result(msg: Message, state: FSMContext):
    if not await _allowed(msg.from_user.id):
        return
    data = await state.get_data()
    await state.finish()
    session_id = data['permission_search_session']
    users = await db.search_document_permission_users(session_id, msg.text.strip())
    if not users:
        await msg.answer("❌ Talaba topilmadi.", reply_markup=back_to_admin_kb())
        return
    await msg.answer(
        f"🔍 {len(users)} ta natija:",
        reply_markup=permission_users_kb(users, session_id)
    )


@dp.callback_query_handler(Text(startswith='docs_date:'), state='*')
async def date_filter_start(call: CallbackQuery, state: FSMContext):
    if not await _allowed(call.from_user.id):
        return
    session_id = int(call.data.split(':')[1])
    await state.update_data(document_filter_session=session_id)
    await call.message.answer("📅 Boshlanish sanasini kiriting (KK.OO.YYYY):")
    await AdminDocumentStates.date_from.set()


@dp.callback_query_handler(Text(startswith='docs_search:'), state='*')
async def document_search_start(call: CallbackQuery, state: FSMContext):
    if not await _allowed(call.from_user.id):
        return
    session_id = int(call.data.split(':')[1])
    await state.update_data(document_search_session=session_id)
    await call.message.answer("🔍 Talaba F.I.Sh., Telegram ID yoki hujjat mavzusini kiriting:")
    await AdminDocumentStates.search.set()


@dp.message_handler(state=AdminDocumentStates.search)
async def document_search_result(msg: Message, state: FSMContext):
    if not await _allowed(msg.from_user.id):
        return
    data = await state.get_data()
    await state.finish()
    session_id = data['document_search_session']
    docs = await db.search_documents(session_id, msg.text.strip())
    if not docs:
        await msg.answer("❌ Hujjat topilmadi.", reply_markup=back_to_admin_kb())
        return
    await msg.answer(
        f"🔍 <b>{len(docs)}</b> ta hujjat topildi:",
        reply_markup=documents_kb(docs, session_id, 'all', 0), parse_mode='HTML'
    )


@dp.message_handler(state=AdminDocumentStates.date_from)
async def date_filter_from(msg: Message, state: FSMContext):
    if not await _allowed(msg.from_user.id):
        return
    try:
        value = datetime.strptime(msg.text.strip(), '%d.%m.%Y')
    except ValueError:
        await msg.answer("❌ Format: KK.OO.YYYY")
        return
    await state.update_data(document_date_from=value)
    await msg.answer("📅 Tugash sanasini kiriting (KK.OO.YYYY):")
    await AdminDocumentStates.date_to.set()


@dp.message_handler(state=AdminDocumentStates.date_to)
async def date_filter_to(msg: Message, state: FSMContext):
    if not await _allowed(msg.from_user.id):
        return
    try:
        date_to_inclusive = datetime.strptime(msg.text.strip(), '%d.%m.%Y')
    except ValueError:
        await msg.answer("❌ Format: KK.OO.YYYY")
        return
    data = await state.get_data()
    date_from = data['document_date_from']
    if date_to_inclusive < date_from:
        await msg.answer("❌ Tugash sanasi boshlanish sanasidan oldin bo‘lishi mumkin emas.")
        return
    await state.finish()
    date_to = date_to_inclusive + timedelta(days=1)
    docs = await db.get_documents_filtered(
        data['document_filter_session'], date_from=date_from, date_to=date_to
    )
    await msg.answer(
        f"📅 Tanlangan oraliqda <b>{len(docs)}</b> ta hujjat topildi.",
        reply_markup=documents_kb(
            docs,
            data['document_filter_session'],
            'all',
            0,
            zip_date_from=date_from.strftime('%Y%m%d'),
            zip_date_to=date_to_inclusive.strftime('%Y%m%d')
        ),
        parse_mode='HTML'
    )
