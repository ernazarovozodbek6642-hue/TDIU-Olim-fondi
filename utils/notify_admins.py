import logging

from aiogram import Dispatcher
from aiogram.types import ReplyKeyboardRemove

from data.config import ADMINS


async def on_startup_notify(dp: Dispatcher):
    for admin in ADMINS:
        # Telegram user ID musbat son bo'ladi. Guruh/kanal IDlarini adminlarga
        # startup xabari sifatida yuborish ChatNotFound xatosini keltirar edi.
        if not str(admin).isdigit() or int(admin) <= 0:
            logging.warning("Skipping non-user ADMINS entry during startup notification")
            continue
        try:
            await dp.bot.send_message(admin, "Bot ishga tushdi", reply_markup=ReplyKeyboardRemove())

        except Exception as err:
            logging.exception("Could not notify an admin: %s", err)
