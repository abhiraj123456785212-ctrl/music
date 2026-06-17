import re
from os import getenv
from dotenv import load_dotenv
from pyrogram import filters

load_dotenv()

# ===================== PROXY (FIXED + SAFE) =====================
# ⚠️ Default OFF rakha hai (kyunki 127.0.0.1:9050 often NOT running)
# Agar WARP/TOR/SOCKS use karna hai tab enable karo manually

USE_PROXY = getenv("USE_PROXY", "false").lower() == "true"

PROXY = None

if USE_PROXY:
    PROXY = {
        "scheme": getenv("PROXY_SCHEME", "socks5"),
        "hostname": getenv("PROXY_HOST", "127.0.0.1"),
        "port": int(getenv("PROXY_PORT", "9050")),
    }
# =================================================================


# ===================== CORE CREDENTIALS =====================
API_ID = int(getenv("API_ID") or 0)
API_HASH = getenv("API_HASH", "")
BOT_TOKEN = getenv("BOT_TOKEN", "")

MONGO_DB_URI = getenv("MONGO_DB_URI", None)

YTPROXY_URL = getenv("YTPROXY_URL", "http://127.0.0.1:9898")
YT_API_KEY = getenv("YT_API_KEY", "my_secret_key_2025")

# ===================== LIMITS =====================
DURATION_LIMIT_MIN = int(getenv("DURATION_LIMIT", "300"))
PLAYLIST_FETCH_LIMIT = int(getenv("PLAYLIST_FETCH_LIMIT", "25"))

TG_AUDIO_FILESIZE_LIMIT = int(getenv("TG_AUDIO_FILESIZE_LIMIT", "204857600"))
TG_VIDEO_FILESIZE_LIMIT = int(getenv("TG_VIDEO_FILESIZE_LIMIT", "2073741824"))

PRIVATE_BOT_MODE_MEM = int(getenv("PRIVATE_BOT_MODE_MEM", "1"))

# ===================== IDS (SAFE HANDLING) =====================
LOGGER_ID = int(getenv("LOGGER_ID") or 0)
OWNER_ID = int(getenv("OWNER_ID") or 0)

# ===================== HEROKU =====================
HEROKU_APP_NAME = getenv("HEROKU_APP_NAME")
HEROKU_API_KEY = getenv("HEROKU_API_KEY")

# ===================== REPO =====================
UPSTREAM_REPO = getenv("UPSTREAM_REPO", "https://github.com/xbitcode/music.git")
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main")
GIT_TOKEN = getenv("GIT_TOKEN", None)

# ===================== LINKS =====================
SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/AeraxTi")
SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/AeraxTi")

# ===================== AUTO =====================
AUTO_LEAVING_ASSISTANT = getenv("AUTO_LEAVING_ASSISTANT", "false").lower() == "true"
ASSISTANT_LEAVE_TIME = int(getenv("ASSISTANT_LEAVE_TIME", "5400"))

# ===================== SPOTIFY =====================
SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET", "")

# ===================== STRING SESSIONS =====================
STRING1 = getenv("STRING_SESSION", None)
STRING2 = getenv("STRING_SESSION2", None)
STRING3 = getenv("STRING_SESSION3", None)
STRING4 = getenv("STRING_SESSION4", None)
STRING5 = getenv("STRING_SESSION5", None)

# ===================== CACHE =====================
CACHE_DURATION = int(getenv("CACHE_DURATION", "86400"))
CACHE_SLEEP = int(getenv("CACHE_SLEEP", "3600"))

# ===================== BOT DATA =====================
BANNED_USERS = filters.user()
adminlist = {}
lyrical = {}
votemode = {}
autoclean = []
confirmer = {}
file_cache = {}

# ===================== IMAGES =====================
START_IMG_URL = [
    "https://img.sanishtech.com/u/2bdda5910374ce9fa637bf12b4c29b5a.jpg"
]

PING_IMG_URL = getenv(
    "PING_IMG_URL",
    "https://telegra.ph/file/87f680aead03443f291b0.jpg"
)

PLAYLIST_IMG_URL = "https://graph.org/file/c95a687e777b55be1c792.jpg"
STATS_IMG_URL = "https://telegra.ph/file/edd388a42dd2c499fd868.jpg"

# ===================== UTILS =====================
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60**i for i, x in enumerate(reversed(stringt.split(":"))))


DURATION_LIMIT = int(time_to_seconds(f"{DURATION_LIMIT_MIN}:360"))

# ===================== VALIDATION =====================
if SUPPORT_CHANNEL and not re.match(r"^https?://", SUPPORT_CHANNEL):
    raise SystemExit("[ERROR] SUPPORT_CHANNEL must start with http/https")

if SUPPORT_CHAT and not re.match(r"^https?://", SUPPORT_CHAT):
    raise SystemExit("[ERROR] SUPPORT_CHAT must start with http/https")
