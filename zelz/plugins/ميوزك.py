from telethon import events
from zelz import zedub

CHECK_GROUP_LINK = "https://t.me/music_matri"

# نخزن ايدي الحساب مالك السورس (المالك)
async def get_owner_id():
    me = await zedub.get_me()
    return me.id

@zedub.on(events.NewMessage(pattern=r"^\.ييوت\s+(.*)"))
async def forward_to_group(event):
    owner_id = await get_owner_id()

    # يتأكد انو انت صاحب الحساب
    if event.sender_id != owner_id:
        return

    input_text = event.pattern_match.group(1)

    # نخزن ايدي رسالتك الأصلية
    original_msg_id = event.id
    chat_id = event.chat_id

    # نرسل للقروب
    sent_msg = await l313l.send_message(CHECK_GROUP_LINK, f"ييوت {input_text}")

    replies = {"count": 0}

    @zedub.on(events.NewMessage(chats=CHECK_GROUP_LINK))
    async def reply_handler(reply_event):
        # نتأكد انو الرد فعلاً على رسالتنا
        if reply_event.reply_to_msg_id != sent_msg.id:
            return

        replies["count"] += 1

        if replies["count"] == 1:
            # أول رد نتجاهله
            return
        elif replies["count"] == 2:
            # الرد الثاني
            if reply_event.audio:
                # يرد على رسالتك الأصلية (وين ما كتبت الأمر) + التاغات
                await zedub.send_file(
                    chat_id,
                    reply_event.audio,
                    caption=f"@BDB0B  _  @QU_QUU",
                    reply_to=original_msg_id
                )
            else:
                await zedub.send_message(
                    chat_id,
                    f"❌ ماكو بصمة لـ: {input_text}",
                    reply_to=original_msg_id
                )

            # نشيل الهاندلر بعد ما يشتغل
            zedub.remove_event_handler(reply_handler)
