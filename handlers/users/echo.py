from aiogram import types
from aiogram.dispatcher import FSMContext
from loader import dp, db
from handlers.admin.admin_users import route_user_message_to_admin
from handlers.users.start import start


# Echo bot
@dp.message_handler(state=None)
async def bot_echo(message: types.Message, state: FSMContext):
    # Agar foydalanuvchi aktiv chat sessiyasida bo'lsa — adminga yo'naltir
    routed = await route_user_message_to_admin(message)
    if routed:
        return
    # Aks holda oddiy start
    await start(msg=message, state=state)
