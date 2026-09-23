from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from loader import dp, db
from states.states import AdminAccessStates


async def _superadmin(user_id):
    admin = await db.get_admin(str(user_id))
    return bool(admin and admin['is_superadmin'])


def admins_kb(admins):
    rows = []
    for admin in admins:
        icon = '👑' if admin['is_superadmin'] else ('✅' if admin['is_active'] else '🚫')
        rows.append([InlineKeyboardButton(
            f"{icon} {admin['user_id']}", callback_data=f"admin_access:{admin['user_id']}"
        )])
    rows.append([InlineKeyboardButton("➕ Admin qo‘shish", callback_data="admin_add")])
    rows.append([InlineKeyboardButton("⬅️ Admin panel", callback_data="adm:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_detail_kb(admin):
    user_id = admin['user_id']
    rows = [
        [InlineKeyboardButton(
            f"{'✅' if admin['can_manage_content'] else '🚫'} Kontent",
            callback_data=f"admin_perm:{user_id}:content"
        )],
        [InlineKeyboardButton(
            f"{'✅' if admin['can_manage_documents'] else '🚫'} Hujjatlar",
            callback_data=f"admin_perm:{user_id}:documents"
        )],
        [InlineKeyboardButton(
            f"{'✅' if admin['can_manage_applications'] else '🚫'} Grant arizalari",
            callback_data=f"admin_perm:{user_id}:applications"
        )],
        [InlineKeyboardButton(
            f"{'✅' if admin['can_manage_users'] else '🚫'} Foydalanuvchilar",
            callback_data=f"admin_perm:{user_id}:users"
        )],
        [InlineKeyboardButton("✅ Barcha huquqlar", callback_data=f"admin_all:{user_id}:1")],
        [InlineKeyboardButton("🚫 Barcha huquqlarni o‘chirish", callback_data=f"admin_all:{user_id}:0")],
    ]
    if not admin['is_superadmin']:
        rows.append([InlineKeyboardButton(
            "🚫 Adminni o‘chirish" if admin['is_active'] else "✅ Adminni faollashtirish",
            callback_data=f"admin_perm:{user_id}:active"
        )])
    rows.append([InlineKeyboardButton("⬅️ Adminlar", callback_data="adm:admins")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@dp.callback_query_handler(text='adm:admins', state='*')
async def admin_access_list(call: CallbackQuery, state: FSMContext):
    if not await _superadmin(call.from_user.id):
        await call.answer("Faqat superadmin uchun", show_alert=True)
        return
    await state.finish()
    await call.answer()
    admins = await db.get_all_admins()
    await call.message.edit_text(
        "🛡 <b>Adminlar va huquqlar</b>\n\nAdminni tanlang:",
        reply_markup=admins_kb(admins), parse_mode='HTML'
    )


@dp.callback_query_handler(Text(startswith='admin_access:'), state='*')
async def admin_access_detail(call: CallbackQuery):
    if not await _superadmin(call.from_user.id):
        return
    user_id = call.data.split(':')[1]
    admin = await db.execute("SELECT * FROM bot_admins WHERE user_id=$1", user_id, fetchrow=True)
    if not admin:
        await call.answer("Admin topilmadi", show_alert=True)
        return
    await call.message.edit_text(
        f"🛡 <b>Admin:</b> <code>{user_id}</code>\n"
        f"Holati: {'faol' if admin['is_active'] else 'o‘chirilgan'}",
        reply_markup=admin_detail_kb(admin), parse_mode='HTML'
    )


@dp.callback_query_handler(text='admin_add', state='*')
async def admin_add_start(call: CallbackQuery):
    if not await _superadmin(call.from_user.id):
        return
    await call.message.answer("Yangi adminning Telegram ID raqamini yuboring:")
    await AdminAccessStates.add_admin.set()


@dp.message_handler(state=AdminAccessStates.add_admin)
async def admin_add_save(msg: Message, state: FSMContext):
    if not await _superadmin(msg.from_user.id):
        return
    user_id = msg.text.strip()
    if not user_id.isdigit():
        await msg.answer("❌ Telegram ID faqat raqamlardan iborat bo‘lishi kerak.")
        return
    await state.finish()
    await db.upsert_admin(user_id, str(msg.from_user.id), all_permissions=False)
    await msg.answer(
        f"✅ <code>{user_id}</code> admin sifatida qo‘shildi. Endi unga kerakli huquqlarni yoqing.",
        parse_mode='HTML'
    )


@dp.callback_query_handler(Text(startswith='admin_perm:'), state='*')
async def admin_permission_toggle(call: CallbackQuery):
    if not await _superadmin(call.from_user.id):
        return
    _, user_id, field = call.data.split(':')
    admin = await db.execute("SELECT * FROM bot_admins WHERE user_id=$1", user_id, fetchrow=True)
    if not admin or admin['is_superadmin']:
        await call.answer("Superadmin huquqlarini o‘zgartirib bo‘lmaydi", show_alert=True)
        return
    column_map = {
        'content': 'can_manage_content', 'documents': 'can_manage_documents',
        'applications': 'can_manage_applications', 'users': 'can_manage_users',
        'active': 'is_active'
    }
    await db.set_admin_permission(user_id, field, not bool(admin[column_map[field]]))
    admin = await db.execute("SELECT * FROM bot_admins WHERE user_id=$1", user_id, fetchrow=True)
    await call.answer("Saqlandi")
    await call.message.edit_reply_markup(reply_markup=admin_detail_kb(admin))


@dp.callback_query_handler(Text(startswith='admin_all:'), state='*')
async def admin_all_permissions(call: CallbackQuery):
    if not await _superadmin(call.from_user.id):
        return
    _, user_id, raw_value = call.data.split(':')
    admin = await db.execute("SELECT * FROM bot_admins WHERE user_id=$1", user_id, fetchrow=True)
    if not admin or admin['is_superadmin']:
        await call.answer("Superadmin huquqlarini o‘zgartirib bo‘lmaydi", show_alert=True)
        return
    value = raw_value == '1'
    for field in ('content', 'documents', 'applications', 'users'):
        await db.set_admin_permission(user_id, field, value)
    admin = await db.execute("SELECT * FROM bot_admins WHERE user_id=$1", user_id, fetchrow=True)
    await call.answer("Barcha huquqlar yoqildi" if value else "Barcha huquqlar o‘chirildi")
    await call.message.edit_reply_markup(reply_markup=admin_detail_kb(admin))
