import logging

from aiogram.types import CallbackQuery

from loader import dp


@dp.callback_query_handler(state='*')
async def unhandled_callback(call: CallbackQuery):
    """Handleri topilmagan eski yoki noma'lum inline tugmaga javob beradi."""
    logging.warning("UNHANDLED_CALLBACK")
    await call.answer(
        "Bu tugma eskirgan. /admin buyrug'i bilan panelni yangilang.",
        show_alert=True,
    )
