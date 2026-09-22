"""
Admin CMS — Bo'limlarni boshqarish
Ipidan ignasigacha: ko'rish, tahrirlash, qo'shish, o'chirish, tartib o'zgartirish.
"""
import os
from aiogram.types import (
    CallbackQuery, Message,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.dispatcher import FSMContext

from aiogram.utils.exceptions import MessageNotModified

from loader import dp, db, bot
from data.config import STORAGE_CHANNEL
from utils.misc.admin_access import admin_allowed
from states.states import AdminCMSStates

IMAGES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'images'
)


# ════════════════════════════════════════
#  KLAVIATURA YORDAMCHILARI
# ════════════════════════════════════════

def cms_main_kb(sections: list) -> InlineKeyboardMarkup:
    """Top-level bo'limlar ro'yxati."""
    kb = InlineKeyboardMarkup(row_width=1)
    for s in sections:
        kb.add(InlineKeyboardButton(
            f"{'✅' if s['is_active'] else '🚫'} {s['title_uz']}",
            callback_data=f"cms:open:{s['section_key']}"
        ))
    kb.add(InlineKeyboardButton("➕ Yangi bo'lim qo'shish", callback_data="cms:add:ROOT"))
    kb.add(InlineKeyboardButton("⬅️ Admin panel", callback_data="adm:main"))
    return kb


def cms_section_kb(section: dict, children: list) -> InlineKeyboardMarkup:
    """Bo'lim ichida: sub-bo'limlar + amallar."""
    kb = InlineKeyboardMarkup(row_width=1)
    for i, c in enumerate(children):
        row = [
            InlineKeyboardButton(
                f"{'✅' if c['is_active'] else '🚫'} {c['title_uz']}",
                callback_data=f"cms:open:{c['section_key']}"
            )
        ]
        # Tartib tugmalari
        nav = []
        if i > 0:
            nav.append(InlineKeyboardButton("⬆️", callback_data=f"cms:up:{c['section_key']}"))
        if i < len(children) - 1:
            nav.append(InlineKeyboardButton("⬇️", callback_data=f"cms:down:{c['section_key']}"))
        if nav:
            kb.row(*row, *nav)
        else:
            kb.add(*row)

    kb.add(InlineKeyboardButton(
        "➕ Sub-bo'lim qo'shish",
        callback_data=f"cms:add:{section['section_key']}"
    ))
    # Agar bu top-level bo'lim bo'lsa, ortga CMS main ga, aks holda parent ga
    parent = section['parent_key']
    back_cb = f"cms:open:{parent}" if parent else "cms:main"
    kb.add(InlineKeyboardButton("⬅️ Ortga", callback_data=back_cb))
    return kb


def cms_edit_kb(section: dict) -> InlineKeyboardMarkup:
    """Bo'lim tafsiloti: tahrirlash tugmalari."""
    kb = InlineKeyboardMarkup(row_width=2)
    key = section['section_key']
    active_label = "🚫 Yashirish" if section['is_active'] else "✅ Ko'rsatish"

    kb.row(
        InlineKeyboardButton("✏️ Matn (UZ)", callback_data=f"cms:edit:text_uz:{key}"),
        InlineKeyboardButton("✏️ Matn (RU)", callback_data=f"cms:edit:text_ru:{key}")
    )
    kb.row(
        InlineKeyboardButton("📝 Sarlavha (UZ)", callback_data=f"cms:edit:title_uz:{key}"),
        InlineKeyboardButton("📝 Sarlavha (RU)", callback_data=f"cms:edit:title_ru:{key}")
    )
    kb.row(
        InlineKeyboardButton("🖼 Rasm yuklash", callback_data=f"cms:edit:image:{key}"),
        InlineKeyboardButton(active_label, callback_data=f"cms:toggle:{key}")
    )
    kb.add(InlineKeyboardButton("🗑 O'chirish", callback_data=f"cms:delete:{key}"))

    parent = section['parent_key']
    back_cb = f"cms:open:{parent}" if parent else "cms:main"
    kb.add(InlineKeyboardButton("⬅️ Ortga", callback_data=back_cb))
    return kb


def confirm_delete_kb(key: str, parent_key) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.row(
        InlineKeyboardButton("✅ Ha, o'chir", callback_data=f"cms:del_confirm:{key}"),
        InlineKeyboardButton("❌ Yo'q", callback_data=f"cms:open:{key}")
    )
    return kb


