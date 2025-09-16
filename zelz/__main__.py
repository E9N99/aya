import sys
import asyncio
import os
import zelz
from zelz import BOTLOG_CHATID, HEROKU_APP, PM_LOGGER_GROUP_ID
from telethon import functions
from .Config import Config
from .core.logger import logging
from .core.session import zedub
from .utils import mybot, autoname, autovars, saves, supscrips
from .utils import add_bot_to_logger_group, setup_bot, startupmessage, verifyLoggerGroup

LOGS = logging.getLogger("BiLaL")
cmdhr = Config.COMMAND_HAND_LER

try:
    LOGS.info("⌭ جـارِ تحميـل الملحقـات ⌭")
    zedub.loop.run_until_complete(autovars())
    LOGS.info("✓ تـم تحميـل الملحقـات .. بنجـاح ✓")
except Exception as e:
    LOGS.error(f"- {e}")

if not Config.ALIVE_NAME:
    try:
        LOGS.info("⌭ بـدء إضافة الاسـم التلقـائـي ⌭")
        zedub.loop.run_until_complete(autoname())
        LOGS.info("✓ تـم إضافة فار الاسـم .. بـنجـاح ✓")
    except Exception as e:
        LOGS.error(f"- {e}")

try:
    LOGS.info("⌭ بـدء تنزيـل ماتركـس ⌭")
    zedub.loop.run_until_complete(setup_bot())
    LOGS.info("✓ تـم تنزيـل ماتركـس .. بـنجـاح ✓")
except Exception as e:
    LOGS.error(f"{str(e)}")
    sys.exit()

class CatCheck:
    def init(self):
        self.sucess = True
Catcheck = CatCheck()

try:
    LOGS.info("⌭ بـدء إنشـاء البـوت التلقـائـي ⌭")
    zedub.loop.run_until_complete(mybot())
    LOGS.info("✓ تـم إنشـاء البـوت .. بـنجـاح ✓")
except Exception as e:
    LOGS.error(f"- {e}")

try:
    LOGS.info("⌭ جـارِ تفعيـل الاشتـراك ⌭")
    zedub.loop.create_task(saves())
    LOGS.info("✓ تـم تفعيـل الاشتـراك .. بنجـاح ✓")
except Exception as e:
    LOGS.error(f"- {e}")

try:
    LOGS.info("⌭ جـارِ تفعيـل الاشتـراك ⌭")
    zedub.loop.create_task(supscrips())
    LOGS.info("✓ تـم تفعيـل الاشتـراك .. بنجـاح ✓")
except Exception as e:
    LOGS.error(f"- {e}")

async def load_plugins_with_delay(plugin_folder, chunk_size=20, delay=2):
    LOGS.info(f"⌭ جـارِ تحميـل ملحقـات {plugin_folder} ⌭")
    
    path = f"./{plugin_folder}"
    if not os.path.exists(path):
        LOGS.warning(f"المجلد {plugin_folder} غير موجود!")
        return
    
    plugins = [
        f"{plugin_folder}.{file[:-3]}"
        for file in os.listdir(path)
        if file.endswith(".py") and not file.startswith("_")
    ]
    
    total_plugins = len(plugins)
    LOGS.info(f"⌭ العدد الإجمالي للملحقات: {total_plugins} ⌭")
    
    for i in range(0, total_plugins, chunk_size):
        chunk = plugins[i:i + chunk_size]
        
        for plugin in chunk:
            try:
                zedub.load_plugin(plugin)
                LOGS.info(f"✓ تم تحميل: {plugin} ✓")
            except Exception as e:
                LOGS.error(f"خطأ في تحميل {plugin}: {str(e)}")
        
        if i + chunk_size < total_plugins:
            LOGS.info(f"⌭ تم تحميل {min(i + chunk_size, total_plugins)} من {total_plugins} ⌭")
            LOGS.info(f"⌭ انتظار {delay} ثانية قبل المتابعة ⌭")
            await asyncio.sleep(delay)
    
    LOGS.info(f"✓ تم تحميل جميع ملحقات {plugin_folder} بنجاح! ✓")

async def startup_process():
    await verifyLoggerGroup()
    
    await load_plugins_with_delay("plugins")
    await load_plugins_with_delay("assistant")
    
    await verifyLoggerGroup()
    await add_bot_to_logger_group(BOTLOG_CHATID)
    if PM_LOGGER_GROUP_ID != -100:
        await add_bot_to_logger_group(PM_LOGGER_GROUP_ID)
    await startupmessage()
    Catcheck.sucess = True
    return

zedub.loop.run_until_complete(startup_process())

if len(sys.argv) not in (1, 3, 4):
    zedub.disconnect()
elif not Catcheck.sucess:
    if HEROKU_APP is not None:
        HEROKU_APP.restart()
else:
    try:
        zedub.run_until_disconnected()
    except ConnectionError:
        pass
