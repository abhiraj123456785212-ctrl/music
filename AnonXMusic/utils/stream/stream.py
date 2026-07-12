import os
from random import randint
from typing import Union, Optional

from pyrogram.types import InlineKeyboardMarkup

import config
from AnonXMusic import Carbon, YouTube, app
from AnonXMusic.core.call import Anony
from AnonXMusic.misc import db
from AnonXMusic.utils.database import add_active_video_chat, is_active_chat
from AnonXMusic.utils.exceptions import AssistantErr
from AnonXMusic.utils.inline import aq_markup, close_markup, stream_markup
from AnonXMusic.utils.pastebin import AnonyBin
from AnonXMusic.utils.stream.queue import put_queue, put_queue_index
from AnonXMusic.utils.thumbnails import get_thumb


# ✅ New: Quality mapping for stream
QUALITY_MAP = {
    "low": {"audio_bitrate": 64, "video_height": 360},
    "medium": {"audio_bitrate": 128, "video_height": 480},
    "high": {"audio_bitrate": 192, "video_height": 720},
    "ultra": {"audio_bitrate": 256, "video_height": 1080},
}
DEFAULT_QUALITY = "medium"


async def stream(
    _,
    mystic,
    user_id,
    result,
    chat_id,
    user_name,
    original_chat_id,
    video: Union[bool, str] = None,
    streamtype: Union[bool, str] = None,
    spotify: Union[bool, str] = None,
    forceplay: Union[bool, str] = None,
    quality: str = DEFAULT_QUALITY,  # ✅ New: quality parameter
):
    if not result:
        return
    if forceplay:
        await Anony.force_stop_stream(chat_id)
    
    # ✅ Validate quality
    if quality not in QUALITY_MAP:
        quality = DEFAULT_QUALITY
    
    quality_info = QUALITY_MAP[quality]
    
    if streamtype == "playlist":
        msg = f"{_['play_19']}\n\n"
        count = 0
        first_song_played = False
        for search in result:
            if int(count) == config.PLAYLIST_FETCH_LIMIT:
                continue
            try:
                (
                    title,
                    duration_min,
                    duration_sec,
                    thumbnail,
                    vidid,
                ) = await YouTube.details(search, False if spotify else True)
            except:
                continue
            if str(duration_min) == "None":
                continue
            if duration_sec > config.DURATION_LIMIT:
                continue
                
            if await is_active_chat(chat_id):
                # ✅ Add quality to queue
                await put_queue(
                    chat_id,
                    original_chat_id,
                    f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if video else "audio",
                    quality=quality,  # ✅ Pass quality
                )
                position = len(db.get(chat_id)) - 1
                count += 1
                msg += f"{count}. {title[:70]}\n"
                msg += f"{_['play_20']} {position}\n\n"
            else:
                if not forceplay:
                    db[chat_id] = []
                status = True if video else None
                try:
                    # ✅ Download with quality
                    file_path, direct, backup_url, quality_used = await YouTube.download(
                        vidid, mystic, video=status, videoid=True, quality=quality
                    )
                except Exception as e:
                    raise AssistantErr(_["play_14"])
                
                # ✅ Use buffer system
                await Anony.join_call(
                    chat_id,
                    original_chat_id,
                    file_path,
                    video=status,
                    image=thumbnail,
                    quality=quality,  # ✅ Pass quality
                    use_buffer=True,   # ✅ Use buffer
                )
                
                db[chat_id].append({
                    "title": title,
                    "dur": duration_min,
                    "streamtype": "video" if video else "audio",
                    "by": user_name,
                    "user_id": user_id,
                    "chat_id": original_chat_id,
                    "file": file_path,
                    "vidid": vidid,
                    "seconds": duration_sec,
                    "played": 0,
                    "quality": quality,  # ✅ Store quality
                })
                
                img = await get_thumb(vidid, user_id)
                button = stream_markup(_, chat_id)
                run = await app.send_photo(
                    original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{vidid}",
                        title[:23],
                        duration_min,
                        user_name,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
                first_song_played = True
                count += 1
                continue
        if count == 0:
            await mystic.edit_text(_["play_3"])
            return
        else:
            if count > 1 or (count == 1 and not first_song_played):
                link = await AnonyBin(msg)
                lines = msg.count("\n")
                if lines >= 17:
                    car = os.linesep.join(msg.split(os.linesep)[:17])
                else:
                    car = msg
                carbon = await Carbon.generate(car, randint(100, 10000000))
                upl = close_markup(_)
                await app.send_photo(
                    original_chat_id,
                    photo=carbon,
                    caption=_["play_21"].format(count, link),
                    reply_markup=upl,
                )
            await mystic.delete()
        return
        
    elif streamtype == "youtube":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        duration_min = result["duration_min"]
        thumbnail = result["thumb"]
        status = True if video else None
        
        # ✅ Download with quality
        file_path, direct, backup_url, quality_used = await YouTube.download(
            vidid, mystic, videoid=True, video=status, quality=quality
        )
        if not file_path:
            raise AssistantErr(_["play_14"])
        
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path if direct else f"vid_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
                quality=quality,  # ✅ Pass quality
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            
            # ✅ Use buffer system
            await Anony.join_call(
                chat_id,
                original_chat_id,
                file_path,
                video=status,
                image=thumbnail,
                quality=quality,  # ✅ Pass quality
                use_buffer=True,   # ✅ Use buffer
            )
            
            await put_queue(
                chat_id,
                original_chat_id,
                file_path if direct else f"vid_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
                quality=quality,  # ✅ Pass quality
            )
            
            img = await get_thumb(vidid, user_id)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{vidid}",
                    title[:23],
                    duration_min,
                    user_name,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
            db[chat_id][0]["quality"] = quality  # ✅ Store quality
            
    elif streamtype == "soundcloud":
        file_path = result["filepath"]
        title = result["title"]
        duration_min = result["duration_min"]
        
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
                quality=quality,  # ✅ Pass quality
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            
            # ✅ Use buffer system
            await Anony.join_call(
                chat_id, 
                original_chat_id, 
                file_path, 
                video=None,
                quality=quality,
                use_buffer=True,
            )
            
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
                forceplay=forceplay,
                quality=quality,  # ✅ Pass quality
            )
            
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.SOUNCLOUD_IMG_URL,
                caption=_["stream_1"].format(
                    config.SUPPORT_CHAT, title[:23], duration_min, user_name
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            db[chat_id][0]["quality"] = quality
            
    elif streamtype == "telegram":
        file_path = result["path"]
        link = result["link"]
        title = (result["title"]).title()
        duration_min = result["dur"]
        status = True if video else None
        
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if video else "audio",
                quality=quality,  # ✅ Pass quality
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            
            # ✅ Use buffer system
            await Anony.join_call(
                chat_id, 
                original_chat_id, 
                file_path, 
                video=status,
                quality=quality,
                use_buffer=True,
            )
            
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
                quality=quality,  # ✅ Pass quality
            )
            
            if video:
                await add_active_video_chat(chat_id)
            
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.TELEGRAM_VIDEO_URL if video else config.TELEGRAM_AUDIO_URL,
                caption=_["stream_1"].format(link, title[:23], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            db[chat_id][0]["quality"] = quality
            
    elif streamtype == "live":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        thumbnail = result["thumb"]
        duration_min = "Live Track"
        status = True if video else None
        
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
                quality=quality,  # ✅ Pass quality
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            
            # ✅ Get video with quality
            n, file_path = await YouTube.video(link, quality=quality)
            if n == 0:
                raise AssistantErr(_["str_3"])
            
            # ✅ Use buffer system
            await Anony.join_call(
                chat_id,
                original_chat_id,
                file_path,
                video=status,
                image=thumbnail if thumbnail else None,
                quality=quality,
                use_buffer=True,
            )
            
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
                quality=quality,  # ✅ Pass quality
            )
            
            img = await get_thumb(vidid, user_id)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{vidid}",
                    title[:23],
                    duration_min,
                    user_name,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            db[chat_id][0]["quality"] = quality
            
    elif streamtype == "index":
        link = result
        title = "ɪɴᴅᴇx ᴏʀ ᴍ3ᴜ8 ʟɪɴᴋ"
        duration_min = "00:00"
        
        if await is_active_chat(chat_id):
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video" if video else "audio",
                quality=quality,  # ✅ Pass quality
            )
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await mystic.edit_text(
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            
            # ✅ Use buffer system
            await Anony.join_call(
                chat_id,
                original_chat_id,
                link,
                video=True if video else None,
                quality=quality,
                use_buffer=True,
            )
            
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video" if video else "audio",
                forceplay=forceplay,
                quality=quality,  # ✅ Pass quality
            )
            
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.STREAM_IMG_URL,
                caption=_["stream_2"].format(user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            db[chat_id][0]["quality"] = quality
            await mystic.delete()


# ✅ New: Function to get stream quality info
def get_quality_info(quality: str = DEFAULT_QUALITY) -> dict:
    """Get quality information for a given quality level"""
    if quality not in QUALITY_MAP:
        quality = DEFAULT_QUALITY
    return QUALITY_MAP[quality]


# ✅ New: Function to format quality for display
def format_quality(quality: str) -> str:
    """Format quality level for display"""
    if quality not in QUALITY_MAP:
        quality = DEFAULT_QUALITY
    info = QUALITY_MAP[quality]
    if "video_height" in info:
        return f"{quality.capitalize()} ({info['audio_bitrate']}kbps / {info['video_height']}p)"
    return f"{quality.capitalize()} ({info['audio_bitrate']}kbps)"


# ✅ New: Function to get stream with quality
async def get_stream_with_quality(
    vidid: str,
    quality: str = DEFAULT_QUALITY,
    video: bool = False,
) -> dict:
    """Get stream URL with specific quality"""
    if quality not in QUALITY_MAP:
        quality = DEFAULT_QUALITY
    
    # This function can be used to get stream info without playing
    # Returns stream info with quality details
    
    result = await YouTube.get_stream_with_buffer(
        vidid,
        videoid=True,
        quality=quality,
        video=video
    )
    
    if result.get("success"):
        result["quality_info"] = QUALITY_MAP[quality]
        result["quality_level"] = quality
    
    return result
