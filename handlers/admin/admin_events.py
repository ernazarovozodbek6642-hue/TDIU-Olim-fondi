from aiogram.types import CallbackQuery, Message
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from loader import dp, db, bot
from utils.misc.admin_access import admin_allowed
from states.states import AdminEventStates
from keyboards.inline.admin_kb import (
    event_date_kb, event_time_kb, event_confirm_kb,
    events_list_kb, event_detail_kb, back_to_admin_kb
)
from datetime import datetime
import pytz


@dp.callback_query_handler(text='adm:events', state='*')
async def admin_events(call: CallbackQuery, state: FSMContext):
    if not await admin_allowed(call.from_user.id, 'content'):
        await call.answer("Tadbirlar bo‘limi uchun ruxsat yo‘q", show_alert=True)
        return
    await state.finish()
    await call.answer()
    events = await db.get_all_events()
    if not events:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("➕ Yangi tadbir", callback_data="event:new")],
            [InlineKeyboardButton("⬅️ Ortga", callback_data="adm:main")]
        ])
        await call.message.edit_text("📅 <b>Tadbirlar</b>\n\nHozircha tadbir yo'q.", reply_markup=kb, parse_mode='HTML')
    else:
        await call.message.edit_text(
            f"📅 <b>Tadbirlar ({len(events)} ta)</b>",
            reply_markup=events_list_kb(events), parse_mode='HTML'
        )


@dp.callback_query_handler(text='event:new', state='*')
async def new_event_name(call: CallbackQuery, state: FSMContext):
    if not await admin_allowed(call.from_user.id, 'content'):
        return
    await call.message.answer("📅 Tadbir nomini kiriting:")
    await AdminEventStates.name.set()


@dp.message_handler(state=AdminEventStates.name)
async def event_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("📅 Sanani tanlang:", reply_markup=event_date_kb())
    await AdminEventStates.date.set()


@dp.callback_query_handler(Text(startswith='edate:'), state=AdminEventStates.date)
async def event_date(call: CallbackQuery, state: FSMContext):
    date = call.data.split(':')[1]
    await state.update_data(date=date)
    await call.message.edit_text("⏰ Vaqtni tanlang:", reply_markup=event_time_kb())
    await AdminEventStates.time.set()


@dp.callback_query_handler(Text(startswith='etime:'), state=AdminEventStates.time)
async def event_time(call: CallbackQuery, state: FSMContext):
    time = call.data.split(':')[1] + ':' + call.data.split(':')[2]
    await state.update_data(time=time)
    await call.message.answer("📍 Joy nomini yozing yoki lokatsiya yuboring:")
    await AdminEventStates.location.set()


@dp.message_handler(state=AdminEventStates.location)
async def event_location_text(msg: Message, state: FSMContext):
    await state.update_data(location=msg.text, location_lat=None, location_lon=None)
    await msg.answer("📝 Tadbir tavsifini yozing:")
    await AdminEventStates.description.set()


@dp.message_handler(content_types=['location'], state=AdminEventStates.location)
async def event_location_geo(msg: Message, state: FSMContext):
    lat = msg.location.latitude
    lon = msg.location.longitude
    await state.update_data(
        location=f"📍 {lat}, {lon}",
        location_lat=lat, location_lon=lon
    )
    await msg.answer("📝 Tadbir tavsifini yozing:")
    await AdminEventStates.description.set()


@dp.message_handler(state=AdminEventStates.description)
async def event_description(msg: Message, state: FSMContext):
    await state.update_data(description=msg.text)
    data = await state.get_data()
    await msg.answer(
        f"📋 <b>Tasdiqlash</b>\n\n"
        f"📅 Nomi: <b>{data['name']}</b>\n"
        f"🗓 Sana: {data['date']}\n"
        f"⏰ Vaqt: {data['time']}\n"
        f"📍 Joy: {data['location']}\n"
        f"📝 Tavsif: <i>{data['description']}</i>",
        reply_markup=event_confirm_kb(), parse_mode='HTML'
    )
    await AdminEventStates.confirm.set()


