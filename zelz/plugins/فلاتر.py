import asyncio
import contextlib
import io
import os
import random
import string

from PIL import Image, ImageFilter
from telethon.tl.functions.messages import ImportChatInviteRequest as Get

from . import Convert, zedub

from ..core.managers import edit_delete, edit_or_reply
from ..helpers import asciiart, zed_meeme, zed_meme, media_type, meme_type
from ..helpers.functions import (
    add_frame,
    crop,
    flip_image,
    grayscale,
    invert_colors,
    mirror_file,
    solarize,
)
from ..helpers.utils import reply_id
from ..sql_helper.globals import addgvar, gvarstatus

plugin_category = "الادوات"


def random_color():
    number_of_colors = 2
    return [
        "#" + "".join(random.choice("0123456789ABCDEF") for _ in range(6))
        for _ in range(number_of_colors)
    ]


FONTS = "1. `zira.ttf`\n2. `Starjedi.ttf`\n3. `Papernotes.ttf`\n4. `Terserah.ttf`\n5. `Dream MMA.ttf`\n6. `EASPORTS15.ttf`\n7. `KGMissKindergarten.ttf`\n8. `212 Orion Sans PERSONAL USE.ttf`\n9. `PEPSI_pl.ttf`\n10. `Paskowy.ttf`\n11. `Cream Cake.otf`\n12. `Hello Valentina.ttf`\n13. `Alien-Encounters-Regular.ttf`\n14. `Linebeam.ttf`\n15. `EASPORTS15.ttf`\n16. `عربي`"
font_list = [
    "zira.ttf",
    "Starjedi.ttf",
    "Papernotes.ttf",
    "Terserah.ttf",
    "Dream MMA.ttf",
    "EASPORTS15.ttf",
    "KGMissKindergarten.ttf",
    "212 Orion Sans PERSONAL USE.ttf",
    "PEPSI_pl.ttf",
    "Paskowy.ttf",
    "Cream Cake.otf",
    "Hello Valentina.ttf",
    "Alien-Encounters-Regular.ttf",
    "Linebeam.ttf",
    "EASPORTS15.ttf",
    "zarz.ttf",
]


