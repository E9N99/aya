import asyncio
import glob
import contextlib
import io
import os
import re
import pathlib
from time import time
import requests
import random
from pathlib import Path

import aiohttp
import aiofiles
import wget
import yt_dlp
from yt_dlp import YoutubeDL
from youtube_search import YoutubeSearch
from ShazamAPI import Shazam
from validators.url import url

from urlextract import URLExtract
from wget import download
from yt_dlp import YoutubeDL
from yt_dlp.utils import (
    ContentTooShortError,
    DownloadError,
    ExtractorError,
    GeoRestrictedError,
    MaxDownloadsReached,
    PostProcessingError,
    UnavailableVideoError,
    XAttrMetadataError,
)

from telethon import events
from telethon.tl import types
from telethon.utils import get_attributes
from telethon.errors.rpcerrorlist import YouBlockedUserError, ChatSendMediaForbiddenError
from telethon.tl.functions.contacts import UnblockRequest as unblock

from ..Config import Config
from ..core import pool
from ..core.logger import logging
from ..core.managers import edit_delete, edit_or_reply
from ..helpers import progress, reply_id
from ..helpers.functions import delete_conv, name_dl, song_dl, video_dl, yt_search
from ..helpers.functions.utube import _mp3Dl, get_yt_video_id, get_ytthumb, ytsearch
from ..helpers.tools import media_type
from ..helpers.utils import _format, reply_id, _zedutils
from . import BOTLOG, BOTLOG_CHATID, zedub

BASE_YT_URL = "https://www.youtube.com/watch?v="
extractor = URLExtract()
LOGS = logging.getLogger(__name__)

plugin_category = "البحث"

# =========================================================== #
#                                                             𝙕𝙏𝙝𝙤𝙣
# =========================================================== #
SONG_SEARCH_STRING = "<b>╮ جـارِ البحث ؏ـن المقطـٓع الصٓوتـي... 🎧♥️╰</b>"
SONG_NOT_FOUND = "<b>⎉╎لـم استطـع ايجـاد المطلـوب .. جرب البحث باستخـدام الامـر (.اغنيه)</b>"
SONG_SENDING_STRING = "<b>╮ جـارِ تحميـل المقطـٓع الصٓوتـي... 🎧♥️╰</b>"
# =========================================================== #
#                                                             𝙕𝙏𝙝𝙤𝙣
# =========================================================== #


def get_cookies_file():
    folder_path = f"{os.getcwd()}/BlBl"
    txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
    if not txt_files:
        raise FileNotFoundError("No .txt files found in the specified folder.")
    cookie_txt_file = random.choice(txt_files)
    return cookie_txt_file


video_opts = {
    "format": "bestvideo+bestaudio/best",  # Download best video and audio and merge
    "keepvideo": True,
    "prefer_ffmpeg": False,
    "geo_bypass": True,
    "outtmpl": "zed_ytv.mp4",
    "merge_output_format": "mp4",  # Merge video and audio into MP4 format
    "quiet": True,
    "no_warnings": True,
    "cookiefile" : get_cookies_file(),
}


async def ytdl_down(event, opts, url):
    ytdl_data = None
    try:
        await event.edit("**╮ ❐ يتـم جلـب البيانـات انتظـر قليلاً ...𓅫╰▬▭ **")
        with YoutubeDL(opts) as ytdl:
            ytdl_data = ytdl.extract_info(url)
    except DownloadError as DE:
        await event.edit(f"`{DE}`")
    except ContentTooShortError:
        await event.edit("**- عذرا هذا المحتوى قصير جدا لتنزيله ⚠️**")
    except GeoRestrictedError:
        await event.edit(
            "**- الفيديو غير متاح من موقعك الجغرافي بسبب القيود الجغرافية التي يفرضها موقع الويب ❕**"
        )
    except MaxDownloadsReached:
        await event.edit("**- تم الوصول إلى الحد الأقصى لعدد التنزيلات ❕**")
    except PostProcessingError:
        await event.edit("**كان هناك خطأ أثناء المعالجة**")
    except UnavailableVideoError:
        await event.edit("**⌔∮عـذرًا .. الوسائط غير متوفـره بالتنسيق المطلـوب**")
    except XAttrMetadataError as XAME:
        await event.edit(f"`{XAME.code}: {XAME.msg}\n{XAME.reason}`")
    except ExtractorError:
        await event.edit("**حدث خطأ أثناء استخراج المعلومات يرجى وضعها بشكل صحيح ⚠️**")
    except Exception as e:
        await event.edit(f"**- خطـأ : **\n__{e}__")
    return ytdl_data


async def fix_attributes(
    path, info_dict: dict, supports_streaming: bool = False, round_message: bool = False
) -> list:
    """Avoid multiple instances of an attribute."""
    new_attributes = []
    video = False
    audio = False

    uploader = info_dict.get("uploader", "Unknown artist")
    duration = int(info_dict.get("duration", 0))
    suffix = path.suffix[1:]
    if supports_streaming and suffix != "mp4":
        supports_streaming = True

    attributes, mime_type = get_attributes(path)
    if suffix == "mp3":
        title = str(info_dict.get("title", info_dict.get("id", "Unknown title")))
        audio = types.DocumentAttributeAudio(
            duration=duration, voice=None, title=title, performer=uploader
        )
    elif suffix == "mp4":
        width = int(info_dict.get("width", 0))
        height = int(info_dict.get("height", 0))
        for attr in attributes:
            if isinstance(attr, types.DocumentAttributeVideo):
                duration = duration or attr.duration
                width = width or attr.w
                height = height or attr.h
                break
        video = types.DocumentAttributeVideo(
            duration=duration,
            w=width,
            h=height,
            round_message=round_message,
            supports_streaming=supports_streaming,
        )

    if audio and isinstance(audio, types.DocumentAttributeAudio):
        new_attributes.append(audio)
    if video and isinstance(video, types.DocumentAttributeVideo):
        new_attributes.append(video)

    new_attributes.extend(
        attr
        for attr in attributes
        if (
            isinstance(attr, types.DocumentAttributeAudio)
            and not audio
            or not isinstance(attr, types.DocumentAttributeAudio)
            and not video
            or not isinstance(attr, types.DocumentAttributeAudio)
            and not isinstance(attr, types.DocumentAttributeVideo)
        )
    )
    return new_attributes, mime_type


