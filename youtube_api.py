
import os
import logging
import threading

from pathlib import Path
from datetime import datetime
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from werkzeug.serving import make_server
import yt_dlp


# ==========================================
# CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

VALID_API_KEY = os.getenv("YT_API_KEY", "").strip()

HOST = "127.0.0.1"
PORT = 9898


# ==========================================
# LOGGING
# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s"
)

logger = logging.getLogger("AERA_YOUTUBE_API")

app = Flask(__name__)


# ==========================================
# SERVER STATE
# ==========================================

_server = None
_server_thread = None
_server_lock = threading.Lock()


# ==========================================
# API KEY AUTHENTICATION
# ==========================================

def require_api_key(f):

    @wraps(f)
    def decorated(*args, **kwargs):

        if not VALID_API_KEY:
            logger.error("YT_API_KEY is not configured.")
            return jsonify({
                "status": "error",
                "message": "API key is not configured"
            }), 503

        api_key = request.headers.get("x-api-key", "")

        if not api_key or api_key != VALID_API_KEY:
            return jsonify({
                "status": "error",
                "message": "Invalid API key"
            }), 401

        return f(*args, **kwargs)

    return decorated


# ==========================================
# YT-DLP OPTIONS
# ==========================================

YDL_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "ignoreerrors": True,
    "extract_flat": False,
    "no_check_certificate": True,
    "prefer_insecure": True,
    "retries": 10,
    "socket_timeout": 60,

    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/142.0.0.0 Safari/537.36"
    ),

    "extractor_args": {
        "youtube": {
            "player_client": ["android", "web"],
            "skip": ["hls", "dash"],
        }
    }
}


# ==========================================
# VIDEO INFORMATION EXTRACTION
# ==========================================

def get_video_info(video_id):

    url = f"https://www.youtube.com/watch?v={video_id}"

    try:

        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:

            info = ydl.extract_info(
                url,
                download=False
            )

        if info is None:
            logger.error("No information found for %s", video_id)
            return None, None, None, None

        # Playlist fallback: use first video
        if "entries" in info:

            entries = info.get("entries") or []

            if not entries:
                return None, None, None, None

            info = entries[0]

            if info is None:
                return None, None, None, None

    except Exception as error:

        logger.error(
            "Extraction error for %s: %s",
            video_id,
            error
        )

        return None, None, None, None

    audio_url = None
    video_url = None

    best_audio_bitrate = 0
    best_video_height = 0

    formats = info.get("formats", [])

    # ======================================
    # FIND BEST AUDIO AND VIDEO
    # ======================================

    for fmt in formats:

        acodec = fmt.get("acodec")
        vcodec = fmt.get("vcodec")

        # Audio-only format
        if acodec != "none" and vcodec == "none":

            bitrate = (
                fmt.get("tbr")
                or fmt.get("abr")
                or 0
            )

            try:
                bitrate = float(bitrate)
            except (TypeError, ValueError):
                bitrate = 0

            if bitrate > best_audio_bitrate:

                best_audio_bitrate = bitrate
                audio_url = fmt.get("url")

        # Video format up to 720p
        if vcodec != "none":

            height = fmt.get("height") or 0

            try:
                height = int(height)
            except (TypeError, ValueError):
                height = 0

            if height <= 720 and height > best_video_height:

                best_video_height = height
                video_url = fmt.get("url")

    # ======================================
    # AUDIO FALLBACK
    # ======================================

    if not audio_url:

        for fmt in formats:

            if fmt.get("acodec") != "none":

                audio_url = fmt.get("url")

                if audio_url:
                    break

    # ======================================
    # VIDEO FALLBACK
    # ======================================

    if not video_url:

        for fmt in formats:

            if fmt.get("vcodec") != "none":

                video_url = fmt.get("url")

                if video_url:
                    break

    # ======================================
    # VIDEO DETAILS
    # ======================================

    title = info.get("title", "Unknown")

    duration = info.get("duration") or 0

    try:
        duration = int(duration)
    except (TypeError, ValueError):
        duration = 0

    minutes = duration // 60
    seconds = duration % 60

    duration_str = f"{minutes}:{seconds:02d}"

    logger.info(
        "Success: %s | Audio: %s | Video: %s",
        title,
        bool(audio_url),
        bool(video_url)
    )

    return audio_url, video_url, title, duration_str


# ==========================================
# VIDEO INFO API
# ==========================================

@app.route("/info/<video_id>", methods=["GET"])
@require_api_key
def get_info(video_id):

    if not video_id or len(video_id) != 11:

        return jsonify({
            "status": "error",
            "message": "Invalid video ID"
        }), 400

    try:

        audio_url, video_url, title, duration = (
            get_video_info(video_id)
        )

        if not audio_url and not video_url:

            return jsonify({
                "status": "error",
                "message": "No streams found"
            }), 404

        return jsonify({

            "status": "success",

            "audio_url": audio_url,
            "video_url": video_url,

            "title": title,
            "duration": duration,

            "video_id": video_id

        }), 200

    except Exception as error:

        logger.exception("Video API error")

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500


# ==========================================
# HEALTH CHECK
# ==========================================

@app.route("/health", methods=["GET"])
def health():

    return jsonify({

        "status": "ok",

        "service": "AERA YouTube API",

        "timestamp": datetime.now().isoformat()

    }), 200


# ==========================================
# START API SERVER
# ==========================================

def start_server():

    global _server
    global _server_thread

    with _server_lock:

        # Prevent duplicate server startup
        if _server_thread and _server_thread.is_alive():

            logger.info("YouTube API is already running.")
            return _server

        if not VALID_API_KEY:

            raise RuntimeError(
                "YT_API_KEY missing in project .env file."
            )

        logger.info("Starting AERA YouTube API...")
        logger.info("Host: %s", HOST)
        logger.info("Port: %s", PORT)

        _server = make_server(
            HOST,
            PORT,
            app,
            threaded=True
        )

        _server_thread = threading.Thread(
            target=_server.serve_forever,
            name="AERA-YouTube-API",
            daemon=True
        )

        _server_thread.start()

        logger.info(
            "YouTube API started successfully at http://%s:%s",
            HOST,
            PORT
        )

        return _server


# ==========================================
# STOP API SERVER
# ==========================================

def stop_server():

    global _server
    global _server_thread

    with _server_lock:

        if _server:

            logger.info("Stopping YouTube API...")

            _server.shutdown()
            _server.server_close()

            _server = None
            _server_thread = None

            logger.info("YouTube API stopped.")


# ==========================================
# STANDALONE EXECUTION
# ==========================================

if __name__ == "__main__":

    logger.info("Starting AERA YouTube API standalone...")

    try:

        start_server()

        if _server_thread:
            _server_thread.join()

    except KeyboardInterrupt:

        logger.info("Shutdown requested.")

        stop_server()

    except Exception:

        logger.exception("YouTube API startup failed.")
        raise
