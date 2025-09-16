# telegraph utils for ZThon
import os
import random
import string
from datetime import datetime

from PIL import Image
from telegraph import Telegraph, exceptions, upload_file
from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl.functions.contacts import UnblockRequest as unblock
from telethon.utils import get_display_name
from urlextract import URLExtract

from ..Config import Config
from ..core.logger import logging
from ..core.managers import edit_delete, edit_or_reply
from ..helpers.functions import delete_conv
from . import BOTLOG, BOTLOG_CHATID, zedub, reply_id

LOGS = logging.getLogger(__name__)

plugin_category = "الخدمات"

extractor = URLExtract()
telegraph = Telegraph()
r = telegraph.create_account(short_name=Config.TELEGRAPH_SHORT_NAME)
auth_url = r["auth_url"]


def resize_image(image):
    im = Image.open(image)
    im.save(image, "PNG")


@zedub.zed_cmd(
    pattern="(ت(ل)?ك(راف)?) ?(m|t|ميديا|نص)(?:\\s|$)([\\s\\S]*)",
    command=("تلكراف", plugin_category),
    info={
        "header": "To get telegraph link.",
        "description": "Reply to text message to paste that text on telegraph you can also pass input along with command \
            So that to customize title of that telegraph and reply to media file to get sharable link of that media(atmost 5mb is supported)",
        "options": {
            "m or media": "To get telegraph link of replied sticker/image/video/gif.",
            "t or text": "To get telegraph link of replied text you can use custom title.",
        },
        "usage": [
            "{tr}tgm",
            "{tr}tgt <title(optional)>",
            "{tr}telegraph media",
            "{tr}telegraph text <title(optional)>",
        ],
    },
)  # sourcery no-metrics
async def _(event):
    "To get telegraph link."
    zedevent = await edit_or_reply(event, "** ⪼ جاري المعالجه ༗...**")
    if BOTLOG:
        await event.client.send_message(
            BOTLOG_CHATID,
            f"**⎉╎ تم إنشاء حساب تيليجـراف جديد {auth_url} للدورة الحالية‌‌** \n**⎉╎ لا تعطي عنوان الرابـط هـذا لأي شـخص**",
        )
    optional_title = event.pattern_match.group(5)
    if not event.reply_to_msg_id:
        return await zedevent.edit(
            "`Reply to a message to get a permanent telegra.ph link.`",
        )

    start = datetime.now()
    r_message = await event.get_reply_message()
    input_str = (event.pattern_match.group(4)).strip()
    if input_str in ["ميديا", "m"]:
        downloaded_file_name = await event.client.download_media(
            r_message, Config.TEMP_DIR
        )
        await zedevent.edit(f"** ⪼ تم تحميل** {downloaded_file_name} **.. بنجـاح**")
        if downloaded_file_name.endswith((".webp")):
            resize_image(downloaded_file_name)
        try:
            media_urls = upload_file(downloaded_file_name)
        except exceptions.TelegraphException as exc:
            await zedevent.edit(f"**- خطـأ : **\n`{exc}`")
            os.remove(downloaded_file_name)
        else:
            end = datetime.now()
            ms = (end - start).seconds
            os.remove(downloaded_file_name)
            await zedevent.edit(
                f"**⎉╎الــرابـط : ** [اضغــط هنـــا](https://graph.org{media_urls[0]})\
                    \n**⎉╎الـوقـت : **`{ms} seconds.`",
                link_preview=True,
            )
    elif input_str in ["نص", "t"]:
        user_object = await event.client.get_entity(r_message.sender_id)
        title_of_page = get_display_name(user_object)
        # apparently, all Users do not have last_name field
        if optional_title:
            title_of_page = optional_title
        page_content = r_message.message
        if r_message.media:
            if page_content != "":
                title_of_page = page_content
            downloaded_file_name = await event.client.download_media(
                r_message, Config.TEMP_DIR
            )
            m_list = None
            with open(downloaded_file_name, "rb") as fd:
                m_list = fd.readlines()
            for m in m_list:
                page_content += m.decode("UTF-8") + "\n"
            os.remove(downloaded_file_name)
        page_content = page_content.replace("\n", "<br>")
        try:
            response = telegraph.create_page(title_of_page, html_content=page_content)
        except Exception as e:
            LOGS.info(e)
            title_of_page = "".join(
                random.choice(list(string.ascii_lowercase + string.ascii_uppercase))
                for _ in range(16)
            )
            response = telegraph.create_page(title_of_page, html_content=page_content)
        end = datetime.now()
        ms = (end - start).seconds
        zed = f"https://telegra.ph/{response['path']}"
        await zedevent.edit(
            f"**link : ** [telegraph]({zed})\
                 \n**Time Taken : **`{ms} seconds.`",
            link_preview=True,
        )