def cancel_kb(back_cb: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("❌ Bekor qilish", callback_data=back_cb))
    return kb


# ════════════════════════════════════════
#  HELPER: bo'lim tafsilotini formatlash
# ════════════════════════════════════════

def section_info_text(s: dict) -> str:
    lines = [
        f"📂 <b>Bo'lim:</b> <code>{s['section_key']}</code>",
        f"👆 <b>Parent:</b> {s['parent_key'] or '—'}",
        f"🇺🇿 <b>Sarlavha UZ:</b> {s['title_uz'] or '—'}",
        f"🇷🇺 <b>Sarlavha RU:</b> {s['title_ru'] or '—'}",
        f"🖼 <b>Rasm:</b> {'✅ Yuklangan' if s['image'] else '—'}",
        "👁 <b>Holat:</b> " + ("✅ Ko'rinadi" if s['is_active'] else "🚫 Yashirin"),
        "",
        "🇺🇿 <b>Matn (UZ):</b>",
        f"<i>{(s['text_uz'] or '—')[:300]}{'...' if s['text_uz'] and len(s['text_uz']) > 300 else ''}</i>",
    ]
    return "\n".join(lines)


# ════════════════════════════════════════
#  HANDLERLAR
# ════════════════════════════════════════

async def safe_edit(call: CallbackQuery, text: str, **kwargs):
    """MessageNotModified xatosini e'tiborsiz qoldiradi."""
    try:
        await call.message.edit_text(text, **kwargs)
    except MessageNotModified:
        pass


@dp.callback_query_handler(lambda c: c.data == "cms:main", state='*')
async def cms_main(call: CallbackQuery, state: FSMContext):
    if not await admin_allowed(call.from_user.id, 'content'):
        return
    await state.finish()
    sections = await db.get_top_sections(admin=True)
    await safe_edit(
        call,
        "📝 <b>Bo'limlarni boshqarish</b>\n\nTop-level bo'limlar:",
        reply_markup=cms_main_kb(sections), parse_mode='HTML'
    )


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("cms:open:"), state='*')
async def cms_open(call: CallbackQuery, state: FSMContext):
    if not await admin_allowed(call.from_user.id, 'content'):
        return
    await state.finish()
    key = call.data.split("cms:open:")[1]
    section = await db.get_section(key)
    if not section:
        await call.answer("Bo'lim topilmadi", show_alert=True)
        return

    children = await db.get_children(admin=True, parent_key=key)

    if children:
        # Sub-bo'limlari bor → ularni ko'rsat
        text = (
            f"📂 <b>{section['title_uz']}</b>\n\n"
            f"Sub-bo'limlar: {len(children)} ta\n\n"
            "Tahrirlash uchun tugmani bosing yoki sub-bo'limni tanlang:"
        )
        # Section-level amallar uchun pastda qo'shimcha qator
        kb = cms_section_kb(section, children)
        # Bo'lim o'zini tahrirlash tugmasini qo'shish
        kb.inline_keyboard.insert(-1, [
            InlineKeyboardButton(
                "⚙️ Bu bo'limni tahrirlash",
                callback_data=f"cms:detail:{key}"
            )
        ])
        await safe_edit(call,text, reply_markup=kb, parse_mode='HTML')
    else:
        # Sub-bo'limlari yo'q → tafsilot ko'rsat
        text = section_info_text(section)
        await safe_edit(call,text, reply_markup=cms_edit_kb(section), parse_mode='HTML')


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("cms:detail:"), state='*')
async def cms_detail(call: CallbackQuery, state: FSMContext):
    if not await admin_allowed(call.from_user.id, 'content'):
        return
    key = call.data.split("cms:detail:")[1]
    section = await db.get_section(key)
    if not section:
        return
    await safe_edit(call,
        section_info_text(section),
        reply_markup=cms_edit_kb(section), parse_mode='HTML'
    )