@zedub.zed_cmd(pattern="سناب(?: |$)(.*)")
async def download_video(event):
    msg = event.pattern_match.group(1)
    rmsg = await event.get_reply_message()
    if not msg and rmsg:
        msg = rmsg.text
    urls = extractor.find_urls(msg)
    if not urls:
        return await edit_or_reply(event, "**- قـم بادخــال رابـط مع الامـر او بالــرد ع رابـط ليتـم التحميـل**")
    zedevent = await edit_or_reply(event, "**⎉╎جـارِ التحميل انتظر قليلا ▬▭ ...**")
    reply_to_id = await reply_id(event)
    for url in urls:
        ytdl_data = await ytdl_down(zedevent, video_opts, url)
        if ytdl_down is None:
            return
        try:
            f = pathlib.Path("zed_ytv.mp4")
            print(f)
            catthumb = pathlib.Path("zed_ytv.jpg")
            if not os.path.exists(catthumb):
                catthumb = pathlib.Path("zed_ytv.webp")
            if not os.path.exists(catthumb):
                catthumb = None
            await zedevent.edit(
                f"**╮ ❐ جـارِ التحضيـر للـرفع انتظـر ...𓅫╰**:\
                \n**{ytdl_data['title']}**"
            )
            ul = io.open(f, "rb")
            c_time = time()
            attributes, mime_type = await fix_attributes(
                f, ytdl_data, supports_streaming=True
            )
            uploaded = await event.client.fast_upload_file(
                file=ul,
                progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                    progress(
                        d, t, zedevent, c_time, "Upload :", file_name=ytdl_data["title"]
                    )
                ),
            )
            ul.close()
            media = types.InputMediaUploadedDocument(
                file=uploaded,
                mime_type=mime_type,
                attributes=attributes,
            )
            await event.client.send_file(
                event.chat_id,
                file=media,
                reply_to=reply_to_id,
                caption=f'**⎉╎المقطــع :** `{ytdl_data["title"]}`\n**⎉╎الرابـط : {msg}**\n**⎉╎تم  التحميـل .. بنجـاح ✅**"',
                thumb=catthumb,
            )
            os.remove(f)
            if catthumb:
                os.remove(catthumb)
        except TypeError:
            await asyncio.sleep(2)
    await event.delete()


@zedub.zed_cmd(pattern="فيس(?: |$)(.*)")
async def download_video(event):
    msg = event.pattern_match.group(1)
    rmsg = await event.get_reply_message()
    if not msg and rmsg:
        msg = rmsg.text
    urls = extractor.find_urls(msg)
    if not urls:
        return await edit_or_reply(event, "**- قـم بادخــال رابـط مع الامـر او بالــرد ع رابـط ليتـم التحميـل**")
    zedevent = await edit_or_reply(event, "**⎉╎جـارِ التحميل انتظر قليلا ▬▭ ...**")
    reply_to_id = await reply_id(event)
    for url in urls:
        ytdl_data = await ytdl_down(zedevent, video_opts, url)
        if ytdl_down is None:
            return
        try:
            f = pathlib.Path("zed_ytv.mp4")
            print(f)
            catthumb = pathlib.Path("zed_ytv.jpg")
            if not os.path.exists(catthumb):
                catthumb = pathlib.Path("zed_ytv.webp")
            if not os.path.exists(catthumb):
                catthumb = None
            await zedevent.edit(
                f"**╮ ❐ جـارِ التحضيـر للـرفع انتظـر ...𓅫╰**:\
                \n**{ytdl_data['title']}**"
            )
            ul = io.open(f, "rb")
            c_time = time()
            attributes, mime_type = await fix_attributes(
                f, ytdl_data, supports_streaming=True
            )
            uploaded = await event.client.fast_upload_file(
                file=ul,
                progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                    progress(
                        d, t, zedevent, c_time, "Upload :", file_name=ytdl_data["title"]
                    )
                ),
            )
            ul.close()
            media = types.InputMediaUploadedDocument(
                file=uploaded,
                mime_type=mime_type,
                attributes=attributes,
            )
            await event.client.send_file(
                event.chat_id,
                file=media,
                reply_to=reply_to_id,
                caption=f'**⎉╎المقطــع :** `{ytdl_data["title"]}`\n**⎉╎الرابـط : {msg}**\n**⎉╎تم  التحميـل .. بنجـاح ✅**"',
                thumb=catthumb,
            )
            os.remove(f)
            if catthumb:
                os.remove(catthumb)
        except TypeError:
            await asyncio.sleep(2)
    await event.delete()


@zedub.zed_cmd(pattern="بنترست(?: |$)(.*)")
async def download_video(event):
    msg = event.pattern_match.group(1)
    rmsg = await event.get_reply_message()
    if not msg and rmsg:
        msg = rmsg.text
    urls = extractor.find_urls(msg)
    if not urls:
        return await edit_or_reply(event, "**- قـم بادخــال رابـط مع الامـر او بالــرد ع رابـط ليتـم التحميـل**")
    zedevent = await edit_or_reply(event, "**⎉╎جـارِ التحميل انتظر قليلا ▬▭ ...**")
    reply_to_id = await reply_id(event)
    for url in urls:
        ytdl_data = await ytdl_down(zedevent, video_opts, url)
        if ytdl_down is None:
            return
        try:
            f = pathlib.Path("zed_ytv.mp4")
            print(f)
            catthumb = pathlib.Path("zed_ytv.jpg")
            if not os.path.exists(catthumb):
                catthumb = pathlib.Path("zed_ytv.webp")
            if not os.path.exists(catthumb):
                catthumb = None
            await zedevent.edit(
                f"**╮ ❐ جـارِ التحضيـر للـرفع انتظـر ...𓅫╰**:\
                \n**{ytdl_data['title']}**"
            )
            ul = io.open(f, "rb")
            c_time = time()
            attributes, mime_type = await fix_attributes(
                f, ytdl_data, supports_streaming=True
            )
            uploaded = await event.client.fast_upload_file(
                file=ul,
                progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                    progress(
                        d, t, zedevent, c_time, "Upload :", file_name=ytdl_data["title"]
                    )
                ),
            )
            ul.close()
            media = types.InputMediaUploadedDocument(
                file=uploaded,
                mime_type=mime_type,
                attributes=attributes,
            )
            await event.client.send_file(
                event.chat_id,
                file=media,
                reply_to=reply_to_id,
                caption=f'**⎉╎المقطــع :** `{ytdl_data["title"]}`\n**⎉╎الرابـط : {msg}**\n**⎉╎تم  التحميـل .. بنجـاح ✅**"',
                thumb=catthumb,
            )
            os.remove(f)
            if catthumb:
                os.remove(catthumb)
        except TypeError:
            await asyncio.sleep(2)
    await event.delete()


@zedub.zed_cmd(
    pattern="ساوند(?: |$)(.*)",
    command=("ساوند", plugin_category),
    info={
        "header": "تحميـل الاغـاني مـن سـاونـد كـلاود الـخ عـبر الرابـط",
        "مثــال": ["{tr}ساوند بالــرد ع رابــط", "{tr}ساوند + رابــط"],
    },
)
async def download_audio(event):
    """To download audio from YouTube and many other sites."""
    msg = event.pattern_match.group(1)
    rmsg = await event.get_reply_message()
    if not msg and rmsg:
        msg = rmsg.text
    urls = extractor.find_urls(msg)
    if not urls:
        return await edit_or_reply(event, "**- قـم بادخــال رابـط مع الامـر او بالــرد ع رابـط ليتـم التحميـل**")
    zedevent = await edit_or_reply(event, "**⎉╎جـارِ التحميل انتظر قليلا ▬▭ ...**")
    reply_to_id = await reply_id(event)
    for url in urls:
        try:
            vid_data = YoutubeDL({"no-playlist": True, "cookiefile": get_cookies_file()}).extract_info(
                url, download=False
            )
        except ExtractorError:
            vid_data = {"title": url, "uploader": "Catuserbot", "formats": []}
        startTime = time()
        retcode = await _mp3Dl(url=url, starttime=startTime, uid="320")
        if retcode != 0:
            return await event.edit(str(retcode))
        _fpath = ""
        thumb_pic = None
        for _path in glob.glob(os.path.join(Config.TEMP_DIR, str(startTime), "*")):
            if _path.lower().endswith((".jpg", ".png", ".webp")):
                thumb_pic = _path
            else:
                _fpath = _path
        if not _fpath:
            return await edit_delete(zedevent, "__Unable to upload file__")
        await zedevent.edit(
            f"**╮ ❐ جـارِ التحضيـر للـرفع انتظـر ...𓅫╰**:\
            \n**{vid_data['title']}***"
        )
        attributes, mime_type = get_attributes(str(_fpath))
        ul = io.open(pathlib.Path(_fpath), "rb")
        if thumb_pic is None:
            thumb_pic = str(
                await pool.run_in_thread(download)(
                    await get_ytthumb(get_yt_video_id(url))
                )
            )
        uploaded = await event.client.fast_upload_file(
            file=ul,
            progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                progress(
                    d,
                    t,
                    zedevent,
                    startTime,
                    "trying to upload",
                    file_name=os.path.basename(pathlib.Path(_fpath)),
                )
            ),
        )
        ul.close()
        media = types.InputMediaUploadedDocument(
            file=uploaded,
            mime_type=mime_type,
            attributes=attributes,
            force_file=False,
            thumb=await event.client.upload_file(thumb_pic) if thumb_pic else None,
        )
        await event.client.send_file(
            event.chat_id,
            file=media,
            caption=f"<b>⎉╎المقطع : </b><code>{vid_data.get('title', os.path.basename(pathlib.Path(_fpath)))}</code>",
            supports_streaming=True,
            reply_to=reply_to_id,
            parse_mode="html",
        )
        for _path in [_fpath, thumb_pic]:
            os.remove(_path)
    await zedevent.delete()


