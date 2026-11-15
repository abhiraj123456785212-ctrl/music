
import asyncio
import importlib
import sys
from pathlib import Path

from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from AnonXMusic import LOGGER, app, userbot
from AnonXMusic.core.call import Anony
from AnonXMusic.misc import sudo
from AnonXMusic.plugins import ALL_MODULES
from AnonXMusic.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS


# ==========================================
# YOUTUBE API SERVER
# ==========================================

# Project root folder (jahan youtube_api.py rakhi hai)
ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import youtube_api


def start_youtube_api():
    try:
        youtube_api.start_server()
        LOGGER("YouTube API").info(
            "YouTube API started successfully on port 9898"
        )
    except Exception as e:
        LOGGER("YouTube API").error(
            f"Failed to start YouTube API: {e}"
        )


def stop_youtube_api():
    try:
        youtube_api.stop_server()
        LOGGER("YouTube API").info("YouTube API stopped")
    except Exception as e:
        LOGGER("YouTube API").error(
            f"Failed to stop YouTube API: {e}"
        )


# ==========================================
# MAIN BOT
# ==========================================

async def init():

    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        LOGGER(__name__).error(
            "Assistant client variables not defined, exiting..."
        )
        exit()

    # Start YouTube API automatically
    start_youtube_api()

    await sudo()

    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)

        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)

    except Exception as e:
        LOGGER(__name__).warning(
            f"Could not load banned users: {e}"
        )

    await app.start()

    for all_module in ALL_MODULES:
        importlib.import_module(
            "AnonXMusic.plugins" + all_module
        )

    LOGGER("AnonXMusic.plugins").info(
        "Successfully Imported Modules..."
    )

    await userbot.start()
    await Anony.start()

    try:
        await Anony.stream_call(
            "https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4"
        )

    except NoActiveGroupCall:
        LOGGER("AnonXMusic").error(
            "Please turn on the videochat of your log group\\channel.\\n\\nStopping Bot..."
        )
        await app.stop()
        stop_youtube_api()
        exit()

    except Exception:
        pass

    await Anony.decorators()

    LOGGER("AnonXMusic").info(
        "Aera Music Bot Started Successfully!"
    )

    try:
        await idle()

    finally:
        try:
            await app.stop()
        except Exception:
            pass

        stop_youtube_api()

        LOGGER("AnonXMusic").info(
            "Stopping AnonX Music Bot..."
        )


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())
