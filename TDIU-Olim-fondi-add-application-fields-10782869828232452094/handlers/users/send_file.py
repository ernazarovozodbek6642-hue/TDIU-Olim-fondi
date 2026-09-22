import uuid
from datetime import datetime

import pytz
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)

from data.config import STORAGE_CHANNEL
from keyboards.default.Student_DB import build_main_kb_uz, build_main_kb_ru
from loader import dp, db, bot
from states.states import SendFile


def sessions_kb(sessions, lang='uz'):
    rows = [[InlineKeyboardButton(
        f"📅 {s['name']}", callback_data=f"doc_session:{s['id']}"
    )] for s in sessions]
    rows.append([InlineKeyboardButton(
        "❌ Bekor qilish" if lang == 'uz' else "❌ Отмена",
        callback_data="doc_cancel"
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def collecting_kb(lang='uz'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            "✅ Yuklashni tugatish" if lang == 'uz' else "✅ Завершить загрузку",
            callback_data="doc_files_done"
        )],
        [InlineKeyboardButton(
            "❌ Bekor qilish" if lang == 'uz' else "❌ Отмена",
            callback_data="doc_cancel"
        )]
    ])


def confirm_kb(lang='uz'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            "✅ Yuborish" if lang == 'uz' else "✅ Отправить",
            callback_data="doc_submit"
        )],
        [InlineKeyboardButton(
            "➕ Yana fayl qo'shish" if lang == 'uz' else "➕ Добавить файл",
            callback_data="doc_add_more"
        )],
        [InlineKeyboardButton(
            "❌ Bekor qilish" if lang == 'uz' else "❌ Отмена",
            callback_data="doc_cancel"
        )]
    ])


def back_keyboard(lang='uz'):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(
            "⬅️Ortga" if lang == 'uz' else "⬅️Назад"
        ), KeyboardButton(
            "❌ Bekor qilish" if lang == 'uz' else "❌ Отмена"
        )]],
        resize_keyboard=True
    )


async def _user_lang(user_id):
    user = await db.select_user(str(user_id))
    return (user.get('language', 'uz') if user else 'uz'), user


async def _main_menu(message, user_id, lang, registered=True):
    kb = await (
        build_main_kb_uz(db, registered, str(user_id))
        if lang == 'uz' else build_main_kb_ru(db, registered, str(user_id))
    )
    await message.answer("Asosiy menyu" if lang == 'uz' else "Главное меню", reply_markup=kb)


@dp.message_handler(text=["📂Hujjat yuborish", "📂Отправить документ"], state='*')
async def send_file_start(msg: Message, state: FSMContext):
    await state.finish()
    lang, _ = await _user_lang(msg.from_user.id)
    sessions = await db.get_user_document_sessions(str(msg.from_user.id))
    if not sessions:
        await msg.answer(
            "⛔ Sizga hujjat yuborish uchun ruxsat berilmagan."
            if lang == 'uz' else
            "⛔ У вас нет разрешения на отправку документов."
        )
        return
    await state.update_data(files=[])
    await msg.answer(
        "📅 Hujjat qaysi sessiyaga tegishli ekanini tanlang:"
        if lang == 'uz' else
        "📅 Выберите сессию, к которой относится документ:",
        reply_markup=sessions_kb(sessions, lang)
    )
    await SendFile.session.set()


@dp.callback_query_handler(Text(startswith="doc_session:"), state=SendFile.session)
async def select_document_session(call: CallbackQuery, state: FSMContext):
    session_id = int(call.data.split(":", 1)[1])
    lang, _ = await _user_lang(call.from_user.id)
    if not await db.has_document_permission(str(call.from_user.id), session_id):
        await call.answer("Ruxsat bekor qilingan" if lang == 'uz' else "Разрешение отозвано", show_alert=True)
        await state.finish()
        return
    session = await db.get_session_by_id(session_id)
    if not session:
        await call.answer("Sessiya topilmadi", show_alert=True)
        return
    await state.update_data(session_id=session_id, session_name=session['name'])
    await call.answer()
    await call.message.delete()
    await call.message.answer(
        (f"📅 Sessiya: <b>{session['name']}</b>\n\n📝 Hujjat mavzusini kiriting:"
         if lang == 'uz' else
         f"📅 Сессия: <b>{session['name']}</b>\n\n📝 Введите тему документа:"),
        reply_markup=back_keyboard(lang), parse_mode='HTML'
    )
    await SendFile.theme.set()