@zedub.zed_cmd(
    pattern="يوتيوب(?: |$)(\\d*)? ?([\\s\\S]*)",
    command=("يوتيوب", plugin_category),
    info={
        "header": "لـ البحـث عـن روابــط بالكلمــه المحــدده علـى يـوتيــوب",
        "مثــال": [
            "{tr}يوتيوب + كلمـه",
            "{tr}يوتيوب + عدد + كلمـه",
        ],
    },
)
async def yt_search(event):
    "Youtube search command"
    if event.is_reply and not event.pattern_match.group(2):
        query = await event.get_reply_message()
        query = str(query.message)
    else:
        query = str(event.pattern_match.group(2))
    if not query:
        return await edit_delete(
            event, "**╮ بالـرد ﮼؏ كلمـٓھہ للبحث أو ضعها مـع الأمـر ... 𓅫╰**"
        )
    video_q = await edit_or_reply(event, "**╮ جـارِ البحث ▬▭... ╰**")
    if event.pattern_match.group(1) != "":
        lim = int(event.pattern_match.group(1))
        if lim <= 0:
            lim = int(10)
    else:
        lim = int(10)
    try:
        full_response = await ytsearch(query, limit=lim)
    except Exception as e:
        return await edit_delete(video_q, str(e), time=10, parse_mode=_format.parse_pre)
    reply_text = f"**⎉╎اليك عزيزي قائمة بروابط الكلمة اللتي بحثت عنها:**\n`{query}`\n\n**⎉╎النتائج:**\n{full_response}"
    await edit_or_reply(video_q, reply_text)

# ================================================================================================ #
# =========================================ساوند كلاود================================================= #
# ================================================================================================ #

def remove_if_exists(path): 
    if os.path.exists(path):
        os.remove(path)


@zedub.zed_cmd(pattern="بحث(?: |$)(.*)")
async def _(event): 
    reply = await event.get_reply_message()
    if event.pattern_match.group(1):
        query = event.pattern_match.group(1)
    elif reply and reply.message:
        query = reply.message
    else:
        return await edit_or_reply(event, "**⎉╎قم باضافـة إسـم للامـر ..**\n**⎉╎بحث + اسـم المقطـع الصـوتي**")
    zedevent = await edit_or_reply(event, "**╮ جـارِ البحث ؏ـن المقطـٓع الصٓوتـي... 🎧♥️╰**")
    ydl_ops = {
        "format": "bestaudio[ext=m4a]",
        "keepvideo": True,
        "prefer_ffmpeg": False,
        "geo_bypass": True,
        "outtmpl": "%(title)s.%(ext)s",
        "quite": True,
        "no_warnings": True,
        "cookiefile" : get_cookies_file(),
    }
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        link = f"https://youtube.com{results[0]['url_suffix']}"
        title = results[0]["title"][:40]
        thumbnail = results[0]["thumbnails"][0]
        thumb_name = f"{title}.jpg"
        thumb = requests.get(thumbnail, allow_redirects=True)
        try:
            open(thumb_name, "wb").write(thumb.content)
        except Exception:
            thumb_name = None
            pass
        duration = results[0]["duration"]

    except Exception as e:
        if "Requested format is not available." in str(e): # تبعي
            await zedevent.edit("**• هنالك تحديث جديد لـ مكتبة يوتيوب 📡**\n**• أرسِـل الامـر** ( `.تحديث البوت` )\n**• ثم انتظر 5 دقائق لـ إعادة تشغيـل البوت ⏳**\n**• بعدها تستطيع استخدام اوامر التحميل .. بدون مشاكـل ☑️**")
        else:
            await zedevent.edit(f"**• فشـل التحميـل** \n**• الخطـأ :** `{str(e)}`\n\n**• قم بـ إرســال هذا الخلل لـ مطور السورس لـ اصلاحه**\n**• تواصـل مطـور السـورس @zxaax**")
            #await zedub.send_message(event.chat_id, "**- استخدم امر التحميل البديـل**\n**- أرسِـل (.تحميل + اسم المقطع الصوتي)**")
            #return
    await zedevent.edit("**╮ جـارِ التحميل ▬▭ . . .🎧♥️╰**")
    try:
        with yt_dlp.YoutubeDL(ydl_ops) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            audio_file = ydl.prepare_filename(info_dict)
            ydl.process_info(info_dict)
        host = str(info_dict["uploader"])
        secmul, dur, dur_arr = 1, 0, duration.split(":")
        for i in range(len(dur_arr) - 1, -1, -1):
            dur += int(float(dur_arr[i])) * secmul
            secmul *= 60
        await zedevent.edit("**╮ جـارِ الرفـع ▬▬ . . .🎧♥️╰**")
        await event.client.send_file(
            event.chat_id,
            audio_file,
            force_document=False,
            caption=f"**⎉ البحث ⥃** `{title}`",
            thumb=thumb_name,
        )
        await zedevent.delete()
    except ChatSendMediaForbiddenError: # Code By T.me/zzzzl1l
        #LOGS.error(str(err))
        return await zedevent.edit("**- عـذرًا .. الوسـائـط مغلقـه هنـا ؟!**")
    except Exception as e:
        if "Requested format is not available." in str(e): # تبعي
            return await zedevent.edit("**• هنالك تحديث جديد لـ مكتبة يوتيوب 📡**\n**• أرسِـل الامـر** ( `.تحديث البوت` )\n**• ثم انتظر 5 دقائق لـ إعادة تشغيـل البوت ⏳**\n**• بعدها تستطيع استخدام اوامر التحميل .. بدون مشاكـل ☑️**")
        else:
            return await zedevent.edit(f"**• فشـل التحميـل** \n**• الخطـأ :** `{str(e)}`\n\n**• قم بـ إرســال هذا الخلل لـ مطور السورس لـ اصلاحه**\n**• تواصـل مطـور السـورس @zxaax**")
    try:
        remove_if_exists(audio_file)
        remove_if_exists(thumb_name)
    except Exception as e:
        print(e)