@zedub.zed_cmd(
    pattern="فرام(ف|م)?$",
    command=("فرام", plugin_category),
    info={
        "header": "لـ اضافة فرام للصور والملصقات",
        "امـر اضـافي": {
            "ف": "لـ ارسال الملف ع شكل ملف وليس صورة",
        },
        "الاستخـدام": [
            "{tr}فرام",
        ],
    },
)
async def maccmd(event):  # sourcery no-metrics
    # sourcery skip: low-code-quality
    "لـ اضافة فرام للصور والملصقات"
    reply = await event.get_reply_message()
    mediatype = await media_type(reply)
    if not reply or not mediatype or mediatype not in ["Photo", "Sticker"]:
        return await edit_delete(event, "**⎉╎بالـرد ع صورة او ملصق لعمل فرام ..**")
    if mediatype == "Sticker" and reply.document.mime_type == "application/i-tgsticker":
        return await edit_delete(
            event,
            "**⎉╎بالـرد ع صورة او ملصق لعمل فرام**\n**⎉╎الملصقات المتحركه غير مدعومه ...!!**",
        )
    catevent = await event.edit("**⎉╎جـارِ عمل فرام لملف الميديا ...**")
    args = event.pattern_match.group(1)
    force = bool(args)
    try:
        imag = await Convert.to_image(
            catevent, reply, dirct="./temp", file="pframe.png", noedits=True
        )
        if imag[1] is None:
            return await edit_delete(
                imag[0], "**⎉╎عـذراً .. لم استطـع استخـراج صـوره من ملـف الميـديا هـذا ؟!**"
            )
        image = Image.open(imag[1])
    except Exception as e:
        return await edit_delete(catevent, f"**⎉╎خطـأ في الصـورة :**\n__{e}__")
    wid, hgt = image.size
    img = Image.new("RGBA", (wid, hgt))
    scale = min(wid // 100, hgt // 100)
    temp = Image.new("RGBA", (wid + scale * 40, hgt + scale * 40), "#fff")
    if image.mode == "RGBA":
        img.paste(image, (0, 0), image)
        newimg = Image.new("RGBA", (wid, hgt))
        for N in range(wid):
            for O in range(hgt):
                if img.getpixel((N, O)) != (0, 0, 0, 0):
                    newimg.putpixel((N, O), (0, 0, 0))
    else:
        img.paste(image, (0, 0))
        newimg = Image.new("RGBA", (wid, hgt), "black")
    newimg = newimg.resize((wid + scale * 5, hgt + scale * 5))
    temp.paste(
        newimg,
        ((temp.width - newimg.width) // 2, (temp.height - newimg.height) // 2),
        newimg,
    )
    temp = temp.filter(ImageFilter.GaussianBlur(scale * 5))
    temp.paste(
        img, ((temp.width - img.width) // 2, (temp.height - img.height) // 2), img
    )
    output = io.BytesIO()
    output.name = (
        "-".join(
            "".join(random.choice(string.hexdigits) for img in range(event))
            for event in [5, 4, 3, 2, 1]
        )
        + ".png"
    )
    temp.save(output, "PNG")
    output.seek(0)
    await event.client.send_file(
        event.chat_id, output, reply_to=reply, force_document=force
    )
    await catevent.delete()


@zedub.zed_cmd(
    pattern="(حقوق|اطبع)(?:\\s|$)([\\s\\S]*)",
    command=("حقوق", plugin_category),
    info={
        "header": "لـ عمل حقوق على ملف الميديا",
        "الوصـف": "اضافة نص لملف الميديا وجعلها بحقوقك",
        "الخيـارات": {
            "حقوق": "Output will be image.",
            "اطبع": "Output will be sticker.",
        },
        "الاستخـدام": [
            "{tr}mmf toptext ; bottomtext",
            "{tr}mms toptext ; bottomtext",
        ],
        "مثــال": [
            "{tr}mmf hello (only on top)",
            "{tr}mmf ; hello (only on bottom)",
            "{tr}mmf hi ; hello (both on top and bottom)",
        ],
    },
)
async def memes(event):
    "لكتابة نص ع ملف الميديا"
    cmd = event.pattern_match.group(1)
    zedinput = event.pattern_match.group(2)
    reply = await event.get_reply_message()
    mediatype = meme_type(reply)
    if not reply:
        return await edit_delete(event, "**⎉╎قم بالـرد ع وسـائط مدعومـه ...**")
    catid = await reply_id(event)
    if not zedinput:
        return await edit_delete(
            event, "**⎉╎حقوق + نص بالـرد ع ملف ميديا مدعوم ...**"
        )
    if ";" in zedinput:
        top, bottom = zedinput.split(";", 1)
    else:
        top = zedinput
        bottom = ""
    if not os.path.isdir("./temp"):
        os.mkdir("./temp")
    output = await Convert.to_image(
        event, reply, dirct="./temp", file="mmf.png", rgb=True
    )
    if output[1] is None:
        return await edit_delete(
            output[0], "**⎉╎عـذراً .. لم استطـع استخـراج صـوره من ملـف الميـديا هـذا ؟!**"
        )
    meme_file = output[1]
    meme = os.path.join("./temp", "catmeme.jpg")
    if gvarstatus("ZED_FONTS") is None:
        ZED_FONTS = "zelz/helpers/styles/Terserah.ttf"
    else:
        ZED_FONTS = gvarstatus("ZED_FONTS")
    if max(len(top), len(bottom)) < 21:
        await zed_meme(ZED_FONTS, top, bottom, meme_file, meme)
    else:
        await zed_meeme(top, bottom, ZED_FONTS, meme_file, meme)
    if mediatype == "Static Sticker":
        meme = (await Convert.to_sticker(event, meme, file="memes.webp", noedits=True))[
            1
        ]
    if mediatype == "Gif":
        meme = (await Convert.to_gif(event, meme, file="mmg.mp4", noedits=True))[
            1
        ]
    if mediatype in ["Video", "Round Video"]:
        meme = (await Convert.to_gif(event, meme, file="mmg.mp4", noedits=True))[
            1
        ]
    if mediatype == "Video Sticker":
        meme = (await Convert.to_webm(event, meme, file="memes.webm", noedits=True))[
            1
        ]
    if mediatype == "Animated Sticker":
        meme = (await Convert.to_sticker(event, meme, file="memes.webp", noedits=True))[
            1
        ]
    await event.client.send_file(
        event.chat_id, meme, reply_to=catid, force_document=False
    )
    await output[0].delete()
    for files in (meme, meme_file):
        if files and os.path.exists(files):
            os.remove(files)


@zedub.zed_cmd(
    pattern="الخطوط(?:\\s|$)([\\s\\S]*)",
    command=("الخطوط", plugin_category),
    info={
        "header": "لعـرض قائمـة خطـوط ماتركس",
        "الاستخـدام": "{tr}.الخطوط",
    },
)
async def lang(event):
    "لعـرض قائمـة خطـوط زدثــون"
    input_str = event.pattern_match.group(1)
    if not input_str:
        await event.edit(f"**⎉╎قائمـة خطـوط زدثــون هـي :-**\n**قم بنسخ اسم الخط ثم ارسل (.خط + اسم الخط)**\n\n{FONTS}")
        return
    else:
        return


@zedub.zed_cmd(
    pattern="خطوط(?:\\s|$)([\\s\\S]*)",
    command=("خطوط", plugin_category),
    info={
        "header": "لـ تغييـر خط كتابـة الحقـوق",
        "الاستخـدام": "{tr}.خط + اسم الخط",
        "مثــال": "{tr}خط Austein.ttf",
    },
)
async def lang(event):
    "لـ تغييـر خط كتابـة الحقـوق"
    input_str = event.pattern_match.group(1)
    if not input_str:
        await event.edit(f"**⎉╎قم بكتابة الامـر كالتالـي :**\n`.خطوط` **+ رقـم الخـط**\n**⎉╎لعـرض قائمـة الخطـوط ارسـل** `.الخطوط`")
        return
    if input_str == "عربي":
        arr = f"zelz/helpers/styles/zarz.ttf"
        addgvar("ZED_FONTS", arr)
        await edit_or_reply(event, "**⎉╎تم تغييـر خـط كتابـة الحقـوق الـى العربيـة**")
    if input_str not in font_list:
        catevent = await edit_or_reply(event, "**⎉╎قم بكتابه اسم الخط بشكل صحيح ...؟!**")
        await asyncio.sleep(1)
        await catevent.edit(f"**⎉╎قائمـة خطـوط زدثــون هـي :-**\n\n{FONTS}")
    else:
        arg = f"zelz/helpers/styles/{input_str}"
        addgvar("ZED_FONTS", arg)
        await edit_or_reply(event, f"**⎉╎تم تغييـر خـط كتابـة الحقـوق الـى :-** `{input_str}`")


@zedub.zed_cmd(
    pattern="رقميه(?:\\s|$)([\\s\\S]*)",
    command=("رقميه", plugin_category),
    info={
        "header": "لتحويـل الصـورة الى صـورة رقميـه",
        "الوصـف": "قم بجلب كود الالوان من جوجل اذا تريد المزيد من الالوان",
        "الاستخـدام": [
            "{tr}رقميه + كود اللون",
            "{tr}رقميه #080808",
            "{tr}رقميه",
        ],
    },
)
async def memes(event):
    "لتحويـل الصـورة الى صـورة رقميـه"
    zedinput = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    if not reply:
        return await edit_delete(event, "**⎉╎قم بالـرد ع وسـائط مدعومـه ...**")
    catid = await reply_id(event)
    if not os.path.isdir("./temp"):
        os.mkdir("./temp")
    jisanidea = None
    output = await Convert.to_image(
        event,
        reply,
        dirct="./temp",
        file="ascii.png",
    )
    if output[1] is None:
        return await edit_delete(
            output[0], "**⎉╎عـذراً .. لم استطـع استخـراج صـوره من ملـف الميـديا هـذا ؟!**"
        )
    meme_file = output[1]
    if output[2] in ["Round Video", "Gif", "Sticker", "Video"]:
        jisanidea = True
    outputfile = (
        os.path.join("./temp", "ascii_file.webp")
        if jisanidea
        else os.path.join("./temp", "ascii_file.jpg")
    )
    c_list = random_color()
    color1 = c_list[0]
    color2 = c_list[1]
    bgcolor = zedinput or "#080808"
    asciiart(meme_file, 0.3, 1.9, outputfile, color1, color2, bgcolor)
    await event.client.send_file(
        event.chat_id, outputfile, reply_to=catid, force_document=False
    )
    await output[0].delete()
    for files in (outputfile, meme_file):
        if files and os.path.exists(files):
            os.remove(files)


@zedub.zed_cmd(
    pattern="عكس الالوان$",
    command=("عكس الالوان", plugin_category),
    info={
        "header": "لعكس الوان صورة او ملصق",
        "الاستخـدام": "{tr}عكس الالوان",
    },
)
async def memes(event):
    reply = await event.get_reply_message()
    if not (reply and (reply.media)):
        await edit_or_reply(event, "**⎉╎قم بالـرد ع وسـائط مدعومـه ...**")
        return
    catid = await reply_id(event)
    if not os.path.isdir("./temp/"):
        os.mkdir("./temp/")
    jisanidea = None
    output = await Convert.to_image(
        event,
        reply,
        dirct="./temp",
        file="invert.png",
    )
    if output[1] is None:
        return await edit_delete(
            output[0], "**⎉╎عـذراً .. لم استطـع استخـراج صـوره من ملـف الميـديا هـذا ؟!**"
        )
    meme_file = output[1]
    if output[2] in ["Round Video", "Gif", "Sticker", "Video"]:
        jisanidea = True
    outputfile = (
        os.path.join("./temp", "invert.webp")
        if jisanidea
        else os.path.join("./temp", "invert.jpg")
    )
    await invert_colors(meme_file, outputfile)
    await event.client.send_file(
        event.chat_id, outputfile, force_document=False, reply_to=catid
    )
    await output[0].delete()
    for files in (outputfile, meme_file):
        if files and os.path.exists(files):
            os.remove(files)


@zedub.zed_cmd(
    pattern="سولار$",
    command=("سولار", plugin_category),
    info={
        "header": "To sun burn the colours of given image or sticker.",
        "الاستخـدام": "{tr}سولار",
    },
)
async def memes(event):
    "Sun burn of image."
    reply = await event.get_reply_message()
    if not reply:
        return await edit_delete(event, "**⎉╎قم بالـرد ع وسـائط مدعومـه ...**")
    catid = await reply_id(event)
    if not os.path.isdir("./temp"):
        os.mkdir("./temp")
    jisanidea = None
    output = await Convert.to_image(
        event,
        reply,
        dirct="./temp",
        file="solarize.png",
    )
    if output[1] is None:
        return await edit_delete(
            output[0], "**⎉╎عـذراً .. لم استطـع استخـراج صـوره من ملـف الميـديا هـذا ؟!**"
        )
    meme_file = output[1]
    if output[2] in ["Round Video", "Gif", "Sticker", "Video"]:
        jisanidea = True
    outputfile = (
        os.path.join("./temp", "solarize.webp")
        if jisanidea
        else os.path.join("./temp", "solarize.jpg")
    )
    await solarize(meme_file, outputfile)
    await event.client.send_file(
        event.chat_id, outputfile, force_document=False, reply_to=catid
    )
    await output[0].delete()
    for files in (outputfile, meme_file):
        if files and os.path.exists(files):
            os.remove(files)


@zedub.zed_cmd(
    pattern="ميرور$",
    command=("ميرور", plugin_category),
    info={
        "header": "shows you the reflection of the media file.",
        "الاستخـدام": "{tr}ميرور",
    },
)
async def memes(event):
    "shows you the reflection of the media file"
    reply = await event.get_reply_message()
    if not reply:
        return await edit_delete(event, "**⎉╎قم بالـرد ع وسـائط مدعومـه ...**")
    catid = await reply_id(event)
    if not os.path.isdir("./temp"):
        os.mkdir("./temp")
    jisanidea = None
    output = await Convert.to_image(
        event,
        reply,
        dirct="./temp",
        file="irotate.png",
    )
    if output[1] is None:
        return await edit_delete(
            output[0], "**⎉╎عـذراً .. لم استطـع استخـراج صـوره من ملـف الميـديا هـذا ؟!**"
        )
    meme_file = output[1]
    if output[2] in ["Round Video", "Gif", "Sticker", "Video"]:
        jisanidea = True
    outputfile = (
        os.path.join("./temp", "mirror_file.webp")
        if jisanidea
        else os.path.join("./temp", "mirror_file.jpg")
    )
    await mirror_file(meme_file, outputfile)
    await event.client.send_file(
        event.chat_id, outputfile, force_document=False, reply_to=catid
    )
    await output[0].delete()
    for files in (outputfile, meme_file):
        if files and os.path.exists(files):
            os.remove(files)


@zedub.zed_cmd(
    pattern="قلب الصوره$",
    command=("قلب الصوره", plugin_category),
    info={
        "header": "shows you the upside down image of the given media file.",
        "الاستخـدام": "{tr}قلب الصوره",
    },
)
async def memes(event):
    "shows you the upside down image of the given media file"
    reply = await event.get_reply_message()
    if not reply:
        return await edit_delete(event, "**⎉╎قم بالـرد ع وسـائط مدعومـه ...**")
    catid = await reply_id(event)
    if not os.path.isdir("./temp"):
        os.mkdir("./temp")
    jisanidea = None
    output = await Convert.to_image(
        event,
        reply,
        dirct="./temp",
        file="flip.png",
    )
    if output[1] is None:
        return await edit_delete(
            output[0], "**⎉╎عـذراً .. لم استطـع استخـراج صـوره من ملـف الميـديا هـذا ؟!**"
        )
    meme_file = output[1]
    if output[2] in ["Round Video", "Gif", "Sticker", "Video"]:
        jisanidea = True
    outputfile = (
        os.path.join("./temp", "flip_image.webp")
        if jisanidea
        else os.path.join("./temp", "flip_image.jpg")
    )
    await flip_image(meme_file, outputfile)
    await event.client.send_file(
        event.chat_id, outputfile, force_document=False, reply_to=catid
    )
    await output[0].delete()
    for files in (outputfile, meme_file):
        if files and os.path.exists(files):
            os.remove(files)


@zedub.zed_cmd(
    pattern="فلتر رصاصي$",
    command=("فلتر رصاصي", plugin_category),
    info={
        "header": "makes your media file to black and white.",
        "الاستخـدام": "{tr}فلتر رصاصي",
    },
)
async def memes(event):
    "makes your media file to black and white"
    reply = await event.get_reply_message()
    if not reply:
        return await edit_delete(event, "**⎉╎قم بالـرد ع وسـائط مدعومـه ...**")
    catid = await reply_id(event)
    if not os.path.isdir("./temp"):
        os.mkdir("./temp")
    jisanidea = None
    output = await Convert.to_image(
        event,
        reply,
        dirct="./temp",
        file="gray.png",
    )
    if output[1] is None:
        return await edit_delete(
            output[0], "**⎉╎عـذراً .. لم استطـع استخـراج صـوره من ملـف الميـديا هـذا ؟!**"
        )
    meme_file = output[1]
    if output[2] in ["Round Video", "Gif", "Sticker", "Video"]:
        jisanidea = True
    outputfile = (
        os.path.join("./temp", "grayscale.webp")
        if jisanidea
        else os.path.join("./temp", "grayscale.jpg")
    )
    await grayscale(meme_file, outputfile)
    await event.client.send_file(
        event.chat_id, outputfile, force_document=False, reply_to=catid
    )
    await output[0].delete()
    for files in (outputfile, meme_file):
        if files and os.path.exists(files):
            os.remove(files)


@zedub.zed_cmd(
    pattern="زوم ?([\\s\\S]*)",
    command=("زوم", plugin_category),
    info={
        "header": "zooms your media file,",
        "الاستخـدام": ["{tr}zoom", "{tr}zoom range"],
    },
)
async def memes(event):
    "zooms your media file."
    zedinput = event.pattern_match.group(1)
    zedinput = int(zedinput) if zedinput else 50
    reply = await event.get_reply_message()
    if not reply:
        return await edit_delete(event, "**⎉╎قم بالـرد ع وسـائط مدعومـه ...**")
    catid = await reply_id(event)
    if not os.path.isdir("./temp"):
        os.mkdir("./temp")
    jisanidea = None
    output = await Convert.to_image(
        event,
        reply,
        dirct="./temp",
        file="zoom.png",
    )
    if output[1] is None:
        return await edit_delete(
            output[0], "**⎉╎عـذراً .. لم استطـع استخـراج صـوره من ملـف الميـديا هـذا ؟!**"
        )
    meme_file = output[1]
    if output[2] in ["Round Video", "Gif", "Sticker", "Video"]:
        jisanidea = True
    outputfile = (
        os.path.join("./temp", "zoomimage.webp")
        if jisanidea
        else os.path.join("./temp", "zoomimage.jpg")
    )
    try:
        await crop(meme_file, outputfile, zedinput)
    except Exception as e:
        return await output[0].edit(f"`{e}`")
    try:
        await event.client.send_file(
            event.chat_id, outputfile, force_document=False, reply_to=catid
        )
    except Exception as e:
        return await output[0].edit(f"`{e}`")
    await output[0].delete()
    for files in (outputfile, meme_file):
        if files and os.path.exists(files):
            os.remove(files)


@zedub.zed_cmd(
    pattern="اطار ?([\\s\\S]*)",
    command=("اطار", plugin_category),
    info={
        "header": "make a frame for your media file.",
        "fill": "This defines the pixel fill value or color value to be applied. The default value is 0 which means the color is black.",
        "الاستخـدام": ["{tr}اطار", "{tr}frame range", "{tr}frame range ; fill"],
    },
)
async def memes(event):
    "make a frame for your media file"
    zedinput = event.pattern_match.group(1)
    if not zedinput:
        zedinput = "50"
    if ";" in str(zedinput):
        zedinput, colr = zedinput.split(";", 1)
    else:
        colr = 0
    zedinput = int(zedinput)
    try:
        colr = int(colr)
    except Exception as e:
        return await edit_delete(event, f"**⎉╎خطـأ :**\n`{e}`")
    reply = await event.get_reply_message()
    if not reply:
        return await edit_delete(event, "**⎉╎قم بالـرد ع وسـائط مدعومـه ...**")
    catid = await reply_id(event)
    if not os.path.isdir("./temp"):
        os.mkdir("./temp")
    jisanidea = None
    output = await Convert.to_image(
        event,
        reply,
        dirct="./temp",
        file="framed.png",
    )
    if output[1] is None:
        return await edit_delete(
            output[0], "**⎉╎عـذراً .. لم استطـع استخـراج صـوره من ملـف الميـديا هـذا ؟!**"
        )
    meme_file = output[1]
    if output[2] in ["Round Video", "Gif", "Sticker", "Video"]:
        jisanidea = True
    outputfile = (os.path.join("./temp", "framed.webp") if jisanidea else os.path.join("./temp", "framed.jpg"))
    try:
        await add_frame(meme_file, outputfile, zedinput, colr)
    except Exception as e:
        return await output[0].edit(f"`{e}`")
    try:
        await event.client.send_file(
            event.chat_id, outputfile, force_document=False, reply_to=catid
        )
    except Exception as e:
        return await output[0].edit(f"`{e}`")
    await event.delete()
    await output[0].delete()
    for files in (outputfile, meme_file):
        if files and os.path.exists(files):
            os.remove(files)









import asyncio
import aiohttp
import os
import shutil
import time
from bs4 import BeautifulSoup
from datetime import datetime
from telethon.utils import guess_extension
from urllib.parse import urlencode

from . import zedub
from ..Config import Config

ZELZAL_APP_ID = "6e65179ed1d879f3d905e28ef8803625"


@zedub.zed_cmd(pattern="صور (.*)")
async def _(event):
    if event.fwd_from:
        return
    start = datetime.now()
    await event.edit("**╮ ❐ جـاري البحث عن الصـور  ...𓅫╰**")
    zedthon = event.pattern_match.group(1)
    wzed_dir = os.path.join(
        Config.TMP_DOWNLOAD_DIRECTORY,
        zedthon
    )
    if not os.path.isdir(wzed_dir):
        os.makedirs(wzed_dir)
    input_url = "https://bots.shrimadhavuk.me/search/"
    headers = {"USER-AGENT": "UseTGBot"}
    url_lst = []
    async with aiohttp.ClientSession() as requests:
        data = {
            "q": zedthon,
            "app_id": ZELZAL_APP_ID,
            "p": "GoogleImages"
        }
        reponse = await requests.get(
            input_url,
            params=data,
            headers=headers
        )
        response = await reponse.json()
        for result in response["results"]:
            if len(url_lst) > 9:
                break
            caption = result.get("description")
            image_url = result.get("url")
            image_req_set = await requests.get(image_url)
            image_file_name = str(time.time()) + "" + guess_extension(
                image_req_set.headers.get("Content-Type")
            )
            image_save_path = os.path.join(
                wzed_dir,
                image_file_name
            )
            with open(image_save_path, "wb") as f_d:
                f_d.write(await image_req_set.read())
            url_lst.append(image_save_path)
    if not url_lst:
        await event.edit(f"**- اووبـس .. لم استطـع ايجـاد صـور عـن {zedthon} ؟!**\n**- حـاول مجـدداً واكتـب الكلمـه بشكـل صحيح**")
        return
    await event.reply(
        file=url_lst,
        parse_mode="html",
        force_document=True
    )
    for each_file in url_lst:
        os.remove(each_file)
    shutil.rmtree(wzed_dir, ignore_errors=True)
    end = datetime.now()
    ms = (end - start).seconds
    await event.edit(
        f"**- اكتمـل البحث عـن {zedthon} في {ms} ثانيـه ✓**",
        link_preview=False
    )
    await asyncio.sleep(5)
    await event.delete()



@zedub.zed_cmd(pattern="خلفيات (.*)")
async def _(event):
    if event.fwd_from:
        return
    start = datetime.now()
    await event.edit("**╮ ❐ جـاري البحث عن خلفيـات  ...𓅫╰**")
    zedthon = event.pattern_match.group(1)
    wzed_dir = os.path.join(
        Config.TMP_DOWNLOAD_DIRECTORY,
        zedthon
    )
    if not os.path.isdir(wzed_dir):
        os.makedirs(wzed_dir)
    input_url = "https://bots.shrimadhavuk.me/search/"
    headers = {"USER-AGENT": "UseTGBot"}
    url_lst = []
    async with aiohttp.ClientSession() as requests:
        data = {
            "q": zedthon,
            "app_id": ZELZAL_APP_ID,
            "p": "GoogleImages"
        }
        reponse = await requests.get(
            input_url,
            params=data,
            headers=headers
        )
        response = await reponse.json()
        for result in response["results"]:
            if len(url_lst) > 9:
                break
            caption = result.get("description")
            image_url = result.get("url")
            image_req_set = await requests.get(image_url)
            image_file_name = str(time.time()) + "" + guess_extension(
                image_req_set.headers.get("Content-Type")
            )
            image_save_path = os.path.join(
                wzed_dir,
                image_file_name
            )
            with open(image_save_path, "wb") as f_d:
                f_d.write(await image_req_set.read())
            url_lst.append(image_save_path)
    if not url_lst:
        await event.edit(f"**- اووبـس .. لم استطـع ايجـاد خلفيـات عـن {zedthon} ؟!**\n**- حـاول مجـدداً واكتـب الكلمـه بشكـل صحيح**")
        return
    await event.reply(
        file=url_lst,
        parse_mode="html",
        force_document=True
    )
    for each_file in url_lst:
        os.remove(each_file)
    shutil.rmtree(wzed_dir, ignore_errors=True)
    end = datetime.now()
    ms = (end - start).seconds
    await event.edit(
        f"**- اكتمـل البحث عـن {zedthon} في {ms} ثانيـه ✓**",
        link_preview=False
    )
    await asyncio.sleep(5)
    await event.delete()
