from telethon import events
from zelz import zedub, Config
from zelz.utils import LOGS

@zedub.on(events.NewMessage(incoming=True))
async def log_mentions_in_groups(event):
    # نتأكد أن الرسالة من مجموعة وفيها منشن مباشر
    if not event.is_group or not event.message.mentioned:
        return

    # نتأكد من وجود قيمة صحيحة لمجموعة التخزين
    if not hasattr(Config, "PM_LOGGER_GROUP_ID") or Config.PM_LOGGER_GROUP_ID == -100:
        return

    try:
        sender = await event.get_sender()
        chat = await event.get_chat()

        name = getattr(sender, "first_name", "مستخدم")
        msg = event.raw_text or "لا توجد رسالة نصية"
        chat_title = getattr(chat, "title", "مجموعة بدون اسم")
        username = getattr(chat, "username", None)

        # توليد رابط فقط إذا كانت المجموعة عامة
        if username:
            link = f"https://t.me/{username}/{event.id}"
        else:
            link = "🚫 هذه مجموعة خاصة ولا يمكن توليد رابط للرسالة"

        # التنسيق النهائي
        formatted = (
            f"⌔┊#التــاكــات\n"
            f"⌔┊الكــروب: {chat_title}\n"
            f"⌔┊المـرسـل: {name}\n"
            f"⌔┊الرابـط: {link}\n"
            f"⌔┊الرسالة:\n{msg}"
        )

        # إرسال التنسيق إلى مجموعة التخزين
        await event.client.send_message(
            Config.PM_LOGGER_GROUP_ID,
            formatted,
            link_preview=False
        )

        # إعادة توجيه الرسالة الأصلية نفسها
        await event.client.forward_messages(
            Config.PM_LOGGER_GROUP_ID,
            event.message,
            silent=True
        )

    except Exception as e:
        LOGS.warn(f"فشل في تخزين التاك: {e}")