#Code by T.me/zzzzl1l
@zedub.zed_cmd(pattern="فيديو(?: |$)(.*)")
async def _(event): #Code by T.me/zzzzl1l
    reply = await event.get_reply_message()
    if event.pattern_match.group(1):
        query = event.pattern_match.group(1)
    elif reply and reply.message:
        query = reply.message
    else:
        return await edit_or_reply(event, "**⎉╎قم باضافـة إسـم للامـر ..**\n**⎉╎فيديو + اسـم الفيديـو**")
    zedevent = await edit_or_reply(event, "**╮ جـارِ البحث ؏ـن الفيديـو... 🎧♥️╰**")
    ydl_opts = {
        "format": "bestvideo+bestaudio/best",  # Download best video and audio and merge
        "keepvideo": True,
        "prefer_ffmpeg": False,
        "geo_bypass": True,
        "outtmpl": "%(title)s.%(ext)s",
        "merge_output_format": "mp4",  # Merge video and audio into MP4 format
        "quite": True,
        "no_warnings": True,
        "cookiefile" : get_cookies_file(),
    }
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        link = f"https://youtube.com{results[0]['url_suffix']}"
        title = results[0]["title"][:40]
        thumbnail = results[0]["thumbnails"][0]
        thumb_name = f"{title}.jpg"
        thumb = requests.get(thumbnail, allow_redirects=True)
        open(thumb_name, "wb").write(thumb.content)
        results[0]["duration"]
        results[0]["url_suffix"]
        results[0]["views"]
    except Exception as e:
        if "Requested format is not available." in str(e): # تبعي
            return await zedevent.edit("**• هنالك تحديث جديد لـ مكتبة يوتيوب 📡**\n**• أرسِـل الامـر** ( `.تحديث البوت` )\n**• ثم انتظر 5 دقائق لـ إعادة تشغيـل البوت ⏳**\n**• بعدها تستطيع استخدام اوامر التحميل .. بدون مشاكـل ☑️**")
        else:
            await zedevent.edit("**• هنالك تحديث جديد لـ مكتبة يوتيوب 📡**\n**• أرسِـل الامـر** ( `.تحديث البوت` )\n**• ثم انتظر 5 دقائق لـ إعادة تشغيـل البوت ⏳**\n**• بعدها تستطيع استخدام اوامر التحميل .. بدون مشاكـل ☑️**")
    try:
        msg = await zedevent.edit("**╮ جـارِ التحميل ▬▭ . . .🎧♥️╰**")
        with YoutubeDL(ydl_opts) as ytdl:
            ytdl_data = ytdl.extract_info(link, download=True)
            file_name = ytdl.prepare_filename(ytdl_data)
    except Exception as e:
        if "Requested format is not available." in str(e): # تبعي
            return await zedevent.edit("**• هنالك تحديث جديد لـ مكتبة يوتيوب 📡**\n**• أرسِـل الامـر** ( `.تحديث البوت` )\n**• ثم انتظر 5 دقائق لـ إعادة تشغيـل البوت ⏳**\n**• بعدها تستطيع استخدام اوامر التحميل .. بدون مشاكـل ☑️**")
        else:
            return await zedevent.edit(f"**• فشـل التحميـل** \n**• الخطـأ :** `{str(e)}`\n\n**• قم بـ إرســال هذا الخلل لـ مطور السورس لـ اصلاحه**\n**• تواصـل مطـور السـورس @zxaax**")
    preview = wget.download(thumbnail)
    await zedevent.edit("**╮ جـارِ الرفـع ▬▬ . . .🎧♥️╰**")
    try:
        await event.client.send_file(
            event.chat_id,
            file_name,
            caption=f"**⎉ البحث ⥃** `{title}`",
            thumb=preview,
            supports_streaming=True,
        )
    except ChatSendMediaForbiddenError: # Code By T.me/zzzzl1l
        #LOGS.error(str(err))
        return await zedevent.edit("**- عـذرًا .. الوسـائـط مغلقـه هنـا ؟!**")
    except Exception as e: # Code By T.me/zzzzl1l
        return await zedevent.edit(f"**• فشـل التحميـل** \n**• الخطـأ :** `{str(e)}`\n\n**• قم بـ إرســال هذا الخلل لـ مطور السورس لـ اصلاحه**\n**• تواصـل مطـور السـورس @zxaax**")
    try:
        remove_if_exists(file_name)
        await zedevent.delete()
    except Exception as e:
        print(e)


# ================================================================================================ #
# =========================================ردود الخاص================================================= #
# ================================================================================================ #

@zedub.zed_cmd(
    pattern="ابحث(?:\ع|$)([\s\S]*)",
    command=("ابحث", plugin_category),
    info={
        "header": "To reverse search song.",
        "الوصـف": "Reverse search audio file using shazam api",
        "امـر مضـاف": {"ع": "To send the song of sazam match"},
        "الاستخـدام": [
            "{tr}ابحث بالــرد ع بصمـه او مقطـع صوتي",
            "{tr}ابحث ع بالــرد ع بصمـه او مقطـع صوتي",
        ],
    },
)
async def shazamcmd(event):
    "To reverse search song."
    reply = await event.get_reply_message()
    mediatype = await media_type(reply)
    chat = "@DeezerMusicBot"
    delete = False
    flag = event.pattern_match.group(1)
    if not reply or not mediatype or mediatype not in ["Voice", "Audio"]:
        return await edit_delete(
            event, "**- بالــرد ع مقطـع صـوتي**"
        )
    zedevent = await edit_or_reply(event, "**- جـار تحميـل المقـطع الصـوتي ...**")
    name = "zed.mp3"
    try:
        for attr in getattr(reply.document, "attributes", []):
            if isinstance(attr, types.DocumentAttributeFilename):
                name = attr.file_name
        dl = io.FileIO(name, "a")
        await event.client.fast_download_file(
            location=reply.document,
            out=dl,
        )
        dl.close()
        mp3_fileto_recognize = open(name, "rb").read()
        shazam = Shazam(mp3_fileto_recognize)
        recognize_generator = shazam.recognizeSong()
        track = next(recognize_generator)[1]["track"]
    except Exception as e:
        LOGS.error(e)
        return await edit_delete(
            zedevent, f"**- خطـأ :**\n__{e}__"
        )

    file = track["images"]["background"]
    title = track["share"]["subject"]
    slink = await yt_search(title)
    if flag == "s":
        deezer = track["hub"]["providers"][1]["actions"][0]["uri"][15:]
        async with event.client.conversation(chat) as conv:
            try:
                purgeflag = await conv.send_message("/start")
            except YouBlockedUserError:
                await zedub(unblock("DeezerMusicBot"))
                purgeflag = await conv.send_message("/start")
            await conv.get_response()
            await event.client.send_read_acknowledge(conv.chat_id)
            await conv.send_message(deezer)
            await event.client.get_messages(chat)
            song = await event.client.get_messages(chat)
            await song[0].click(0)
            await conv.get_response()
            file = await conv.get_response()
            await event.client.send_read_acknowledge(conv.chat_id)
            delete = True
    await event.client.send_file(
        event.chat_id,
        file,
        caption=f"<b>⎉╎ المقطـع الصـوتي :</b> <code>{title}</code>\n<b>⎉╎ الرابـط : <a href = {slink}/1>YouTube</a></b>",
        reply_to=reply,
        parse_mode="html",
    )
    await zedevent.delete()
    if delete:
        await delete_conv(event, chat, purgeflag)


