import os
import sys
import logging
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from aiogram import executor

from loader import dp, db
from data import config
import middlewares, filters, handlers
from utils.notify_admins import on_startup_notify
from utils.set_bot_commands import set_default_commands
from utils.misc.scheduler import scheduler, reschedule_pending_events


async def on_startup(dispatcher):
    # Bot faqat long polling rejimida ishlaydi. Avvalgi deploy yoki tashqi
    # servis qoldirgan webhook barcha update/callbacklarni to'sib qo'ymasligi
    # uchun uni startupda ochiq tarzda olib tashlaymiz.
    await dispatcher.bot.delete_webhook(drop_pending_updates=False)
    logging.info("Telegram webhook cleared; polling mode enabled")

    await db.create()
    await set_default_commands(dispatcher)
    await db.create_table_users()
    await db.create_table_sessions()
    await db.create_table_bot_admins()
    await db.seed_config_admins(config.ADMINS)
    await db.create_table_document_permissions()
    await db.create_table_appeals()
    await db.create_table_documents()
    await db.create_table_answers()
    await db.create_table_events()
    await db.create_table_bot_chats()
    await db.create_table_arizalar()
    await db.seed_default_session()
    await db.assign_legacy_records_to_active_session()
    await db.create_table_sections()
    await db.seed_sections_if_empty()
    await db.ensure_service_sections()

    await on_startup_notify(dispatcher)

    # Schedulerni ishga tushirish va kutilayotgan eslatmalarni qayta rejalashtirish
    scheduler.start()
    await reschedule_pending_events()


if __name__ == '__main__':
    executor.start_polling(
        dp,
        on_startup=on_startup,
        reset_webhook=True,
        skip_updates=False,
    )
