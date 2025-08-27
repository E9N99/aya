import json
import math
import os
import aiohttp
import requests
import random
import re
import time
from uuid import uuid4
import sys
import asyncio
from validators.url import url
from subprocess import run as runapp
from datetime import datetime
from pySmartDL import SmartDL
from pathlib import Path
from platform import python_version
from telethon import Button, functions, events, types, custom
from telethon.errors import QueryIdInvalidError
from telethon.events import CallbackQuery, InlineQuery
from telethon.utils import get_display_name
from telethon.tl.types import InputMessagesFilterDocument, MessageEntityMentionName
from telethon.tl.functions.photos import GetUserPhotosRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import BotInlineResult, InputBotInlineMessageMediaAuto, DocumentAttributeImageSize, InputWebDocument, InputBotInlineResult
from telethon.tl.functions.messages import SetInlineBotResultsRequest

from . import zedub
from ..Config import Config
from ..helpers.functions import rand_key
from ..core.logger import logging
from ..core.managers import edit_delete, edit_or_reply
from ..sql_helper.globals import addgvar, delgvar, gvarstatus
from ..helpers.utils import reply_id, _format
from . import media_type, progress
from ..utils import Zed_Dev, load_module, remove_plugin
from ..sql_helper.global_collection import add_to_collectionlist, del_keyword_collectionlist, get_collectionlist_items
from . import SUDO_LIST, edit_delete, edit_or_reply, reply_id, BOTLOG, BOTLOG_CHATID, HEROKU_APP, mention

import traceback
from telethon import Button
from .. import zedub
from ..sql_helper.globals import addgvar, delgvar, gvarstatus
from ..core.managers import edit_or_reply

Zel_Uid = zedub.uid
Zed_Dev = [7291869416]  # ضع هنا ID مطورك إذا تريد

async def get_user_from_event(event):
    """تجيب الشخص المستهدف سواء بالرد أو @username"""
    try:
        if event.reply_to_msg_id:
            replied = await event.get_reply_message()
            return await event.client.get_entity(replied.sender_id)
        user = event.pattern_match.group(1)
        if user.isnumeric():
            user = int(user)
        return await event.client.get_entity(user)
    except Exception:
        return None

async def run_hamsa_command(event):
    try:
        # تحقق VIP أو مطور
        if gvarstatus("ZThon_Vip") is None and Zel_Uid not in Zed_Dev:
            return await edit_or_reply(event,
                "**⎉╎عذراً .. هذا الامر VIP فقط**")

        # جلب المستخدم المستهدف
        target_user = await get_user_from_event(event)
        if not target_user:
            return await edit_or_reply(event, "**⎉╎حدد الشخص بالرد أو باليوزر**")

        # حفظ معلومات مؤقتة
        delgvar("hmsa_id")
        delgvar("hmsa_name")
        delgvar("hmsa_user")
        addgvar("hmsa_id", str(target_user.id))
        addgvar("hmsa_name", target_user.first_name or "Unknown")
        addgvar("hmsa_user", f"@{target_user.username}" if target_user.username else "None")

        # إنشاء زر Inline لفتح البوت المساعد
        btns = [
            [Button.switch_inline(
                "💌 أرسل همسة",
                query=f"secret {gvarstatus('hmsa_id')}",
                same_peer=True
            )]
        ]

        # إرسال InlineQuery للبوت المساعد
        response = await zedub.inline_query(Config.TG_BOT_USERNAME, "zelzal")
        await response[0].click(event.chat_id)
        await event.delete()

    except Exception:
        print("\n❌ خطأ run_hamsa_command:\n", traceback.format_exc())
        await edit_or_reply(event, "❌ صار خطأ، شوف اللوغ للتفاصيل.")

# ربط الأوامر الثلاثة بنفس الدالة
@zedub.zed_cmd(pattern="همسه(?: |$)(.*)")
async def cmd_hamsa1(event):
    await run_hamsa_command(event)

@zedub.zed_cmd(pattern="اهمس(?: |$)(.*)")
async def cmd_hamsa2(event):
    await run_hamsa_command(event)

@zedub.zed_cmd(pattern="همسة(?: |$)(.*)")
async def cmd_hamsa3(event):
    await run_hamsa_command(event)
