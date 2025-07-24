import json
import os
from telethon.tl import functions

from .. import zedub
from ..Config import Config
from ..core.managers import edit_delete, edit_or_reply
from ..utils.tools import create_supergroup

from telethon import events
from telethon.utils import get_display_name
from Tepthon import zedub
from . import zedub  

TRACK_FILE = "tracked_users.json"  
LOG_CHAT_ID = -1002538233107        


if os.path.exists(TRACK_FILE):
    with open(TRACK_FILE, "r") as f:
        tracked_users = json.load(f)
else:
    tracked_users = []

def save_tracked():
    with open(TRACK_FILE, "w") as f:
        json.dump(tracked_users, f)

@zedub.zed_cmd(pattern=r"^\.تتبع(?: |$)(.*)", command=("تتبع", "التتبع"))
async def start_tracking(event):
    await event.delete()  
    input_arg = event.pattern_match.group(1).strip()

    
    if event.is_reply:
        reply = await event.get_reply_message()
        user = await event.client.get_entity(reply.sender_id)
    elif input_arg:
        try:
            user = await event.client.get_entity(input_arg)
        except Exception:
            await event.reply("لم أتمكن من العثور على المستخدم.")
            return
    else:
        await event.reply("يرجى الرد على رسالة الشخص أو كتابة يوزره/آيده بعد الأمر.")
        return

    user_id = user.id
    if user_id in tracked_users:
        await event.reply(f"المستخدم [{get_display_name(user)}](tg://user?id={user_id}) مُتابع بالفعل.", parse_mode="md")
    else:
        tracked_users.append(user_id)
        save_tracked()
        await event.reply(f"تم بدء تتبع المستخدم [{get_display_name(user)}](tg://user?id={user_id}).", parse_mode="md")

@zedub.zed_cmd(pattern=r"^\.الغاءتتبع(?: |$)(.*)", command=("الغاءتتبع", "إلغاءتتبع"))
async def stop_tracking(event):
    await event.delete() 
    input_arg = event.pattern_match.group(1).strip()

    if event.is_reply:
        reply = await event.get_reply_message()
        user = await event.client.get_entity(reply.sender_id)
    elif input_arg:
        try:
            user = await event.client.get_entity(input_arg)
        except Exception:
            await event.reply("لم أتمكن من العثور على المستخدم.")
            return
    else:
        await event.reply("يرجى الرد على رسالة الشخص أو كتابة يوزره/آيده بعد الأمر.")
        return

    user_id = user.id
    if user_id not in tracked_users:
        await event.reply(f"المستخدم [{get_display_name(user)}](tg://user?id={user_id}) غير متابع أصلاً.", parse_mode="md")
    else:
        tracked_users.remove(user_id)
        save_tracked()
        await event.reply(f"تم إلغاء تتبع المستخدم [{get_display_name(user)}](tg://user?id={user_id}).", parse_mode="md")

@zedub.zed_handler(events.NewMessage(incoming=True))
async def track_messages(event):
    if event.sender_id not in tracked_users:
        return

    sender = await event.get_sender()
    chats = await event.client.get_dialogs()
    common_chats = []
    for chat in chats:
        try:
            participants = await event.client.get_participants(chat)
            if sender.id in [p.id for p in participants]:
                common_chats.append(chat)
        except Exception:
            continue

    if event.chat_id not in [chat.id for chat in common_chats]:
        return

    try:
        chat = await event.get_chat()
        user_name = get_display_name(sender)

        if event.is_channel or event.is_group:
            if hasattr(event.chat, 'username') and event.chat.username:
                message_link = f"https://t.me/{event.chat.username}/{event.id}"
            else:
                message_link = "(لا يمكن توليد رابط)"
        else:
            message_link = "(دردشة خاصة)"

        msg = f"""
🔔 <b>رسالة جديدة من المستخدم المتتبع</b>

<b>الاسم:</b> {user_name}
<b>الايدي:</b> <code>{sender.id}</code>
<b>في المجموعة:</b> {chat.title if hasattr(chat, 'title') else 'محادثة خاصة'}
<b>رابط الرسالة:</b> {message_link}
        """

        await event.client.send_message(
            LOG_CHAT_ID,
            msg,
            parse_mode="html"
        )

    except Exception as e:
        print(f"خطأ في التتبع: {e}")