# Code by T.me/zzzzl1l
@zedub.zed_cmd(pattern=".ff(?:\s|$)([\s\S]*)")
async def zelzal_song(event):
    song = event.pattern_match.group(1)
    chat = "@ROOTMusic_bot"
    reply_id_ = await reply_id(event)
    zzevent = await edit_or_reply(event, SONG_SEARCH_STRING, parse_mode="html")
    async with event.client.conversation(chat) as conv:
        try:
            purgeflag = await conv.send_message("/start")
        except YouBlockedUserError:
            await catub(unblock("ROOTMusic_bot"))
            await conv.send_message("/start")
        await conv.send_message(song)
        hmm = await conv.get_response()
        zzz = await event.client.get_messages(chat)
        await zzevent.edit(SONG_SENDING_STRING, parse_mode="html")
        await zzz[0].click(0)
        await conv.get_response()
        music = await conv.get_response()
        await event.client.send_read_acknowledge(conv.chat_id)
        await event.client.send_file(
            event.chat_id,
            music,
            caption=f"<b>⎉ البحث ⥃ <code>{song}</code></b>",
            parse_mode="html",
            reply_to=reply_id_,
        )
        await zzevent.delete()
        await delete_conv(event, chat, purgeflag)


@zedub.zed_cmd(
    pattern="يوتيوب(?: |$)(\d*)? ?([\s\S]*)",
    command=("يوتيوب", plugin_category),
    info={
        "header": "لـ البحـث عـن روابــط بالكلمــه المحــدده علـى يـوتيــوب",
        "مثــال": [
            "{tr}يوتيوب + كلمـه",
            "{tr}يوتيوب + عدد + كلمـه",
        ],
    },
)
async def you_search(event):
    "Youtube search command"
    if event.is_reply and not event.pattern_match.group(2):
        query = await event.get_reply_message()
        query = str(query.message)
    else:
        query = str(event.pattern_match.group(2))
    if not query:
        return await edit_delete(
            event, "**╮ بالـرد ﮼؏ كلمـٓھہ للبحث أو ضعها مـع الأمـر ... 𓅫╰**"
        )
    video_q = await edit_or_reply(event, "**╮ جـارِ البحث ▬▭... ╰**")
    if event.pattern_match.group(1) != "":
        lim = int(event.pattern_match.group(1))
        if lim <= 0:
            lim = int(10)
    else:
        lim = int(10)
    try:
        full_response = await ytsearch(query, limit=lim)
    except Exception as e:
        return await edit_delete(video_q, str(e), time=10, parse_mode=_format.parse_pre)
    reply_text = f"**•  اليك عزيزي قائمة بروابط الكلمة اللتي بحثت عنها:**\n`{query}`\n\n**•  النتائج:**\n{full_response}"
    await edit_or_reply(video_q, reply_text)


async def ytdl_down(event, opts, url):
    ytdl_data = None
    try:
        await event.edit("**╮ ❐ يتـم جلـب البيانـات انتظـر قليلاً ...𓅫╰▬▭ **")
        with YoutubeDL(opts) as ytdl:
            ytdl_data = ytdl.extract_info(url)
    except DownloadError as DE:
        await event.edit(f"`{DE}`")
    except ContentTooShortError:
        await event.edit("**- عذرا هذا المحتوى قصير جدا لتنزيله ⚠️**")
    except GeoRestrictedError:
        await event.edit(
            "**- الفيديو غير متاح من موقعك الجغرافي بسبب القيود الجغرافية التي يفرضها موقع الويب ❕**"
        )
    except MaxDownloadsReached:
        await event.edit("**- تم الوصول إلى الحد الأقصى لعدد التنزيلات ❕**")
    except PostProcessingError:
        await event.edit("**كان هناك خطأ أثناء المعالجة**")
    except UnavailableVideoError:
        await event.edit("**⌔∮عـذرًا .. الوسائط غير متوفـره بالتنسيق المطلـوب**")
    except XAttrMetadataError as XAME:
        await event.edit(f"`{XAME.code}: {XAME.msg}\n{XAME.reason}`")
    except ExtractorError:
        await event.edit("**حدث خطأ أثناء استخراج المعلومات يرجى وضعها بشكل صحيح ⚠️**")
    except Exception as e:
        await event.edit(f"**Error : **\n__{e}__")
    return ytdl_data


async def fix_attributes(
    path, info_dict: dict, supports_streaming: bool = False, round_message: bool = False
) -> list:
    """Avoid multiple instances of an attribute."""
    new_attributes = []
    video = False
    audio = False

    uploader = info_dict.get("uploader", "Unknown artist")
    duration = int(info_dict.get("duration", 0))
    suffix = path.suffix[1:]
    if supports_streaming and suffix != "mp4":
        supports_streaming = True

    attributes, mime_type = get_attributes(path)
    if suffix == "mp3":
        title = str(info_dict.get("title", info_dict.get("id", "Unknown title")))
        audio = types.DocumentAttributeAudio(
            duration=duration, voice=None, title=title, performer=uploader
        )
    elif suffix == "mp4":
        width = int(info_dict.get("width", 0))
        height = int(info_dict.get("height", 0))
        for attr in attributes:
            if isinstance(attr, types.DocumentAttributeVideo):
                duration = duration or attr.duration
                width = width or attr.w
                height = height or attr.h
                break
        video = types.DocumentAttributeVideo(
            duration=duration,
            w=width,
            h=height,
            round_message=round_message,
            supports_streaming=supports_streaming,
        )

    if audio and isinstance(audio, types.DocumentAttributeAudio):
        new_attributes.append(audio)
    if video and isinstance(video, types.DocumentAttributeVideo):
        new_attributes.append(video)

    new_attributes.extend(
        attr
        for attr in attributes
        if (
            isinstance(attr, types.DocumentAttributeAudio)
            and not audio
            or not isinstance(attr, types.DocumentAttributeAudio)
            and not video
            or not isinstance(attr, types.DocumentAttributeAudio)
            and not isinstance(attr, types.DocumentAttributeVideo)
        )
    )
    return new_attributes, mime_type


