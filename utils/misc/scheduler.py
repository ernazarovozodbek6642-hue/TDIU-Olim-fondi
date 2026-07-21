from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import pytz

scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")


async def send_event_reminder(event_id: int, remind_field: str):
    from loader import db, bot
    event = await db.get_event_by_id(event_id)
    if not event:
        return

    users = await db.select_registered_users()

    if remind_field == 'remind_1day':
        time_label_uz = "1 kun"
        time_label_ru = "1 день"
    elif remind_field == 'remind_2hours':
        time_label_uz = "2 soat"
        time_label_ru = "2 часа"
    elif remind_field == 'remind_1hour':
        time_label_uz = "1 soat"
        time_label_ru = "1 час"
    else:
        time_label_uz = "10 daqiqa"
        time_label_ru = "10 минут"

    for user in users:
        try:
            lang = user.get('language', 'uz')
            if lang == 'uz':
                text = (
                    f"⏰ <b>Eslatma!</b> {time_label_uz} qoldi!\n\n"
                    f"📅 <b>{event['name']}</b>\n"
                    f"🗓 {event['event_date']} ⏰ {event['event_time']}\n"
                    f"📍 {event['location']}"
                )
            else:
                text = (
                    f"⏰ <b>Напоминание!</b> Осталось {time_label_ru}!\n\n"
                    f"📅 <b>{event['name']}</b>\n"
                    f"🗓 {event['event_date']} ⏰ {event['event_time']}\n"
                    f"📍 {event['location']}"
                )
            await bot.send_message(user['id'], text, parse_mode='HTML')
            if event.get('location_lat') and event.get('location_lon'):
                await bot.send_location(user['id'], event['location_lat'], event['location_lon'])
        except Exception:
            pass

    await db.update_event_reminder(event_id, remind_field)


async def schedule_event_reminders(event_id: int, event_date: str, event_time: str):
    """Tadbir uchun eslatmalarni rejalashtirir."""
    try:
        tz = pytz.timezone("Asia/Tashkent")
        dt = datetime.strptime(f"{event_date} {event_time}", "%d.%m.%Y %H:%M")
        dt = tz.localize(dt)
        now = datetime.now(tz)

        remind_1day = dt - timedelta(days=1)
        remind_2hours = dt - timedelta(hours=2)
        remind_1hour = dt - timedelta(hours=1)
        remind_10min = dt - timedelta(minutes=10)

        if remind_1day > now:
            scheduler.add_job(
                send_event_reminder, 'date', run_date=remind_1day,
                args=[event_id, 'remind_1day'],
                id=f'ev_{event_id}_1day', replace_existing=True
            )
        if remind_2hours > now:
            scheduler.add_job(
                send_event_reminder, 'date', run_date=remind_2hours,
                args=[event_id, 'remind_2hours'],
                id=f'ev_{event_id}_2h', replace_existing=True
            )
        if remind_1hour > now:
            scheduler.add_job(
                send_event_reminder, 'date', run_date=remind_1hour,
                args=[event_id, 'remind_1hour'],
                id=f'ev_{event_id}_1h', replace_existing=True
            )
        if remind_10min > now:
            scheduler.add_job(
                send_event_reminder, 'date', run_date=remind_10min,
                args=[event_id, 'remind_10min'],
                id=f'ev_{event_id}_10m', replace_existing=True
            )
    except Exception as e:
        print(f"[SCHEDULER ERROR] {e}")


async def reschedule_pending_events():
    """Bot qayta ishga tushganda kutilayotgan eslatmalarni qayta rejalashtiradi."""
    from loader import db
    try:
        events = await db.get_all_events()
        tz = pytz.timezone("Asia/Tashkent")
        now = datetime.now(tz)

        for event in events:
            try:
                dt = datetime.strptime(
                    f"{event['event_date']} {event['event_time']}", "%d.%m.%Y %H:%M"
                )
                dt = tz.localize(dt)
                if dt < now:
                    continue
                if not event.get('remind_1day'):
                    await schedule_event_reminders(event['id'], event['event_date'], event['event_time'])
                    continue
                elif not event.get('remind_2hours'):
                    remind_2h = dt - timedelta(hours=2)
                    remind_1h = dt - timedelta(hours=1)
                    remind_10m = dt - timedelta(minutes=10)
                    if remind_2h > now:
                        scheduler.add_job(send_event_reminder, 'date', run_date=remind_2h,
                                          args=[event['id'], 'remind_2hours'],
                                          id=f'ev_{event["id"]}_2h', replace_existing=True)
                    if remind_1h > now:
                        scheduler.add_job(send_event_reminder, 'date', run_date=remind_1h,
                                          args=[event['id'], 'remind_1hour'],
                                          id=f'ev_{event["id"]}_1h', replace_existing=True)
                    if remind_10m > now:
                        scheduler.add_job(send_event_reminder, 'date', run_date=remind_10m,
                                          args=[event['id'], 'remind_10min'],
                                          id=f'ev_{event["id"]}_10m', replace_existing=True)
                elif not event.get('remind_1hour'):
                    remind_1h = dt - timedelta(hours=1)
                    remind_10m = dt - timedelta(minutes=10)
                    if remind_1h > now:
                        scheduler.add_job(send_event_reminder, 'date', run_date=remind_1h,
                                          args=[event['id'], 'remind_1hour'],
                                          id=f'ev_{event["id"]}_1h', replace_existing=True)
                    if remind_10m > now:
                        scheduler.add_job(send_event_reminder, 'date', run_date=remind_10m,
                                          args=[event['id'], 'remind_10min'],
                                          id=f'ev_{event["id"]}_10m', replace_existing=True)
                elif not event.get('remind_10min'):
                    remind_10m = dt - timedelta(minutes=10)
                    if remind_10m > now:
                        scheduler.add_job(send_event_reminder, 'date', run_date=remind_10m,
                                          args=[event['id'], 'remind_10min'],
                                          id=f'ev_{event["id"]}_10m', replace_existing=True)
            except Exception:
                pass
    except Exception as e:
        print(f"[RESCHEDULE ERROR] {e}")
