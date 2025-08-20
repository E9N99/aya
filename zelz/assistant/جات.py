import asyncio
from telethon import events, Button
from telethon.tl.functions.messages import GetHistoryRequest

# تخزين القنوات مؤقتاً
user_sessions = {}

@zedub.on(events.NewMessage(pattern="/chat"))
async def _(event):
    chat_id = event.chat_id
    user_sessions[chat_id] = {"source": None, "target": None}

    buttons = [
        [Button.inline("📥 تحديد القناة الهدف", data="set_source")],
        [Button.inline("📤 تحديد قناتي", data="set_target")],
        [Button.inline("🚀 ابدأ النسخ", data="start_copy")]
    ]
    await event.respond("اختر من القائمة:", buttons=buttons)


@zedub.on(events.CallbackQuery(pattern="set_source"))
async def _(event):
    chat_id = event.chat_id
    await event.respond("ارسل يوزر القناة الهدف (مثال: `@channel_source`)")
    user_sessions[chat_id]["step"] = "source"
    await event.answer()


@zedub.on(events.CallbackQuery(pattern="set_target"))
async def _(event):
    chat_id = event.chat_id
    await event.respond("ارسل يوزر قناتك (مثال: `@channel_target`)")
    user_sessions[chat_id]["step"] = "target"
    await event.answer()


@zedub.on(events.NewMessage)
async def _(event):
    chat_id = event.chat_id
    if chat_id not in user_sessions:
        return

    session = user_sessions[chat_id]
    if "step" not in session:
        return

    if session["step"] == "source":
        session["source"] = event.raw_text.strip()
        await event.reply(f"✅ تم تعيين القناة الهدف: {session['source']}")
        session.pop("step")
    elif session["step"] == "target":
        session["target"] = event.raw_text.strip()
        await event.reply(f"✅ تم تعيين قناتك: {session['target']}")
        session.pop("step")


@zedub.on(events.CallbackQuery(pattern="start_copy"))
async def _(event):
    chat_id = event.chat_id
    session = user_sessions.get(chat_id, {})

    source = session.get("source")
    target = session.get("target")

    if not source or not target:
        await event.respond("⚠️ لازم تحدد القناتين أولاً")
        await event.answer()
        return

    await event.respond(f"⏳ جاري نسخ محتوى {source} إلى {target}...")

    try:
        offset_id = 0
        limit = 100
        total = 0

        while True:
            history = await zedub(GetHistoryRequest(
                peer=source,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                limit=limit,
                max_id=0,
                min_id=0,
                hash=0
            ))

            if not history.messages:
                break

            for msg in history.messages:
                try:
                    if msg.media:
                        await zedub.send_file(target, msg.media, caption=msg.message or "")
                    else:
                        await zedub.send_message(target, msg.message)
                    total += 1
                    await asyncio.sleep(0.5)  # منع الحظر
                except Exception as e:
                    print(f"خطأ عند النسخ: {e}")

            offset_id = history.messages[-1].id

        await event.respond(f"✅ تم نسخ {total} رسالة من {source} إلى {target}")
        user_sessions.pop(chat_id, None)

    except Exception as e:
        await event.respond(f"❌ فشل النسخ: {e}")