@zedub.zed_cmd(
    pattern="تحميل صوت(?: |$)(.*)",
    command=("تحميل صوت", plugin_category),
    info={
        "header": "تحميـل الاغـاني مـن يوتيوب .. فيسبوك .. انستا .. الـخ عـبر الرابـط",
        "مثــال": ["{tr}تحميل صوت بالــرد ع رابــط", "{tr}تحميل صوت + رابــط"],
    },
)
async def download_audio(event):
    msg = event.pattern_match.group(1)
    rmsg = await event.get_reply_message()
    if not msg and rmsg:
        msg = rmsg.text
    urls = extractor.find_urls(msg)
    if not urls:
        return await edit_or_reply(event, "**- قـم بادخــال رابـط مع الامـر او بالــرد ع رابـط ليتـم التحميـل**")
    zedevent = await edit_or_reply(event, "**⌔╎جـارِ التحميل انتظر قليلا ▬▭ ...**")
    reply_to_id = await reply_id(event)
    for url in urls:
        try:
            vid_data = YoutubeDL({"no-playlist": True, "cookiefile": get_cookies_file()}).extract_info(
                url, download=False
            )
        except ExtractorError:
            vid_data = {"title": url, "uploader": "Catuserbot", "formats": []}
        startTime = time()
        retcode = await _mp3Dl(url=url, starttime=startTime, uid="320")
        if retcode != 0:
            return await event.edit(str(retcode))
        _fpath = ""
        thumb_pic = None
        for _path in glob.glob(os.path.join(Config.TEMP_DIR, str(startTime), "*")):
            if _path.lower().endswith((".jpg", ".png", ".webp")):
                thumb_pic = _path
            else:
                _fpath = _path
        if not _fpath:
            return await edit_delete(zedevent, "__Unable to upload file__")
        await zedevent.edit(
            f"**╮ ❐ جـارِ التحضيـر للـرفع انتظـر ...𓅫╰**:\
            \n**{vid_data['title']}***"
        )
        attributes, mime_type = get_attributes(str(_fpath))
        ul = io.open(pathlib.Path(_fpath), "rb")
        if thumb_pic is None:
            thumb_pic = str(
                await pool.run_in_thread(download)(
                    await get_ytthumb(get_yt_video_id(url))
                )
            )
        uploaded = await event.client.fast_upload_file(
            file=ul,
            progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                progress(
                    d,
                    t,
                    zedevent,
                    startTime,
                    "trying to upload",
                    file_name=os.path.basename(pathlib.Path(_fpath)),
                )
            ),
        )
        ul.close()
        media = types.InputMediaUploadedDocument(
            file=uploaded,
            mime_type=mime_type,
            attributes=attributes,
            force_file=False,
            thumb=await event.client.upload_file(thumb_pic) if thumb_pic else None,
        )
        try:
            await event.client.send_file(
                event.chat_id,
                file=media,
                caption=f"<b>⎉ تحميـل ⥃ </b><code>{vid_data.get('title', os.path.basename(pathlib.Path(_fpath)))}</code>",
                supports_streaming=True,
                reply_to=reply_to_id,
                parse_mode="html",
            )
        except ChatSendMediaForbiddenError: # Code By T.me/zzzzl1l
            return await zedevent.edit("**- عـذرًا .. الوسـائـط مغلقـه هنـا ؟!**")
        except Exception as e: # Code By T.me/zzzzl1l
            return await zedevent.edit(f"**• فشـل التحميـل** \n**• الخطـأ :** `{str(e)}`\n\n**• غالباً .. التحميل غير متاح في هذه الدردشـة ✖️**")
        for _path in [_fpath, thumb_pic]:
            os.remove(_path)
    await zedevent.delete()

@zedub.zed_cmd(
    pattern="تحميل فيديو(?: |$)(.*)",
    command=("تحميل فيديو", plugin_category),
    info={
        "header": "تحميـل مقـاطـع الفيـديــو مـن يوتيوب .. فيسبوك .. انستا .. الـخ عـبر الرابـط",
        "مثــال": [
            "{tr}تحميل فيديو بالــرد ع رابــط",
            "{tr}تحميل فيديو + رابــط",
        ],
    },
)
async def download_video(event):
    msg = event.pattern_match.group(1)
    rmsg = await event.get_reply_message()
    if not msg and rmsg:
        msg = rmsg.text
    urls = extractor.find_urls(msg)
    if not urls:
        return await edit_or_reply(event, "**- قـم بادخــال رابـط مع الامـر او بالــرد ع رابـط ليتـم التحميـل**")
    zedevent = await edit_or_reply(event, "**⌔╎جـارِ التحميل انتظر قليلا ▬▭ ...**")
    reply_to_id = await reply_id(event)
    for url in urls:
        ytdl_data = await ytdl_down(zedevent, video_opts, url)
        if ytdl_down is None:
            return
        try:
            f = pathlib.Path("zed_ytv.mp4")
            print(f)
            zedthumb = pathlib.Path("zed_ytv.jpg")
            if not os.path.exists(zedthumb):
                zedthumb = pathlib.Path("zed_ytv.webp")
            if not os.path.exists(zedthumb):
                zedthumb = None
            await zedevent.edit(
                f"**╮ ❐ جـارِ التحضيـر للـرفع انتظـر ...𓅫╰**:\
                \n**{ytdl_data['title']}**"
            )
            ul = io.open(f, "rb")
            c_time = time()
            attributes, mime_type = await fix_attributes(
                f, ytdl_data, supports_streaming=True
            )
            uploaded = await event.client.fast_upload_file(
                file=ul,
                progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                    progress(
                        d, t, zedevent, c_time, "Upload :", file_name=ytdl_data["title"]
                    )
                ),
            )
            ul.close()
            media = types.InputMediaUploadedDocument(
                file=uploaded,
                mime_type=mime_type,
                attributes=attributes,
            )
            try:
                await event.client.send_file(
                    event.chat_id,
                    file=media,
                    reply_to=reply_to_id,
                    caption=f'**⎉ تحميـل ⥃** `{ytdl_data["title"]}`',
                    thumb=zedthumb,
                )
            except ChatSendMediaForbiddenError: # Code By T.me/zzzzl1l
                return await zedevent.edit("**- عـذرًا .. الوسـائـط مغلقـه هنـا ؟!**")
            except Exception as e: # Code By T.me/zzzzl1l
                return await zedevent.edit(f"**• فشـل التحميـل** \n**• الخطـأ :** `{str(e)}`\n\n**• غالباً .. التحميل غير متاح في هذه الدردشـة ✖️**")
            os.remove(f)
            if zedthumb:
                os.remove(zedthumb)
        except TypeError:
            await asyncio.sleep(2)
    await zedevent.delete()

# ================================================================================================ #
# =========================================ردود الخاص================================================= #
# ================================================================================================ #
import re
import datetime
from asyncio import sleep

from telethon import events
from telethon.utils import get_display_name

from . import zedub
from ..core.logger import logging
from ..core.managers import edit_delete, edit_or_reply
from ..sql_helper import pmpermit_sql as pmpermit_sql
from ..sql_helper.globals import addgvar, delgvar, gvarstatus
from ..sql_helper.pasmat_sql import (
    add_pasmat,
    get_pasmats,
    remove_all_pasmats,
    remove_pasmat,
)
from ..sql_helper.pmrad_sql import (
    add_pmrad,
    get_pmrads,
    remove_all_pmrads,
    remove_pmrad,
)
from . import BOTLOG, BOTLOG_CHATID

plugin_category = "الخدمات"
LOGS = logging.getLogger(__name__)


ZelzalMeMe_cmd = (
    "𓆩 [ 𝗧𝗘𝗣𝗧𝗛𝗢𝗡 - اوامـر البصمـات 🎙](t.me/Tepthon) 𓆪\n\n"
    "**✾╎قائـمه اوامـر ردود البصمات والميديا العامـه🎙:**\n\n"
    "**⎞𝟏⎝** `.بصمه`\n"
    "**•• ⦇الامـر + كلمـة الـرد بالـرد ع بصمـه او ميديـا⦈ لـ اضـافة رد بصمـه عـام**\n\n"
    "**⎞𝟐⎝** `.حذف بصمه`\n"
    "**•• ⦇الامـر + كلمـة البصمـه⦈ لـ حـذف رد بصمـه محـدد**\n\n"
    "**⎞𝟑⎝** `.بصماتي`\n"
    "**•• لـ عـرض قائمـة بـ جميـع بصمـاتك المضـافـه**\n\n"
    "**⎞𝟒⎝** `.حذف بصماتي`\n"
    "**•• لـ حـذف جميـع بصمـاتك المضافـه**\n\n"
    "\n 𓆩 [𝙎𝙊𝙐𝙍𝘾𝞝 𝗧𝗘𝗣𝗧𝗛𝗢𝗡](t.me/Tepthon) 𓆪"
)