# ── TARTIB O'ZGARTIRISH ──

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("cms:up:"), state='*')
async def cms_move_up(call: CallbackQuery, state: FSMContext):
    if not await admin_allowed(call.from_user.id, 'content'):
        return
    key = call.data.split("cms:up:")[1]
    section = await db.get_section(key)
    if not section:
        return
    siblings = await db.get_children(admin=True, parent_key=section['parent_key'])
    idx = next((i for i, s in enumerate(siblings) if s['section_key'] == key), None)
    if idx and idx > 0:
        await db.swap_section_order(key, siblings[idx - 1]['section_key'])
    await call.answer("⬆️ Ko'tarildi")
    # Refresh parent
    await _refresh_parent(call, state, section['parent_key'])


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("cms:down:"), state='*')
async def cms_move_down(call: CallbackQuery, state: FSMContext):
    if not await admin_allowed(call.from_user.id, 'content'):
        return
    key = call.data.split("cms:down:")[1]
    section = await db.get_section(key)
    if not section:
        return
    siblings = await db.get_children(admin=True, parent_key=section['parent_key'])
    idx = next((i for i, s in enumerate(siblings) if s['section_key'] == key), None)
    if idx is not None and idx < len(siblings) - 1:
        await db.swap_section_order(key, siblings[idx + 1]['section_key'])
    await call.answer("⬇️ Tushirildi")
    await _refresh_parent(call, state, section['parent_key'])


async def _refresh_parent(call: CallbackQuery, state: FSMContext, parent_key):
    if parent_key:
        parent = await db.get_section(parent_key)
        children = await db.get_children(admin=True, parent_key=parent_key)
        kb = cms_section_kb(parent, children)
        kb.inline_keyboard.insert(-1, [
            InlineKeyboardButton("⚙️ Bu bo'limni tahrirlash", callback_data=f"cms:detail:{parent_key}")
        ])
        await call.message.edit_reply_markup(reply_markup=kb)
    else:
        sections = await db.get_top_sections(admin=True)
        await call.message.edit_reply_markup(reply_markup=cms_main_kb(sections))


# ── TOGGLE (yashirish/ko'rsatish) ──

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("cms:toggle:"), state='*')
async def cms_toggle(call: CallbackQuery, state: FSMContext):
    if not await admin_allowed(call.from_user.id, 'content'):
        return
    key = call.data.split("cms:toggle:")[1]
    section = await db.get_section(key)
    if not section:
        return
    new_val = not section['is_active']
    await db.update_section_field(key, 'is_active', new_val)
    await call.answer("✅ Yashirildi" if not new_val else "✅ Ko'rsatildi")
    section = await db.get_section(key)
    await safe_edit(call,
        section_info_text(section),
        reply_markup=cms_edit_kb(section), parse_mode='HTML'
    )


# ── O'CHIRISH ──

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("cms:delete:"), state='*')
async def cms_delete_confirm(call: CallbackQuery, state: FSMContext):
    if not await admin_allowed(call.from_user.id, 'content'):
        return
    key = call.data.split("cms:delete:")[1]
    # Xizmat bo'limlarini o'chirib bo'lmaydi
    if key.startswith("svc:"):
        await call.answer("⛔ Bu tizim bo'limi — o'chirib bo'lmaydi. Faqat faol/nofaol qilish mumkin.", show_alert=True)
        return
    section = await db.get_section(key)
    await safe_edit(call,
        f"⚠️ <b>O'chirishni tasdiqlang</b>\n\n"
        f"<code>{key}</code> bo'limi va uning barcha sub-bo'limlari o'chadi!\n\n"
        "Davom etasizmi?",
        reply_markup=confirm_delete_kb(key, section['parent_key'] if section else None),
        parse_mode='HTML'
    )


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("cms:del_confirm:"), state='*')
async def cms_delete_execute(call: CallbackQuery, state: FSMContext):
    if not await admin_allowed(call.from_user.id, 'content'):
        return
    key = call.data.split("cms:del_confirm:")[1]
    section = await db.get_section(key)
    parent_key = section['parent_key'] if section else None
    await db.delete_section(key)
    await call.answer("🗑 O'chirildi")

    if parent_key:
        parent = await db.get_section(parent_key)
        if parent:
            children = await db.get_children(admin=True, parent_key=parent_key)
            kb = cms_section_kb(parent, children)
            await safe_edit(call,
                f"📂 <b>{parent['title_uz']}</b>\n\nSub-bo'limlar: {len(children)} ta",
                reply_markup=kb, parse_mode='HTML'
            )
        else:
            sections = await db.get_top_sections(admin=True)
            await safe_edit(call,
                "📝 <b>Bo'limlarni boshqarish</b>",
                reply_markup=cms_main_kb(sections), parse_mode='HTML'
            )
    else:
        sections = await db.get_top_sections(admin=True)
        await safe_edit(call,
            "📝 <b>Bo'limlarni boshqarish</b>",
            reply_markup=cms_main_kb(sections), parse_mode='HTML'
        )


