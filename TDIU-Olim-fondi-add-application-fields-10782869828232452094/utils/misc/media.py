"""
Rasm yuborish uchun umumiy helper.

image_value uch xil bo'lishi mumkin:
  1. Fayl nomi:                 'about1.jpg'           (eski usul — local disk)
  2. Faqat file_id:             'AgACAgIAAxkBAAI...'   (eski yangi usul)
  3. Murakkab format:           'file_id|channel_id|message_id'
                                                        (yangi usul — token o'zgarsa
                                                         message_id orqali fallback)

answer_photo_smart() — yuborilgan Message obyektini qaytaradi (yoki None).
Callback back-button da photo_msg_id sifatida saqlash uchun ishlatiladi.
"""

import os
from typing import Optional
from aiogram import Bot
from aiogram.types import InputFile, Message

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
IMAGES_DIR = BASE_DIR / 'images'


def is_file_id(value: str) -> bool:
    """
    Fayl nomi (.jpg/.png kengaytmali, qisqa) vs Telegram ma'lumotini farqlaydi.
    Murakkab format 'file_id|channel_id|message_id' ham True qaytaradi.
    """
    if not value:
        return False
    if '.' in value and len(value) < 100:
        return False  # fayl nomi
    return len(value) > 30


def parse_image_value(value: str):
    """
    image_value ni tahlil qiladi.

    Qaytaradi: (file_id, channel_id, message_id)
      - Oddiy file_id:   (file_id, None, None)
      - Murakkab format: (file_id, channel_id, message_id)
      - Fayl nomi:       (None, None, None)
    """
    if not value:
        return None, None, None

    if not is_file_id(value):
        return None, None, None  # fayl nomi

    if '|' in value:
        parts = value.split('|', 2)
        if len(parts) == 3:
            fid, cid, mid = parts
            try:
                return fid, cid, int(mid)
            except ValueError:
                pass
        return value, None, None

    return value, None, None


async def answer_photo_smart(target, image_value: str, **kwargs) -> Optional[Message]:
    """
    target    — Message yoki CallbackQuery.message
    image_value — file_id, 'file_id|channel|mid', yoki fayl nomi

    Muvaffaqiyatli bo'lsa yuborilgan Message obyektini qaytaradi.
    Yuborilmasa None qaytaradi.

    Qaytarilgan message.message_id ni back-button callback da saqlang:
        photo_msg = await answer_photo_smart(msg, image)
        photo_id = photo_msg.message_id if photo_msg else 0
        callback_data=f"back:{lang}:{photo_id}"
    """
    if not image_value:
        return None

    msg: Message = target if isinstance(target, Message) else target.message
    bot: Bot = msg.bot
    chat_id = msg.chat.id

    file_id, channel_id, message_id = parse_image_value(image_value)

    if file_id:
        # 1-urinish: file_id bilan
        try:
            sent = await msg.answer_photo(photo=file_id, **kwargs)
            return sent
        except Exception:
            pass

        # 2-urinish: kanaldan copy (token o'zgarganda kerak bo'ladi)
        if channel_id and message_id:
            try:
                sent = await bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=channel_id,
                    message_id=message_id,
                    **kwargs
                )
                return sent
            except Exception:
                pass

        return None

    # Fayl nomi (eski usul)
    img_path = os.path.join(IMAGES_DIR, image_value)
    if os.path.exists(img_path):
        try:
            sent = await msg.answer_photo(photo=InputFile(img_path), **kwargs)
            return sent
        except Exception:
            pass

    return None