# Copyright (C) 2022 Zed-Thon . All Rights Reserved
@zedub.zed_cmd(pattern="البصمات")
async def cmd(zelzallll):
    await edit_or_reply(zelzallll, ZelzalMeMe_cmd)

async def reply_id(event):
    reply_to_id = None
    if event.reply_to_msg_id:
        reply_to_id = event.reply_to_msg_id
    return reply_to_id

@zedub.on(admin_cmd(incoming=True))
async def filter_incoming_handler(event):
    name = event.raw_text
    repl = await reply_id(event)
    filters = get_pasmats(zedub.uid)
    if not filters:
        return
    for trigger in filters:
        if name == trigger.keyword:
            file_media = None
            filter_msg = None
            if trigger.f_mesg_id:
                msg_o = await event.client.get_messages(
                    entity=BOTLOG_CHATID, ids=int(trigger.f_mesg_id)
                )
                file_media = msg_o.media
                filter_msg = msg_o.message
                link_preview = True
            elif trigger.reply:
                filter_msg = trigger.reply
                link_preview = False
            try:
                await event.client.send_file(
                    event.chat_id,
                    file=file_media,
                    link_preview=link_preview,
                    reply_to=repl,
                )
                await event.delete()
            except BaseException:
                return

@zedub.zed_cmd(pattern="بصمه (.*)")
async def add_new_meme(event):
    keyword = event.pattern_match.group(1)
    string = event.text.partition(keyword)[2]
    msg = await event.get_reply_message()
    msg_id = None
    if msg and msg.media and not string:
        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID,
                f"**⪼ البصمـات 🔊 :**\
                \n**⪼ تم حفـظ البصمـه بـ اسم {keyword}**\n**⪼ لـ قائمـه بصماتك .. بنجـاح ✅**\n**⪼ لـ تصفـح قائمـة بصماتك أرسِـل (.بصماتي) 📑**",
            )
            msg_o = await event.client.forward_messages(
                entity=BOTLOG_CHATID,
                messages=msg,
                from_peer=event.chat_id,
                silent=True,
            )
            msg_id = msg_o.id
        else:
            await edit_or_reply(
                event,
                "**❈╎يتطلب اضافة البصمات تعيين كـروب السجـل اولاً ..**\n**❈╎لاضافـة كـروب السجـل**\n**❈╎اتبـع الشـرح ⇚** https://t.me/zzzvrr/13",
            )
            return
    elif msg and msg.text and not string:
        return await edit_or_reply(event, "**⪼ أرسِـل (** `.بصمه` **) + اسم البصمـه**\n**⪼بالـرد ع بصمـه او مقطـع صـوتـي 🔊**\n**⪼ لإضافتـها لـ قائمـة بصماتك 🧾**")
    elif not string:
        return await edit_or_reply(event, "**⪼ أرسِـل (** `.بصمه` **) + اسم البصمـه**\n**⪼بالـرد ع بصمـه او مقطـع صـوتـي 🔊**\n**⪼ لإضافتـها لـ قائمـة بصماتك 🧾**")
    else:
        return await edit_or_reply(event, "**⪼ أرسِـل (** `.بصمه` **) + اسم البصمـه**\n**⪼بالـرد ع بصمـه او مقطـع صـوتـي 🔊**\n**⪼ لإضافتـها لـ قائمـة بصماتك 🧾**")
    success = "**⪼تم {} البصمـه بـ اسم {} .. بنجـاح ✅**"
    if add_pasmat(str(zedub.uid), keyword, string, msg_id) is True:
        return await edit_or_reply(event, success.format("اضافة", keyword))
    remove_pasmat(str(zedub.uid), keyword)
    if add_pasmat(str(zedub.uid), keyword, string, msg_id) is True:
        return await edit_or_reply(event, success.format("تحديث", keyword))
    await edit_or_reply(event, "**⪼ أرسِـل (** `.بصمه` **) + اسم البصمـه**\n**⪼بالـرد ع بصمـه او مقطـع صـوتـي 🔊**\n**⪼ لإضافتـها لـ قائمـة بصماتك 🧾**")


@zedub.zed_cmd(pattern="بصماتي$")
async def on_meme_list(event):
    OUT_STR = "**⪼ لا يوجـد لديك بصمـات محفوظـه ❌**\n\n**⪼ أرسِـل (** `.بصمه` **) + اسم البصمـه**\n**⪼بالـرد ع بصمـه او مقطـع صـوتـي 🔊**\n**⪼ لإضافتـها لـ قائمـة بصماتك 🧾**"
    filters = get_pasmats(zedub.uid)
    for filt in filters:
        if OUT_STR == "**⪼ لا يوجـد لديك بصمـات محفوظـه ❌**\n\n**⪼ أرسِـل (** `.بصمه` **) + اسم البصمـه**\n**⪼بالـرد ع بصمـه او مقطـع صـوتـي 🔊**\n**⪼ لإضافتـها لـ قائمـة بصماتك 🧾**":
            OUT_STR = "𓆩 𝗦𝗼𝘂𝗿𝗰𝗲 𝗧𝗘𝗣𝗧𝗛𝗢𝗡 - قائمـة بصمـاتك المضـافـة 🔊𓆪\n⋆┄─┄─┄─┄┄─┄─┄─┄─┄┄⋆\n"
        OUT_STR += "🎙 `{}`\n".format(filt.keyword)
    await edit_or_reply(
        event,
        OUT_STR,
        caption="**⧗╎قائمـة بصمـاتك المضـافـه🔊**",
        file_name="filters.text",
    )


@zedub.zed_cmd(pattern="حذف بصمه(?: |$)(.*)")
async def remove_a_meme(event):
    filt = event.pattern_match.group(1)
    if not remove_pasmat(zedub.uid, filt):
        await event.edit("**- ❝ البصمـه ↫** {} **غيـر موجـوده ⁉️**".format(filt))
    else:
        await event.edit("**- ❝ البصمـه ↫** {} **تم حذفهـا بنجاح ☑️**".format(filt))


@zedub.zed_cmd(pattern="حذف بصماتي$")
async def on_all_meme_delete(event):
    filters = get_pasmats(zedub.uid)
    if filters:
        remove_all_pasmats(zedub.uid)
        await edit_or_reply(event, "**⪼ تم حـذف جميـع بصمـاتك .. بنجـاح ✅**")
    else:
        OUT_STR = "**⪼ لا يوجـد لديك بصمـات محفوظـه ❌**\n\n**⪼ أرسِـل (** `.بصمه` **) + اسم البصمـه**\n**⪼بالـرد ع بصمـه او مقطـع صـوتـي 🔊**\n**⪼ لإضافتـها لـ قائمـة بصماتك 🧾**"
        await edit_or_reply(event, OUT_STR)

# ================================================================================================ #
# =========================================ردود الخاص================================================= #
# ================================================================================================ #

