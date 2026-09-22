from aiogram.types import ChatMemberUpdated
from loader import dp, db


@dp.my_chat_member_handler()
async def on_my_chat_member(update: ChatMemberUpdated):
    """Bot guruh/kanalga admin sifatida qo'shilganda yoki chiqarilganda chaqiriladi."""
    chat = update.chat
    new_status = update.new_chat_member.status
    old_status = update.old_chat_member.status

    # Faqat guruh va kanallarni kuzatamiz
    if chat.type not in ('group', 'supergroup', 'channel'):
        return

    # Bot admin bo'ldi → saqlash
    if new_status == 'administrator':
        try:
            await db.add_bot_chat(
                chat_id=chat.id,
                chat_title=chat.title or '',
                chat_type=chat.type
            )
        except Exception:
            pass

    # Bot admin edi, demote qilindi yoki chiqarildi/kicked → o'chirish
    elif old_status == 'administrator' or new_status in ('kicked', 'left'):
        try:
            await db.remove_bot_chat(chat.id)
        except Exception:
            pass
