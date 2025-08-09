import random
import re
import time
import psutil
from datetime import datetime
from platform import python_version

import requests
from telethon import version
from telethon.errors.rpcerrorlist import (
    MediaEmptyError,
    WebpageCurlFailedError,
    WebpageMediaEmptyError,
)

from . import StartTime, zedub, zedversion

from ..Config import Config
from ..core.managers import edit_or_reply
from ..helpers.functions import zedalive, check_data_base_heal_th, get_readable_time
from ..helpers.utils import reply_id
from ..sql_helper.globals import gvarstatus

plugin_category = "العروض"
STATS = gvarstatus("Z_STATS") or "فحص"


@zedub.zed_cmd(pattern=f"{STATS}$")
async def amireallyalive(event):
    reply_to_id = await reply_id(event)
    uptime = await get_readable_time((time.time() - StartTime))
    boot_time_timestamp = psutil.boot_time()
    bt = datetime.fromtimestamp(boot_time_timestamp)
    start = datetime.now()
    zedevent = await edit_or_reply(event, "**⎆┊جـاري .. فحـص البـوت الخـاص بك**")
    end = datetime.now()
    ms = (end - start).microseconds / 1000
    _, check_sgnirts = check_data_base_heal_th()
    if gvarstatus("z_date") is not None:
        zzd = gvarstatus("z_date")
        zzt = gvarstatus("z_time")
        zedda = f"{zzd}┊{zzt}"
    else:
        zedda = f"{bt.year}/{bt.month}/{bt.day}"
    Z_EMOJI = gvarstatus("ALIVE_EMOJI") or "✾╿"
    ALIVE_TEXT = gvarstatus("ALIVE_TEXT") or "**بـوت  ماتركـس 𝙈𝙖𝙏𝙍𝙞𝙭 ⌁  يعمـل .. بنجـاح ☑️ 𓆩**"
    ZED_IMG = gvarstatus("ALIVE_PIC")
    zed_caption = gvarstatus("ALIVE_TEMPLATE") or zed_temp
    caption = zed_caption.format(
        ALIVE_TEXT=ALIVE_TEXT,
        Z_EMOJI=Z_EMOJI,
        mention=mention,
        uptime=uptime,
        zedda=zedda,
        telever=version.__version__,
        zdver=zedversion,
        pyver=python_version(),
        dbhealth=check_sgnirts,
        ping=ms,
    )
    if ZED_IMG:
        ZED = [x for x in ZED_IMG.split()]
        PIC = random.choice(ZED)
        try:
            await event.client.send_file(
                event.chat_id, PIC, caption=caption, reply_to=reply_to_id
            )
            await zedevent.delete()
        except (WebpageMediaEmptyError, MediaEmptyError, WebpageCurlFailedError):
            return await edit_or_reply(
                zedevent,
                f"**⌔∮ عـذراً عليـك الـرد ع صـوره او ميـديـا  ⪼  `.اضف صورة الفحص` <بالرد ع الصـوره او الميـديـا> ",
            )
    else:
        await edit_or_reply(
            zedevent,
            caption,
        )


zed_temp = """

**~ سۅٛࢪس سيدثۅٛن يعمݪ بنجاެح** 

**~ اެسِمِكَ : {mention}** ٫
**~ اެصداެࢪ اެݪتيݪيثۅٛن : `{pyver}`** ٫
**‌‎~ اެصداެࢪ اެݪسۅٛࢪس : {telever}**٫
**~ بَاެيَثَۅٛنِ :  {pyver}** ٫
**~ اެݪمِنِصِهِ : 𐌺᧐yᥱδ
‌‎**اެݪسِࢪعَة `{ping}`** ٫
**~ اެݪۅٛقت :`{uptime}`** ٫
‌‎**تَاެࢪيَخِ اެݪتَنِصِيَبَ  {zedda}
**𖠄 𝙨𝙤𝙪𝙍𝙘𝙚 𝙈𝙖𝙏𝙍𝙞𝙭 ⌁ 𖠄**"""







import random
import re
import time
import psutil
from datetime import datetime
from platform import python_version

import requests
from telethon import version
from telethon.errors.rpcerrorlist import (
    MediaEmptyError,
    WebpageCurlFailedError,
    WebpageMediaEmptyError,
)
from telethon.events import CallbackQuery

from . import StartTime, zedub, tepversion

from ..Config import Config
from ..core.managers import edit_or_reply
from ..helpers.functions import zedalive, check_data_base_heal_th, get_readable_time
from ..helpers.utils import reply_id
from ..sql_helper.globals import gvarstatus
from . import mention

plugin_category = "العروض"
STATS = gvarstatus("Z_STATS") or "فحص"