@zedub.on(admin_cmd(incoming=True))
async def filter_incoming_handler(event):
    if not event.is_private:
        return
    if event.sender_id == event.client.uid:
        return
    name = event.raw_text
    filters = get_pmrads(zedub.uid)
    if not filters:
        return
    a_user = await event.get_sender()
    chat = await event.get_chat()
    me = await event.client.get_me()
    title = None
    #participants = await event.client.get_participants(chat)
    count = None
    mention = f"[{a_user.first_name}](tg://user?id={a_user.id})"
    my_mention = f"[{me.first_name}](tg://user?id={me.id})"
    first = a_user.first_name
    last = a_user.last_name
    fullname = f"{first} {last}" if last else first
    username = f"@{a_user.username}" if a_user.username else mention
    userid = a_user.id
    my_first = me.first_name
    my_last = me.last_name
    my_fullname = f"{my_first} {my_last}" if my_last else my_first
    my_username = f"@{me.username}" if me.username else my_mention
    for trigger in filters:
        pattern = f"( |^|[^\\w]){re.escape(trigger.keyword)}( |$|[^\\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            file_media = None
            filter_msg = None
            if trigger.f_mesg_id:
                msg_o = await event.client.get_messages(
                    entity=BOTLOG_CHATID, ids=int(trigger.f_mesg_id)
                )
                file_media = msg_o.media
                filter_msg = msg_o.message
                link_preview = True
            elif trigger.reply:
                filter_msg = trigger.reply
                link_preview = False
            await event.reply(
                filter_msg.format(
                    mention=mention,
                    first=first,
                    last=last,
                    fullname=fullname,
                    username=username,
                    userid=userid,
                    my_first=my_first,
                    my_last=my_last,
                    my_fullname=my_fullname,
                    my_username=my_username,
                    my_mention=my_mention,
                ),
                file=file_media,
                link_preview=link_preview,
            )

@zedub.zed_cmd(pattern="اضف تلقائي (.*)")
async def add_new_meme(event):
    keyword = event.pattern_match.group(1)
    string = event.text.partition(keyword)[2]
    msg = await event.get_reply_message()
    msg_id = None
    if msg and msg.media and not string:
        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID,
                f"**⪼ ردودك التلقائيـه خـاص 🗣 :**\
                \n**⪼ تم حفـظ الـرد التلقـائـي بـ اسم {keyword}**\n**⪼ لـ قائمـه ردودك التلقائيـه .. بنجـاح ✅**\n**⪼ لـ تصفـح قائمـة ردودك التلقائيـه أرسِـل (.ردود الخاص) 📑**",
            )
            msg_o = await event.client.forward_messages(
                entity=BOTLOG_CHATID,
                messages=msg,
                from_peer=event.chat_id,
                silent=True,
            )
            msg_id = msg_o.id
        else:
            await edit_or_reply(
                event,
                "**❈╎يتطلب اضافة الـردود التلقـائـيـه تعيين كـروب السجـل اولاً ..**\n**❈╎لاضافـة كـروب السجـل**\n**❈╎اتبـع الشـرح ⇚** https://t.me/zzzvrr/13",
            )
            return
    elif msg and msg.text and not string:
        string = msg.text
    elif not string:
        return await edit_or_reply(event, "**⪼ أرسِـل (** `.اضف تلقائي` **) + كلمـة الـرد**\n**⪼بالـرد ع جملـة او ميديـا ??**\n**⪼ لإضافتـها لـ قائمـة ردودك التلقائيـه 🧾**")
    else:
        return await edit_or_reply(event, "**⪼ أرسِـل (** `.اضف تلقائي` **) + كلمـة الـرد**\n**⪼بالـرد ع جملـة او ميديـا 🗣**\n**⪼ لإضافتـها لـ قائمـة ردودك التلقائيـه 🧾**")
    success = "**⪼تم {} الـرد التلقـائـي بـ اسم {} .. بنجـاح ✅**"
    if add_pmrad(str(zedub.uid), keyword, string, msg_id) is True:
        return await edit_or_reply(event, success.format("اضافة", keyword))
    remove_pmrad(str(zedub.uid), keyword)
    if add_pmrad(str(zedub.uid), keyword, string, msg_id) is True:
        return await edit_or_reply(event, success.format("تحديث", keyword))
    await edit_or_reply(event, "**⪼ أرسِـل (** `.اضف تلقائي` **) + كلمـة الـرد**\n**⪼بالـرد ع جملـة او ميديـا 🗣**\n**⪼ لإضافتـها لـ قائمـة ردودك التلقائيـه 🧾**")


@zedub.zed_cmd(pattern="ردود الخاص$")
async def on_meme_list(event):
    OUT_STR = "**⪼ لا يوجـد لديك ردود تلقائيـه لـ الخـاص ❌**\n\n**⪼ أرسِـل (** `.اضف تلقائي` **) + كلمـة الـرد**\n**⪼بالـرد ع جملـة او ميديـا 🗣**\n**⪼ لإضافتـها لـ قائمـة ردودك التلقائيـه 🧾**"
    filters = get_pmrads(zedub.uid)
    for filt in filters:
        if OUT_STR == "**⪼ لا يوجـد لديك ردود تلقائيـه لـ الخـاص ❌**\n\n**⪼ أرسِـل (** `.اضف تلقائي` **) + كلمـة الـرد**\n**⪼بالـرد ع جملـة او ميديـا 🗣**\n**⪼ لإضافتـها لـ قائمـة ردودك التلقائيـه 🧾**":
            OUT_STR = "𓆩 𝗦𝗼𝘂𝗿𝗰𝗲 𝗧𝗘𝗣𝗧𝗛𝗢𝗡 - ردودك التلقـائيـه خـاص 🗣𓆪\n⋆┄─┄─┄─┄┄─┄─┄─┄─┄┄⋆\n"
        OUT_STR += "🎙 `{}`\n".format(filt.keyword)
    await edit_or_reply(
        event,
        OUT_STR,
        caption="**⧗╎قائمـة ردودك التلقـائـيـه خـاص المضـافـه🗣**",
        file_name="filters.text",
    )


@zedub.zed_cmd(pattern="حذف تلقائي(?: |$)(.*)")
async def remove_a_meme(event):
    filt = event.pattern_match.group(1)
    if not remove_pmrad(zedub.uid, filt):
        await event.edit("**- ❝ الـرد التلقـائـي ↫** {} **غيـر موجـود ⁉️**".format(filt))
    else:
        await event.edit("**- ❝ الـرد التلقـائـي ↫** {} **تم حذفه .. بنجاح ☑️**".format(filt))


@zedub.zed_cmd(pattern="حذف ردود الخاص$")
async def on_all_meme_delete(event):
    filters = get_pmrads(zedub.uid)
    if filters:
        remove_all_pmrads(zedub.uid)
        await edit_or_reply(event, "**⪼ تم حـذف جميـع ردودك التلقـائـيـه خـاص .. بنجـاح ✅**")
    else:
        OUT_STR = "**⪼ لا يوجـد لديك ردود تلقائيـه لـ الخـاص ❌**\n\n**⪼ أرسِـل (** `.اضف تلقائي` **) + كلمـة الـرد**\n**⪼بالـرد ع جملـة او ميديـا 🗣**\n**⪼ لإضافتـها لـ قائمـة ردودك التلقائيـه 🧾**"
        await edit_or_reply(event, OUT_STR)
