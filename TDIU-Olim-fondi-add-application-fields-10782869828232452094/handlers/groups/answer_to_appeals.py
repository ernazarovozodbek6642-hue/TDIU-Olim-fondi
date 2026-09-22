from aiogram import types
from aiogram.types import Message
from loader import dp, bot, db
import re
from datetime import datetime
import pytz


@dp.message_handler(content_types=types.ContentTypes.ANY,
                    chat_type=['group', 'supergroup'])
async def reply_to_appeal(msg: Message):

    # Reply bolishi va bot yuborgan xabarga javob bolishi kerak
    if not msg.reply_to_message or not msg.reply_to_message.from_user.is_bot:
        return

    html = msg.reply_to_message.html_text or ""

    # Extract all <code>...</code> numerical blocks
    codes = re.findall(r'<code>(\d+)</code>', html)
    if not codes:
        return

    # In our messages, User ID is the first code block, and Appeal ID is the second code block (if exists)
    user_id = int(codes[0])
    appeal_id = int(codes[1]) if len(codes) > 1 else None

    # Murojaat matni
    appeal_match = re.search(r'(?:Matn|):\s*<i>(.*?)</i>', html, re.DOTALL)
    appeal_text = appeal_match.group(1) if appeal_match else ""

    # Foydalanuvchiga javob yuborish
    from aiogram.utils import exceptions
    try:
        if msg.text:
            await bot.send_message(
                chat_id=user_id,
                text=(
                    "📬 <b>Murojaatingizga javob keldi!</b>\n\n"
                    + ("<b>Sizning murojaatingiz:</b>\n<i>{}</i>\n\n".format(appeal_text) if appeal_text else "")
                    + "<b>Javob:</b>\n{}".format(msg.text)
                ),
                parse_mode="HTML"
            )
        elif msg.photo:
            await bot.send_photo(
                chat_id=user_id,
                photo=msg.photo[-1].file_id,
                caption="📬 <b>Murojaatingizga javob keldi!</b>\n\n" + (msg.caption or ""),
                parse_mode="HTML"
            )
        elif msg.document:
            await bot.send_document(
                chat_id=user_id,
                document=msg.document.file_id,
                caption="📬 <b>Murojaatingizga javob keldi!</b>\n\n" + (msg.caption or ""),
                parse_mode="HTML"
            )
        elif msg.voice:
            await bot.send_voice(chat_id=user_id, voice=msg.voice.file_id)
        elif msg.sticker:
            await bot.send_sticker(chat_id=user_id, sticker=msg.sticker.file_id)
    except exceptions.TelegramAPIError as e:
        await msg.reply("Telegram API xatosi: {}".format(e))
        return
    except Exception as e:
        await msg.reply("Xabar yuborishda xato: {}".format(e))
        return

    # DB ga saqlash
    if appeal_id:
        tz = pytz.timezone("Asia/Tashkent")
        tashkent_time = datetime.now(tz)
        try:
            await db.add_answer(
                appeal_id=appeal_id,
                answer_text=msg.text or msg.caption or "[media]",
                created_at=tashkent_time.replace(tzinfo=None)
            )
        except Exception:
            pass

    await msg.reply("Javob murojaatchiga yuborildi")