# ── TAHRIRLASH (edit) ──

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("cms:edit:"), state='*')
async def cms_edit_start(call: CallbackQuery, state: FSMContext):
    if not await admin_allowed(call.from_user.id, 'content'):
        return
    parts = call.data.split(":")  # cms:edit:field:key
    field = parts[2]
    key = ":".join(parts[3:])

    await state.update_data(edit_field=field, edit_key=key)

    labels = {
        'text_uz': "🇺🇿 Yangi matn (UZ) yozing:",
        'text_ru': "🇷🇺 Yangi matn (RU) yozing:",
        'title_uz': "🇺🇿 Yangi sarlavha (UZ) yozing:",
        'title_ru': "🇷🇺 Yangi sarlavha (RU) yozing:",
        'image': "🖼 Rasm yuboring (foto yuklang) yoki fayl nomini yozing:",
    }

    state_map = {
        'text_uz': AdminCMSStates.edit_text_uz,
        'text_ru': AdminCMSStates.edit_text_ru,
        'title_uz': AdminCMSStates.edit_title_uz,
        'title_ru': AdminCMSStates.edit_title_ru,
        'image': AdminCMSStates.edit_image,
    }

    section = await db.get_section(key)
    back_cb = f"cms:open:{section['parent_key']}" if section and section['parent_key'] else "cms:main"

    await safe_edit(call,
        f"{labels.get(field, 'Yangi qiymat yozing:')}\n\n"
        f"<i>Hozirgi: {(section.get(field) or '—')[:200] if section else '—'}</i>",
        reply_markup=cancel_kb(f"cms:open:{key}"),
        parse_mode='HTML'
    )
    await state_map[field].set()


@dp.message_handler(state=[
    AdminCMSStates.edit_text_uz, AdminCMSStates.edit_text_ru,
    AdminCMSStates.edit_title_uz, AdminCMSStates.edit_title_ru,
])
async def cms_edit_save(msg: Message, state: FSMContext):
    if not await admin_allowed(msg.from_user.id, 'content'):
        return
    data = await state.get_data()
    field = data.get('edit_field')
    key = data.get('edit_key')
    await state.finish()

    if not field or not key:
        await msg.answer("❌ Xato. Qaytadan urinib ko'ring.")
        return

    await db.update_section_field(key, field, msg.text)
    section = await db.get_section(key)

    await msg.answer(
        f"✅ <b>Saqlandi!</b>\n\n{section_info_text(section)}",
        reply_markup=cms_edit_kb(section), parse_mode='HTML'
    )


# ── RASM YUKLASH (photo yoki fayl nomi) ──

@dp.message_handler(state=AdminCMSStates.edit_image, content_types=['photo', 'text'])
async def cms_edit_image_save(msg: Message, state: FSMContext):
    if not await admin_allowed(msg.from_user.id, 'content'):
        return
    data = await state.get_data()
    key = data.get('edit_key')
    await state.finish()

    if not key:
        await msg.answer("❌ Xato.")
        return

    if msg.photo:
        photo = msg.photo[-1]
        try:
            # Rasmni Storage kanaliga yuborish
            sent = await bot.send_photo(
                chat_id=STORAGE_CHANNEL,
                photo=photo.file_id,
                caption=f"#cms_image #{key.replace(':', '_')}"
            )
            file_id = sent.photo[-1].file_id
            message_id = sent.message_id
            # Format: file_id|channel_id|message_id
            image_value = f"{file_id}|{STORAGE_CHANNEL}|{message_id}"
        except Exception as e:
            await msg.answer(f"❌ Kanalga yuborishda xato: {e}")
            return
    else:
        image_value = msg.text.strip()

    await db.update_section_field(key, 'image', image_value)
    section = await db.get_section(key)

    await msg.answer(
        f"✅ <b>Rasm saqlandi:</b> <code>{image_value}</code>\n\n{section_info_text(section)}",
        reply_markup=cms_edit_kb(section), parse_mode='HTML'
    )


# ── YANGI BO'LIM QO'SHISH ──

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("cms:add:"), state='*')
async def cms_add_start(call: CallbackQuery, state: FSMContext):
    if not await admin_allowed(call.from_user.id, 'content'):
        return
    raw = call.data.split("cms:add:")[1]
    parent_key = None if raw == "ROOT" else raw

    await state.update_data(new_parent=parent_key)
    await safe_edit(call,
        "➕ <b>Yangi bo'lim qo'shish</b>\n\n"
        "Bo'lim uchun <b>kalit so'z</b> (key) yozing.\n"
        "<i>Masalan: about:new_section yoki stat:new</i>\n"
        "<i>Faqat lotin harflari, raqamlar va ':' belgisi!</i>",
        reply_markup=cancel_kb("cms:main"),
        parse_mode='HTML'
    )
    await AdminCMSStates.add_key.set()


