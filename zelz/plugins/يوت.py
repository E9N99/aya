import os
import requests
import yt_dlp
from telethon import TelegramClient, events
from youtube_search import YoutubeSearch as B3KKK
from ..Config import Config
from zelz import zedub
import glob
import random

def get_cookies_file():
    folder_path = f"{os.getcwd()}/rcookies"
    txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
    if not txt_files:
        raise FileNotFoundError("No .txt files found in the specified folder.")
    cookie_txt_file = random.choice(txt_files)
    return cookie_txt_file

@zedub.on(events.NewMessage(pattern='.يوت (.*)'))
async def srchDl(e):
    try:
        # تحقق من هوية المرسل
        if e.sender_id != Config.OWNER_ID:  # تأكد من أنك تستخدم معرف المرسل الصحيح
            return

        txt = e.raw_text.split(maxsplit=1)  # تقسيم النص إلى امر والبحث
        if len(txt) < 2:
            await e.reply("اكتب اسم الفيديو بعد الامر.")
            return
        q = txt[1]

        # استخدام B3KKK للبحث عن الفيديو
        res = B3KKK(q, max_results=1).to_dict()
        if not res:
            await e.reply("ما لقيت شـيء 😢")
            return
        vid = res[0]
        ttl = vid["title"]
        id = vid["id"]
        lnk = f"https://youtu.be/{id}"
        await e.reply(f"بيتم التحميل يا باشا: {ttl}")

        opts = {
            "format": "bestaudio/best",
            "cookiefile": get_cookies_file(),
            "noplaylist": True,
            "quiet": True  # تقليل التفاعلات من yt-dlp
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(lnk, download=False)

        # تحقق من وجود خاصية 'duration'
        duration = info.get("duration", 0)
        if duration > 3605:
            await e.reply("طول الفيديو كبير اوي، مش هنقدر نحمله 🙄")
            return

        # تحميل الصوت
        audio_file = ydl.prepare_filename(info)
        ydl.download([lnk])

        thb = info.get("thumbnail", None)
        if thb:
            thbFile = f"{id}.png"
            r = requests.get(thb)
            with open(thbFile, "wb") as f:
                f.write(r.content)

            await zedub.send_file(
                e.chat_id,
                audio_file,
                title=info["title"],
                performer=info.get("channel", "Unknown Artist"),
                duration=duration,
                thumb=thbFile,
            )
            os.remove(thbFile)
        else:
            await zedub.send_file(
                e.chat_id,
                audio_file,
                title=info["title"],
                performer=info.get("channel", "Unknown Artist"),
                duration=duration,
            )

        os.remove(audio_file)  # إزالة ملف الصوت بعد الإرسال
    except Exception as ex:
        await e.reply(f"حصل خطأ: {str(ex)}")
