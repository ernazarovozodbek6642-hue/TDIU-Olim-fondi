from aiogram import Dispatcher

from loader import dp
from .callback_audit import CallbackAuditMiddleware
from .throttling import ThrottlingMiddleware


if __name__ == "middlewares":
    dp.middleware.setup(CallbackAuditMiddleware())
    dp.middleware.setup(ThrottlingMiddleware())