@dp.callback_query_handler(text='event:confirm', state=AdminEventStates.confirm)
async def event_confirm(call: CallbackQuery, state: FSMContext):
    if not await admin_allowed(call.from_user.id, 'content'):
        return
    data = await state.get_data()
    edit_event_id = data.get('edit_event_id')
    await state.finish()

    tz = pytz.timezone("Asia/Tashkent")
    now = datetime.now(tz)

    from utils.misc.scheduler import schedule_event_reminders

    if edit_event_id:
        # TAHRIRLASH rejimi
        event = await db.update_event(
            event_id=edit_event_id,
            name=data['name'],
            event_date=data['date'],
            event_time=data['time'],
            location=data['location'],
            description=data['description'],
            location_lat=data.get('location_lat'),
            location_lon=data.get('location_lon')
        )
        await call.message.edit_text("✅ Tadbir yangilandi!", reply_markup=back_to_admin_kb())
        await schedule_event_reminders(event['id'], data['date'], data['time'])
        return

    # YANGI TADBIR yaratish
    event = await db.add_event(
        name=data['name'],
        event_date=data['date'],
        event_time=data['time'],
        location=data['location'],
        description=data['description'],
        created_at=now.replace(tzinfo=None),
        location_lat=data.get('location_lat'),
        location_lon=data.get('location_lon')
    )

    # Barcha ro'yxatdan o'tganlarga xabar
    users = await db.select_registered_users()
    sent = 0
    for user in users:
        try:
            lang = user.get('language', 'uz')
            if lang == 'uz':
                text = (
                    f"📅 <b>Yangi tadbir!</b>\n\n"
                    f"🎯 <b>{data['name']}</b>\n"
                    f"🗓 Sana: {data['date']}\n"
                    f"⏰ Vaqt: {data['time']}\n"
                    f"📍 Joy: {data['location']}\n"
                    f"📝 {data['description']}"
                )
            else:
                text = (
                    f"📅 <b>Новое мероприятие!</b>\n\n"
                    f"🎯 <b>{data['name']}</b>\n"
                    f"🗓 Дата: {data['date']}\n"
                    f"⏰ Время: {data['time']}\n"
                    f"📍 Место: {data['location']}\n"
                    f"📝 {data['description']}"
                )
            await bot.send_message(user['id'], text, parse_mode='HTML')
            if data.get('location_lat') and data.get('location_lon'):
                await bot.send_location(user['id'], data['location_lat'], data['location_lon'])
            sent += 1
        except Exception:
            pass

    # Guruh va kanallarga ham xabar yuborish
    group_text = (
        f"📅 <b>Yangi tadbir!</b>\n\n"
        f"🎯 <b>{data['name']}</b>\n"
        f"🗓 Sana: {data['date']}\n"
        f"⏰ Vaqt: {data['time']}\n"
        f"📍 Joy: {data['location']}\n"
        f"📝 {data['description']}"
    )
    bot_chats = await db.get_bot_chats()
    chat_sent = 0
    for chat in bot_chats:
        try:
            await bot.send_message(chat['chat_id'], group_text, parse_mode='HTML')
            if data.get('location_lat') and data.get('location_lon'):
                await bot.send_location(chat['chat_id'], data['location_lat'], data['location_lon'])
            chat_sent += 1
        except Exception:
            pass

    await call.message.edit_text(
        f"✅ Tadbir saqlandi!\n"
        f"👤 {sent} ta foydalanuvchiga xabar yuborildi.\n"
        f"💬 {chat_sent} ta guruh/kanalga xabar yuborildi.",
        reply_markup=back_to_admin_kb()
    )

    # Eslatmalarni rejalashtirish
    await schedule_event_reminders(event['id'], data['date'], data['time'])


@dp.callback_query_handler(text='event:edit', state=AdminEventStates.confirm)
async def event_edit(call: CallbackQuery, state: FSMContext):
    await call.message.answer("📅 Tadbir nomini qayta kiriting:")
    await AdminEventStates.name.set()


@dp.callback_query_handler(Text(startswith='ev_edit:'), state='*')
async def event_edit_start(call: CallbackQuery, state: FSMContext):
    if not await admin_allowed(call.from_user.id, 'content'):
        return
    event_id = int(call.data.split(':')[1])
    event = await db.get_event_by_id(event_id)
    if not event:
        await call.answer("Topilmadi", show_alert=True)
        return
    await state.update_data(
        edit_event_id=event_id,
        name=event['name'],
        date=event['event_date'],
        time=event['event_time'],
        location=event['location'],
        description=event['description'],
        location_lat=event.get('location_lat'),
        location_lon=event.get('location_lon')
    )
    await call.message.answer(
        f"✏️ Tahrirlash. Yangi nomni kiriting:\n<i>Hozirgi: {event['name']}</i>",
        parse_mode='HTML'
    )
    await AdminEventStates.name.set()


@dp.callback_query_handler(Text(startswith='ev:'), state='*')
async def event_detail(call: CallbackQuery):
    if not await admin_allowed(call.from_user.id, 'content'):
        return
    event_id = int(call.data.split(':')[1])
    event = await db.get_event_by_id(event_id)
    if not event:
        await call.answer("Topilmadi", show_alert=True)
        return
    await call.message.edit_text(
        f"📅 <b>{event['name']}</b>\n\n"
        f"🗓 Sana: {event['event_date']}\n"
        f"⏰ Vaqt: {event['event_time']}\n"
        f"📍 Joy: {event['location']}\n"
        f"📝 {event['description']}",
        reply_markup=event_detail_kb(event_id), parse_mode='HTML'
    )


@dp.callback_query_handler(Text(startswith='ev_del:'), state='*')
async def event_delete(call: CallbackQuery):
    if not await admin_allowed(call.from_user.id, 'content'):
        return
    event_id = int(call.data.split(':')[1])
    await db.delete_event(event_id)
    await call.answer("✅ Tadbir o'chirildi")
    # Ro'yxatga qaytish
    events = await db.get_all_events()
    if not events:
        await call.message.edit_text("📅 Tadbirlar yo'q.", reply_markup=back_to_admin_kb())
    else:
        await call.message.edit_text(
            f"📅 <b>Tadbirlar ({len(events)} ta)</b>",
            reply_markup=events_list_kb(events), parse_mode='HTML'
        )