@zedub.zed_cmd(pattern=f"{STATS}$")
async def amireallyalive(event):
    reply_to_id = await reply_id(event)
    uptime = await get_readable_time((time.time() - StartTime))
    boot_time_timestamp = psutil.boot_time()
    bt = datetime.fromtimestamp(boot_time_timestamp)
    start = datetime.now()
    zedevent = await edit_or_reply(event, "**⎆┊جـاري .. فحـص البـوت الخـاص بك**")
    end = datetime.now()
    ms = (end - start).microseconds / 1000
    _, check_sgnirts = check_data_base_heal_th()
    if gvarstatus("z_date") is not None:
        zzd = gvarstatus("z_date")
        zzt = gvarstatus("z_time")
        zedda = f"{zzd}┊{zzt}"
    else:
        zedda = f"{bt.year}/{bt.month}/{bt.day}"
    Z_EMOJI = gvarstatus("ALIVE_EMOJI") or "✾╿"
    ALIVE_TEXT = gvarstatus("ALIVE_TEXT") or "**بـوت  ماتركـس 𝙈𝙖𝙏𝙍𝙞𝙭 ⌁  يعمـل .. بنجـاح ☑️ 𓆩**"
    ZED_IMG = gvarstatus("ALIVE_PIC")
    zed_caption = gvarstatus("ALIVE_TEMPLATE") or zed_temp
    caption = zed_caption.format(
        ALIVE_TEXT=ALIVE_TEXT,
        Z_EMOJI=Z_EMOJI,
        mention=mention,
        uptime=uptime,
        zedda=zedda,
        telever=version.__version__,
        zdver=tepversion,
        pyver=python_version(),
        dbhealth=check_sgnirts,
        ping=ms,
    )
    if ZED_IMG:
        ZED = [x for x in ZED_IMG.split()]
        PIC = random.choice(ZED)
        try:
            await event.client.send_file(
                event.chat_id, PIC, caption=caption, reply_to=reply_to_id
            )
            await zedevent.delete()
        except (WebpageMediaEmptyError, MediaEmptyError, WebpageCurlFailedError):
            return await edit_or_reply(
                zedevent,
                f"**⌔∮ عـذراً عليـك الـرد ع صـوره او ميـديـا  ⪼  `.اضف صورة الفحص` <بالرد ع الصـوره او الميـديـا> ",
            )
    else:
        await edit_or_reply(
            zedevent,
            caption,
        )


zed_temp = """{ALIVE_TEXT}

**{Z_EMOJI} قاعـدة البيانـات : ** سريعـة للغايـة 🚀 
**{Z_EMOJI} إصــدار المكتبــة :** `{telever}`
**{Z_EMOJI} إصــدار الـسـورس : ** `{zdver}`
**{Z_EMOJI} إصــدار بايـثون : ** `{pyver}`
**{Z_EMOJI} وَقـت التشغِيـل : ** `{uptime}`
**{Z_EMOJI} منــصـة التنصِيب :** `RENDAR`
**{Z_EMOJI} تاريــخ التنصيـب : ** `{zedda}`
**{Z_EMOJI} المالـك : ** {mention}
**{Z_EMOJI} قنـاتنا :** [اضغـط هنـا](https://t.me/BDB0B)"""


@zedub.zed_cmd(
    pattern="الفحص$",
    command=("الفحص", plugin_category),
    info={
        "header": "- لـ التحـقق من ان البـوت يعمـل بنجـاح .. بخـاصيـة الانـلايـن ✓",
        "الاسـتخـدام": [
            "{tr}الفحص",
        ],
    },
)
async def amireallyialive(event):
    "A kind of showing bot details by your inline bot"
    reply_to_id = await reply_id(event)
    Z_EMOJI = gvarstatus("ALIVE_EMOJI") or "✾╿"
    zed_caption = "**- بوت ماتركـس MaTrix يعمـل بنجـاح 🌿 .. **\n"
    zed_caption += f"**{Z_EMOJI} إصـــدار تليثـون : ** `{version.__version__}\n`"
    zed_caption += f"**{Z_EMOJI} إصــدار ماتركـس : ** `{tepversion}`\n"
    zed_caption += f"**{Z_EMOJI} إصــدار بايـثـون : ** `{python_version()}\n`"
    zed_caption += f"**{Z_EMOJI} المالـك : ** {mention}\n"
    results = await event.client.inline_query(Config.TG_BOT_USERNAME, zed_caption)
    await results[0].click(event.chat_id, reply_to=reply_to_id, hide_via=True)
    await event.delete()


@zedub.tgbot.on(CallbackQuery(data=re.compile(b"stats")))
async def on_plug_in_callback_query_handler(event):
    statstext = await zedalive(StartTime)
    await event.answer(statstext, cache_time=0, alert=True)