@dp.message_handler(Text(equals=["⬅️Ortga", "⬅️Назад"]), state=SendFile.theme)
async def back_to_document_sessions(msg: Message, state: FSMContext):
    lang, _ = await _user_lang(msg.from_user.id)
    sessions = await db.get_user_document_sessions(str(msg.from_user.id))
    await msg.answer(
        "📅 Sessiyani tanlang:" if lang == 'uz' else "📅 Выберите сессию:",
        reply_markup=sessions_kb(sessions, lang)
    )
    await SendFile.session.set()


@dp.message_handler(state=SendFile.theme, content_types=['text'])
async def receive_document_theme(msg: Message, state: FSMContext):
    if msg.text in ["❌ Bekor qilish", "❌ Отмена"]:
        await cancel_document_message(msg, state)
        return
    theme = (msg.text or '').strip()
    if not theme:
        return
    await state.update_data(theme=theme, files=[])
    lang, _ = await _user_lang(msg.from_user.id)
    await msg.answer(
        ("📎 Fayl yoki rasm yuboring. Bir nechta fayl yuborishingiz mumkin.\n"
         "Har bir fayldan keyin «Yuklashni tugatish» tugmasini bosing."
         if lang == 'uz' else
         "📎 Отправьте файл или фото. Можно отправить несколько файлов.\n"
         "После загрузки нажмите «Завершить загрузку»."),
        reply_markup=back_keyboard(lang)
    )
    await SendFile.files.set()


@dp.message_handler(Text(equals=["⬅️Ortga", "⬅️Назад"]), state=SendFile.files)
async def back_to_document_theme(msg: Message, state: FSMContext):
    lang, _ = await _user_lang(msg.from_user.id)
    await msg.answer(
        "📝 Hujjat mavzusini qayta kiriting:" if lang == 'uz' else "📝 Введите тему документа заново:",
        reply_markup=back_keyboard(lang)
    )
    await SendFile.theme.set()


@dp.message_handler(state=SendFile.files, content_types=['document', 'photo'])
async def collect_document_file(msg: Message, state: FSMContext):
    data = await state.get_data()
    files = list(data.get('files') or [])
    lang, _ = await _user_lang(msg.from_user.id)
    if len(files) >= 20:
        await msg.answer(
            "❌ Bir yuborishda 20 tadan ortiq fayl mumkin emas."
            if lang == 'uz' else "❌ Не более 20 файлов за одну отправку."
        )
        return
    if msg.photo:
        item = {'file_id': msg.photo[-1].file_id, 'file_type': 'photo', 'file_name': f'photo_{len(files)+1}.jpg'}
    else:
        item = {
            'file_id': msg.document.file_id,
            'file_type': 'document',
            'file_name': msg.document.file_name or f'document_{len(files)+1}'
        }
    files.append(item)
    await state.update_data(files=files)
    await msg.answer(
        (f"✅ {len(files)}-fayl qo‘shildi. Yana fayl yuboring yoki tugating."
         if lang == 'uz' else
         f"✅ Добавлен файл №{len(files)}. Добавьте ещё или завершите загрузку."),
        reply_markup=collecting_kb(lang)
    )