@dp.message_handler(state=AdminCMSStates.add_key)
async def cms_add_key(msg: Message, state: FSMContext):
    if not await admin_allowed(msg.from_user.id, 'content'):
        return
    key = msg.text.strip().lower().replace(" ", "_")
    existing = await db.get_section(key)
    if existing:
        await msg.answer(
            f"❌ <code>{key}</code> allaqachon mavjud. Boshqa kalit yozing:",
            parse_mode='HTML'
        )
        return
    await state.update_data(new_key=key)
    await msg.answer("🇺🇿 Sarlavha (UZ) yozing:")
    await AdminCMSStates.add_title_uz.set()


@dp.message_handler(state=AdminCMSStates.add_title_uz)
async def cms_add_title_uz(msg: Message, state: FSMContext):
    if not await admin_allowed(msg.from_user.id, 'content'):
        return
    await state.update_data(new_title_uz=msg.text)
    await msg.answer("🇷🇺 Sarlavha (RU) yozing:")
    await AdminCMSStates.add_title_ru.set()


@dp.message_handler(state=AdminCMSStates.add_title_ru)
async def cms_add_title_ru(msg: Message, state: FSMContext):
    if not await admin_allowed(msg.from_user.id, 'content'):
        return
    await state.update_data(new_title_ru=msg.text)
    await msg.answer("🇺🇿 Matn (UZ) yozing. O'tkazib yuborish uchun — yozing:")
    await AdminCMSStates.add_text_uz.set()


@dp.message_handler(state=AdminCMSStates.add_text_uz)
async def cms_add_text_uz(msg: Message, state: FSMContext):
    if not await admin_allowed(msg.from_user.id, 'content'):
        return
    await state.update_data(new_text_uz=msg.text if msg.text != "—" else "")
    await msg.answer("🇷🇺 Matn (RU) yozing. O'tkazib yuborish uchun — yozing:")
    await AdminCMSStates.add_text_ru.set()


@dp.message_handler(state=AdminCMSStates.add_text_ru)
async def cms_add_text_ru(msg: Message, state: FSMContext):
    if not await admin_allowed(msg.from_user.id, 'content'):
        return
    await state.update_data(new_text_ru=msg.text if msg.text != "—" else "")
    await msg.answer("🖼 Rasm yuboring (foto yuklang) yoki o'tkazish uchun — yozing:")
    await AdminCMSStates.add_image.set()


@dp.message_handler(state=AdminCMSStates.add_image, content_types=['photo', 'text'])
async def cms_add_image(msg: Message, state: FSMContext):
    if not await admin_allowed(msg.from_user.id, 'content'):
        return
    data = await state.get_data()
    await state.finish()

    if msg.photo:
        photo = msg.photo[-1]
        try:
            sent = await bot.send_photo(
                chat_id=STORAGE_CHANNEL,
                photo=photo.file_id,
                caption=f"#cms_image #new"
            )
            file_id = sent.photo[-1].file_id
            message_id = sent.message_id
            image = f"{file_id}|{STORAGE_CHANNEL}|{message_id}"
        except Exception as e:
            await msg.answer(f"❌ Kanalga yuborishda xato: {e}")
            return
    else:
        image = msg.text.strip() if msg.text.strip() != "—" else None

    # Tartib raqami: oxirgi + 1
    parent = data.get('new_parent')
    siblings = await db.get_children(admin=True, parent_key=parent) if parent else await db.get_top_sections(admin=True)
    order = (max((s['order_num'] for s in siblings), default=0) + 1)

    result = await db.add_section(
        section_key=data['new_key'],
        parent_key=parent,
        title_uz=data['new_title_uz'],
        title_ru=data['new_title_ru'],
        text_uz=data.get('new_text_uz', ''),
        text_ru=data.get('new_text_ru', ''),
        image=image,
        order_num=order
    )

    if result:
        section = await db.get_section(data['new_key'])
        await msg.answer(
            f"✅ <b>Bo'lim qo'shildi!</b>\n\n{section_info_text(section)}",
            reply_markup=cms_edit_kb(section), parse_mode='HTML'
        )
    else:
        await msg.answer("❌ Qo'shishda xato yuz berdi.")
