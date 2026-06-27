from aiogram import executor

from loader import dp, db
import middlewares, filters, handlers
from utils.notify_admins import on_startup_notify
from utils.set_bot_commands import set_default_commands
from utils.misc.scheduler import scheduler, reschedule_pending_events


async def on_startup(dispatcher):
    await db.create()
    await set_default_commands(dispatcher)
    await db.create_table_users()
    await db.create_table_appeals()
    await db.create_table_documents()
    await db.create_table_answers()
    await db.create_table_events()
    await db.create_table_bot_chats()
    await db.create_table_arizalar()
    await db.create_table_sections()
    await db.seed_sections_if_empty()

    await on_startup_notify(dispatcher)

    # Schedulerni ishga tushirish va kutilayotgan eslatmalarni qayta rejalashtirish
    scheduler.start()
    await reschedule_pending_events()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
