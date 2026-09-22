import logging

from aiogram import types
from aiogram.dispatcher.handler import current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware


class CallbackAuditMiddleware(BaseMiddleware):
    """Qaysi callback handler tanlanganini shaxsiy ma'lumotsiz log qiladi."""

    async def on_process_callback_query(
        self, callback_query: types.CallbackQuery, data: dict
    ):
        handler = current_handler.get()
        logging.info(
            "CALLBACK_HANDLER handler=%s",
            getattr(handler, "__name__", "unhandled"),
        )