@zedub.zed_cmd(
    pattern="ctg(?: |$)([\\s\\S]*)",
    command=("ctg", plugin_category),
    info={
        "header": "Reply to link To get link preview using telegrah.s.",
        "usage": "{tr}ctg <reply/text>",
    },
)
async def ctg(event):
    "To get link preview"
    input_str = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    reply_to_id = await reply_id(event)
    if not input_str and reply:
        input_str = reply.text
    if not input_str:
        return await edit_delete(event, "**ಠ∀ಠ Give me link to search..**", 20)
    urls = extractor.find_urls(input_str)
    if not urls:
        return await edit_delete(event, "**There no link to search in the text..**", 20)
    chat = "@chotamreaderbot"
    zedevent = await edit_or_reply(event, "```Processing...```")
    async with event.client.conversation(chat) as conv:
        try:
            msg_flag = await conv.send_message(urls[0])
        except YouBlockedUserError:
            await edit_or_reply(
                zedevent, "**Error:** Trying to unblock & retry, wait a sec..."
            )
            await zedub(unblock("chotamreaderbot"))
            msg_flag = await conv.send_message(urls[0])
        response = await conv.get_response()
        await event.client.send_read_acknowledge(conv.chat_id)
        if response.text.startswith(""):
            await edit_or_reply(zedevent, "Am I Dumb Or Am I Dumb?")
        else:
            await zedevent.delete()
            await event.client.send_message(
                event.chat_id, response, reply_to=reply_to_id, link_preview=True
            )
        await delete_conv(event, chat, msg_flag)








import io
import sys
import traceback

from . import zedub

from ..helpers.utils import _format
from . import *


@zedub.zed_cmd(pattern="امر التجربه")
async def hi(event):
    await edit_or_reply(
        event,
        "**[ᯓ 𝙈𝙖𝙏𝙍𝙞𝙭 ⌁ 𝗨𝘀𝗲𝗿𝗯𝗼𝘁 - تنفيــذ الاكــواد](t.me/veevvw)\n⋆─┄─┄─┄──┄─┄─┄─⋆**\n\n الامر: `.تجربه` + كود برمجي\n- يقوم بتشغيل الكود و أظهار النتيجة",
        link_preview=False,
    )


@zedub.zed_cmd(pattern="تجربه(?:\\s|$)([\\s\\S]*)")
async def _(event):
    cmd = "".join(event.message.message.split(maxsplit=1)[1:])
    if not cmd:
        return await edit_delete(event, "**- ادخـل الكـود مع الامــر كالتالـي**\n**- (.تجربه + الكـود البرمجـي)**")
    cmd = (
        cmd.replace("sendmessage", "send_message")
        .replace("sendfile", "send_file")
        .replace("editmessage", "edit_message")
    )
    zedthon = await edit_or_reply(event, "**- جار تنفيـذ الكـود .. انتظـر**")
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    redirected_error = sys.stderr = io.StringIO()
    stdout, stderr, exc = None, None, None
    try:
        await aexec(cmd, event)
    except Exception:
        exc = traceback.format_exc()
    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    evaluation = ""
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = "Success"
    final_output = (
        f"**⎉╎الكــود : **\n```{cmd}``` \n\n**⎉╎النتيجـة : **\n```{evaluation}``` \n"
    )
    await edit_or_reply(
        zedthon,
        text=final_output,
        aslink=True,
        linktext=f"**⎉╎الكــود : **\n```{cmd}``` \n\n**⎉╎النتيجـة : **\n",
    )
    if BOTLOG:
        await event.client.send_message(
            BOTLOG_CHATID, f"**⎉╎تم تشغيـل وتجـربـة امـر {cmd} .. بنجـاح**"
        )


async def aexec(code, smessatatus):
    message = event = smessatatus
    p = lambda _x: print(_format.yaml_format(_x))
    reply = await event.get_reply_message()
    exec(
        (
            "async def __aexec(message, event , reply, client, p, chat): "
            + "".join(f"\n {l}" for l in code.split("\n"))
        )
    )

    return await locals()["__aexec"](
        message, event, reply, message.client, p, message.chat_id
    )
