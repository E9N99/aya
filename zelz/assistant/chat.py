import openai
import asyncio
import json
import os
from telethon import events
from gtts import gTTS
import re
import random
from collections import defaultdict
from datetime import datetime
from typing import Optional, Union

from telethon import Button, events
from telethon.errors import UserIsBlockedError
from telethon.events import CallbackQuery, StopPropagation
from telethon.utils import get_display_name

from . import Config, zedub

from ..core import check_owner, pool
from ..core.logger import logging
from ..core.session import tgbot
from ..helpers import reply_id
from ..helpers.utils import _format
from ..sql_helper.bot_blacklists import check_is_black_list
from ..sql_helper.bot_pms_sql import (
    add_user_to_db,
    get_user_id,
    get_user_logging,
    get_user_reply,
)
from ..sql_helper.bot_starters import add_starter_to_db, get_starter_details
from ..sql_helper.globals import delgvar, gvarstatus
from . import BOTLOG, BOTLOG_CHATID
from .botmanagers import ban_user_from_bot




from openai import OpenAI

from . import Config, zedub  # نفس طريقة مشروعك

# ===== إعدادات البوت =====
botusername = Config.TG_BOT_USERNAME

# ===== إعدادات OpenAI =====
client_ai = OpenAI(api_key="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")

# ===== قاعدة بيانات الجلسات =====
DB_FILE = "chat_sessions.json"
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        sessions = json.load(f)
else:
    sessions = {}

SESSION_TIMEOUT = 300  # 5 دقائق
DEFAULT_MOOD = "رسمي"
DEFAULT_PERSONA = "مساعد AI"

def save_sessions():
    with open(DB_FILE, "w") as f:
        json.dump(sessions, f)

async def end_session(user_id, event=None):
    if str(user_id) in sessions:
        task = sessions[str(user_id)].get("task")
        if task:
            task.cancel()
        del sessions[str(user_id)]
        save_sessions()
        if event:
            await event.reply("✅ تم إنهاء الجلسة.")

# ===== فتح جلسة جديدة =====
@zedub.bot_cmd(
    pattern=f"^/chat({botusername})?([\\s]+)?$",
    incoming=True,
    func=lambda e: e.is_private,
)
async def start_chat(event):
    user_id = str(event.sender_id)
    sessions[user_id] = {
        "messages": [],
        "mood": DEFAULT_MOOD,
        "persona": DEFAULT_PERSONA,
        "task": None
    }
    save_sessions()
    await event.reply(
        "🔮 هلا VIP! فتحتلك جلسة محادثة AI.\n"
        "اكتب أي شي وراح أجاوبك.\n\n"
        "استخدم:\n"
        "/end → إنهاء الجلسة\n"
        "/reset → مسح المحادثة\n"
        "/mood [وصف] → تغيير أسلوب الرد\n"
        "/persona [اسم الشخصية] → اختيار شخصية AI\n"
        "/history → استرجاع آخر المحادثات"
    )

    async def session_timer():
        await asyncio.sleep(SESSION_TIMEOUT)
        if user_id in sessions:
            await event.reply("⏰ انتهت الجلسة بسبب عدم النشاط.")
            await end_session(user_id)

    sessions[user_id]["task"] = asyncio.create_task(session_timer())

# ===== إنهاء الجلسة =====
@zedub.bot_cmd(pattern="^/end$", incoming=True)
async def end_chat(event):
    user_id = str(event.sender_id)
    await end_session(user_id, event)

# ===== إعادة ضبط المحادثة =====
@zedub.bot_cmd(pattern="^/reset$", incoming=True)
async def reset_chat(event):
    user_id = str(event.sender_id)
    if user_id in sessions:
        sessions[user_id]["messages"] = []
        save_sessions()
        await event.reply("♻️ تم مسح المحادثة والبدء من جديد.")
    else:
        await event.reply("ماكو جلسة مفتوحة.")

# ===== تغيير Mood =====
@zedub.bot_cmd(pattern="^/mood (.+)", incoming=True)
async def change_mood(event):
    user_id = str(event.sender_id)
    if user_id in sessions:
        mood = event.pattern_match.group(1)
        sessions[user_id]["mood"] = mood
        save_sessions()
        await event.reply(f"✨ تم تغيير أسلوب الرد إلى: {mood}")
    else:
        await event.reply("ماكو جلسة مفتوحة.")

# ===== تغيير Persona =====
@zedub.bot_cmd(pattern="^/persona (.+)", incoming=True)
async def change_persona(event):
    user_id = str(event.sender_id)
    if user_id in sessions:
        persona = event.pattern_match.group(1)
        sessions[user_id]["persona"] = persona
        save_sessions()
        await event.reply(f"🎭 تم اختيار شخصية AI: {persona}")
    else:
        await event.reply("ماكو جلسة مفتوحة.")

# ===== عرض التاريخ =====
@zedub.bot_cmd(pattern="^/history$", incoming=True)
async def show_history(event):
    user_id = str(event.sender_id)
    if user_id in sessions:
        messages = sessions[user_id]["messages"]
        if not messages:
            await event.reply("📜 لا توجد محادثات سابقة.")
        else:
            text = "\n".join([f"{m['role']}: {m['content']}" for m in messages[-10:]])
            await event.reply(f"📜 آخر 10 رسائل:\n{text}")
    else:
        await event.reply("ماكو جلسة مفتوحة.")

# ===== الرد بالذكاء الاصطناعي =====
@zedub.bot_cmd(incoming=True)
async def chat_ai(event):
    user_id = str(event.sender_id)
    text = event.raw_text

    if text.startswith("/"):
        return

    if user_id in sessions:
        # إعادة تشغيل التايمر
        if sessions[user_id]["task"]:
            sessions[user_id]["task"].cancel()
        async def session_timer():
            await asyncio.sleep(SESSION_TIMEOUT)
            if user_id in sessions:
                await event.reply("⏰ انتهت الجلسة بسبب عدم النشاط.")
                await end_session(user_id)
        sessions[user_id]["task"] = asyncio.create_task(session_timer())

        # إضافة الرسالة للسياق
        sessions[user_id]["messages"].append({"role": "user", "content": text})

        # إعداد النظام لMood وPersona
        system_prompt = f"أنت {sessions[user_id]['persona']}، اكتب بأسلوب: {sessions[user_id]['mood']}"
        messages_for_ai = [{"role": "system", "content": system_prompt}] + sessions[user_id]["messages"]

        try:
            response = client_ai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages_for_ai
            )
            reply_text = response.choices[0].message.content
            await event.reply(reply_text)

            sessions[user_id]["messages"].append({"role": "assistant", "content": reply_text})
            save_sessions()

            # تحويل الرد لصوت TTS (اختياري)
            tts = gTTS(text=reply_text, lang='ar')
            tts.save("reply.mp3")
            await event.reply(file="reply.mp3")
            os.remove("reply.mp3")

        except Exception as e:
            await event.reply(f"⚠️ صار خطأ: {str(e)}")