@dp.callback_query_handler(text="doc_files_done", state=SendFile.files)
async def finish_collecting_files(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    files = data.get('files') or []
    lang, _ = await _user_lang(call.from_user.id)
    if not files:
        await call.answer("Avval fayl yuboring" if lang == 'uz' else "Сначала отправьте файл", show_alert=True)
        return
    await call.answer()
    await call.message.answer(
        (f"📋 <b>Yuborishni tasdiqlang</b>\n\n"
         f"📅 Sessiya: {data.get('session_name')}\n"
         f"📝 Mavzu: {data.get('theme')}\n"
         f"📎 Fayllar: {len(files)} ta"
         if lang == 'uz' else
         f"📋 <b>Подтвердите отправку</b>\n\n"
         f"📅 Сессия: {data.get('session_name')}\n"
         f"📝 Тема: {data.get('theme')}\n"
         f"📎 Файлов: {len(files)}"),
        reply_markup=confirm_kb(lang), parse_mode='HTML'
    )
    await SendFile.confirm.set()


@dp.callback_query_handler(text="doc_add_more", state=SendFile.confirm)
async def add_more_documents(call: CallbackQuery, state: FSMContext):
    await call.answer()
    lang, _ = await _user_lang(call.from_user.id)
    await call.message.answer(
        "📎 Yana fayl yuboring:" if lang == 'uz' else "📎 Отправьте ещё один файл:",
        reply_markup=back_keyboard(lang)
    )
    await SendFile.files.set()


@dp.callback_query_handler(text="doc_submit", state=SendFile.confirm)
async def submit_documents(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session_id = data.get('session_id')
    lang, user = await _user_lang(call.from_user.id)
    if not session_id or not await db.has_document_permission(str(call.from_user.id), session_id):
        await call.answer("Ruxsat bekor qilingan" if lang == 'uz' else "Разрешение отозвано", show_alert=True)
        await state.finish()
        return
    files = data.get('files') or []
    if not files:
        await call.answer("Fayl topilmadi", show_alert=True)
        return

    await call.answer("⏳ Saqlanmoqda..." if lang == 'uz' else "⏳ Сохраняется...")
    batch_id = uuid.uuid4().hex
    now = datetime.now(pytz.timezone("Asia/Tashkent")).replace(tzinfo=None)
    student = (user.get('real_name') or user.get('full_name') or str(call.from_user.id)) if user else str(call.from_user.id)
    saved = 0
    for index, item in enumerate(files, 1):
        channel_message_id = None
        caption = (
            f"📄 {data.get('theme')} | 🎓 {student} | "
            f"📅 {data.get('session_name')} | {index}/{len(files)}"
        )
        try:
            if item['file_type'] == 'photo':
                sent = await bot.send_photo(STORAGE_CHANNEL, item['file_id'], caption=caption)
            else:
                sent = await bot.send_document(STORAGE_CHANNEL, item['file_id'], caption=caption)
            channel_message_id = sent.message_id
        except Exception as exc:
            print(f"[STORAGE CHANNEL ERROR] {exc}")
        await db.add_document(
            user_id=str(call.from_user.id), theme=data.get('theme', ''),
            file_id=item['file_id'], file_type=item['file_type'],
            channel_message_id=channel_message_id, session_id=session_id,
            batch_id=batch_id, created_at=now
        )
        saved += 1

    await state.finish()
    admins = await db.get_all_admins()
    for admin in admins:
        if not admin['is_active'] or not (admin['is_superadmin'] or admin['can_manage_documents']):
            continue
        try:
            await bot.send_message(
                admin['user_id'],
                f"📥 <b>Yangi hujjatlar</b>\n\n👤 {student}\n📅 {data.get('session_name')}\n"
                f"📝 {data.get('theme')}\n📎 {saved} ta fayl",
                parse_mode='HTML'
            )
        except Exception as exc:
            print(f"[DOCUMENT ADMIN NOTIFY ERROR] {exc}")

    await call.message.answer(
        (f"✅ {saved} ta hujjatingiz qabul qilindi va ko‘rib chiqishga yuborildi."
         if lang == 'uz' else
         f"✅ Принято файлов: {saved}. Они отправлены на рассмотрение.")
    )
    await _main_menu(call.message, call.from_user.id, lang, bool(user and user.get('registered')))


@dp.callback_query_handler(text="doc_cancel", state='*')
async def cancel_document(call: CallbackQuery, state: FSMContext):
    await state.finish()
    await call.answer()
    lang, user = await _user_lang(call.from_user.id)
    await call.message.answer("❌ Bekor qilindi." if lang == 'uz' else "❌ Отменено.")
    await _main_menu(call.message, call.from_user.id, lang, bool(user and user.get('registered')))


async def cancel_document_message(msg: Message, state: FSMContext):
    await state.finish()
    lang, user = await _user_lang(msg.from_user.id)
    await msg.answer("❌ Bekor qilindi." if lang == 'uz' else "❌ Отменено.")
    await _main_menu(msg, msg.from_user.id, lang, bool(user and user.get('registered')))


@dp.message_handler(Text(equals=["❌ Bekor qilish", "❌ Отмена"]), state=[
    SendFile.session, SendFile.theme, SendFile.files, SendFile.confirm
])
async def cancel_document_by_text(msg: Message, state: FSMContext):
    await cancel_document_message(msg, state)
