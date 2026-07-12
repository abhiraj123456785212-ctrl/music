import asyncio
import glob
import os
import random
import re
from typing import Union, Optional, Dict, List
import yt_dlp
import aiohttp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from ytSearch import VideosSearch
from AnonXMusic import LOGGER
from AnonXMusic.utils.formatters import time_to_seconds
from config import YT_API_KEY, YTPROXY_URL as YTPROXY

logger = LOGGER(__name__)

def cookie_txt_file():
    try:
        folder_path = f"{os.getcwd()}/cookies"
        filename = f"{os.getcwd()}/cookies/logs.csv"
        txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
        if not txt_files:
            raise FileNotFoundError("No .txt files found in the specified folder.")
        cookie_txt_file = random.choice(txt_files)
        with open(filename, 'a') as file:
            file.write(f'Choosen File : {cookie_txt_file}\n')
        return f"""cookies/{str(cookie_txt_file).split("/")[-1]}"""
    except:
        return None


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        
        # ✅ New: Quality options
        self.QUALITY_OPTIONS = {
            "low": {
                "audio": "bestaudio[abr<=64]/bestaudio",
                "video": "bestvideo[height<=360]+bestaudio/best[height<=360]"
            },
            "medium": {
                "audio": "bestaudio[abr<=128][abr>=96]/bestaudio",
                "video": "bestvideo[height<=480]+bestaudio/best[height<=480]"
            },
            "high": {
                "audio": "bestaudio[abr<=192][abr>=160]/bestaudio",
                "video": "bestvideo[height<=720]+bestaudio/best[height<=720]"
            },
            "ultra": {
                "audio": "bestaudio[abr>=256]/bestaudio",
                "video": "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
            }
        }
        
        # ✅ New: Cache for stream URLs
        self.stream_cache = {}
        self.CACHE_EXPIRY = 3600  # 1 hour
        
        self.dl_stats = {
            "total_requests": 0,
            "okflix_downloads": 0,
            "cookie_downloads": 0,
            "existing_files": 0,
            "cache_hits": 0,       # ✅ New
            "cache_misses": 0      # ✅ New
        }

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if re.search(self.regex, link):
            return True
        else:
            return False

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset in (None,):
            return None
        return text[offset : offset + length]

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]

        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            if str(duration_min) == "None":
                duration_sec = 0
            else:
                duration_sec = int(time_to_seconds(duration_min))
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]
            
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
        return title

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]

        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            duration = result["duration"]
        return duration

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]

        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        return thumbnail

    # ✅ Updated: video() method with quality support
    async def video(self, link: str, videoid: Union[bool, str] = None, quality: str = "medium"):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]

        # ✅ Get quality format
        if quality not in self.QUALITY_OPTIONS:
            quality = "medium"
        format_str = self.QUALITY_OPTIONS[quality]["video"]

        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "-g",
            "-f",
            format_str,
            f"{link}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            return 0, stderr.decode()

    # ========== UPDATED PLAYLIST FUNCTION USING yt-dlp ==========
    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]

        ydl_opts = {
            "quiet": True,
            "extract_flat": True,
            "force_generic_extractor": False,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=False)
                if "entries" not in info:
                    return None
                videos = []
                for entry in info["entries"][:limit]:
                    if entry is None:
                        continue
                    vidid = entry.get("id")
                    if not vidid:
                        continue
                    title = entry.get("title", "Unknown")
                    duration = entry.get("duration")
                    if duration:
                        duration_min = f"{duration//60}:{duration%60:02d}"
                        duration_sec = duration
                    else:
                        duration_min = "0:00"
                        duration_sec = 0
                    thumbnail = f"https://img.youtube.com/vi/{vidid}/hqdefault.jpg"
                    videos.append({
                        "vidid": vidid,
                        "title": title,
                        "duration_min": duration_min,
                        "duration_sec": duration_sec,
                        "thumbnail": thumbnail,
                    })
                return videos
        except Exception as e:
            logger.error(f"Playlist fetch error: {e}")
            return None

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]

        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]
        ytdl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    str(format["format"])
                except:
                    continue
                if not "dash" in str(format["format"]).lower():
                    try:
                        format["format"]
                        format["filesize"]
                        format["format_id"]
                        format["ext"]
                        format["format_note"]
                    except:
                        continue
                    formats_available.append(
                        {
                            "format": format["format"],
                            "filesize": format["filesize"],
                            "format_id": format["format_id"],
                            "ext": format["ext"],
                            "format_note": format["format_note"],
                            "yturl": link,
                        }
                    )
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]

        try:
            results = []
            search = VideosSearch(link, limit=10)
            search_results = (await search.next()).get("result", [])

            for result in search_results:
                duration_str = result.get("duration", "0:00")
                try:
                    parts = duration_str.split(":")
                    duration_secs = 0
                    if len(parts) == 3:
                        duration_secs = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    elif len(parts) == 2:
                        duration_secs = int(parts[0]) * 60 + int(parts[1])

                    if duration_secs <= 3600:
                        results.append(result)
                except (ValueError, IndexError):
                    continue

            if not results or query_type >= len(results):
                raise ValueError("No suitable videos found within duration limit")

            selected = results[query_type]
            return (
                selected["title"],
                selected["duration"],
                selected["thumbnails"][0]["url"].split("?")[0],
                selected["id"]
            )

        except Exception as e:
            LOGGER(__name__).error(f"Error in slider: {str(e)}")
            raise ValueError("Failed to fetch video details")

    # ✅ New: get_cache_key method
    def _get_cache_key(self, vid_id: str, quality: str, stream_type: str) -> str:
        return f"{vid_id}:{quality}:{stream_type}"

    # ✅ New: is_cache_valid method
    def _is_cache_valid(self, vid_id: str, quality: str, stream_type: str) -> bool:
        key = self._get_cache_key(vid_id, quality, stream_type)
        if key in self.stream_cache:
            data, timestamp = self.stream_cache[key]
            if time.time() - timestamp < self.CACHE_EXPIRY:
                return True
        return False

    # ✅ New: get_from_cache method
    def _get_from_cache(self, vid_id: str, quality: str, stream_type: str) -> Optional[str]:
        key = self._get_cache_key(vid_id, quality, stream_type)
        if key in self.stream_cache:
            data, timestamp = self.stream_cache[key]
            if time.time() - timestamp < self.CACHE_EXPIRY:
                self.dl_stats["cache_hits"] += 1
                return data
        self.dl_stats["cache_misses"] += 1
        return None

    # ✅ New: save_to_cache method
    def _save_to_cache(self, vid_id: str, quality: str, stream_type: str, url: str):
        key = self._get_cache_key(vid_id, quality, stream_type)
        self.stream_cache[key] = (url, time.time())

    # ✅ Updated: download() method with quality, cache, and backup support
    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
        quality: str = "medium",           # ✅ New: quality parameter
        prebuffer: bool = True,            # ✅ New: prebuffer flag
        retry_count: int = 3,              # ✅ New: retry count
    ):
        """
        Enhanced download method with quality support, caching, and backup URLs.
        
        Returns:
            tuple: (stream_url, success, backup_url, quality_used)
        """
        # Extract video ID
        if videoid:
            vid_id = link
        else:
            match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:[&?]|$)", link)
            vid_id = match.group(1) if match else None

        if not vid_id:
            return None, False, None, None

        # ✅ Check cache first
        stream_type = "video" if video else "audio"
        cached_url = self._get_from_cache(vid_id, quality, stream_type)
        if cached_url:
            logger.info(f"✅ Cache hit for {vid_id}")
            return cached_url, True, None, quality

        if songvideo or songaudio:
            return None, False, None, None

        # ✅ Try with retries
        for attempt in range(retry_count):
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {"x-api-key": f"{YT_API_KEY}"}
                    
                    # ✅ Add quality parameter to API request
                    api_url = f"{YTPROXY}/info/{vid_id}?quality={quality}&type={stream_type}&prebuffer={str(prebuffer).lower()}"
                    
                    async with session.get(api_url, headers=headers, timeout=30) as resp:
                        if resp.status != 200:
                            logger.warning(f"API attempt {attempt+1} failed: {resp.status}")
                            if attempt < retry_count - 1:
                                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                                continue
                            return None, False, None, None
                        
                        data = await resp.json()
                        if data.get("status") != "success":
                            logger.warning(f"API error: {data.get('message')}")
                            if attempt < retry_count - 1:
                                await asyncio.sleep(1 * (attempt + 1))
                                continue
                            return None, False, None, None
                        
                        # ✅ Get stream URL and backup URL
                        result_data = data.get("data", {})
                        stream_url = result_data.get("video_url" if video else "audio_url")
                        backup_url = result_data.get("backup_url")
                        quality_used = result_data.get("quality", quality)
                        
                        if not stream_url:
                            stream_url = result_data.get("video_url")
                        
                        if not stream_url:
                            logger.error(f"No stream URL for {vid_id}")
                            return None, False, None, None
                        
                        # ✅ Save to cache
                        self._save_to_cache(vid_id, quality_used, stream_type, stream_url)
                        
                        logger.info(f"✅ Stream fetched for {vid_id} (quality: {quality_used})")
                        return stream_url, True, backup_url, quality_used
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout attempt {attempt+1} for {vid_id}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
            except Exception as e:
                logger.error(f"Download error attempt {attempt+1}: {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
        
        return None, False, None, None

    # ✅ New: get_stream_with_buffer method
    async def get_stream_with_buffer(
        self,
        link: str,
        videoid: Union[bool, str] = None,
        quality: str = "medium",
        video: bool = False,
    ) -> Dict:
        """
        Get stream URL with buffer information.
        Returns dict with stream_url, backup_url, duration, title, etc.
        """
        if videoid:
            vid_id = link
        else:
            match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:[&?]|$)", link)
            vid_id = match.group(1) if match else None
        
        if not vid_id:
            return {"success": False, "error": "Invalid video ID"}
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"x-api-key": f"{YT_API_KEY}"}
                stream_type = "video" if video else "audio"
                api_url = f"{YTPROXY}/info/{vid_id}?quality={quality}&type={stream_type}&prebuffer=true"
                
                async with session.get(api_url, headers=headers, timeout=30) as resp:
                    if resp.status != 200:
                        return {"success": False, "error": f"API error: {resp.status}"}
                    
                    data = await resp.json()
                    if data.get("status") != "success":
                        return {"success": False, "error": data.get("message", "Unknown error")}
                    
                    result_data = data.get("data", {})
                    
                    return {
                        "success": True,
                        "stream_url": result_data.get("video_url" if video else "audio_url"),
                        "backup_url": result_data.get("backup_url"),
                        "title": result_data.get("title", "Unknown"),
                        "duration": result_data.get("duration_str", "0:00"),
                        "duration_sec": result_data.get("duration", 0),
                        "quality": result_data.get("quality", quality),
                        "prebuffer": result_data.get("prebuffer"),
                        "video_id": vid_id
                    }
        except Exception as e:
            logger.error(f"get_stream_with_buffer error: {e}")
            return {"success": False, "error": str(e)}

    # ✅ New: clear_cache method
    def clear_cache(self):
        """Clear the stream cache"""
        self.stream_cache.clear()
        self.dl_stats["cache_hits"] = 0
        self.dl_stats["cache_misses"] = 0
        logger.info("🔄 Stream cache cleared")

    # ✅ New: get_stats method
    def get_stats(self) -> Dict:
        """Get download statistics"""
        return self.dl_stats

    # ✅ New: set_quality method
    def set_quality(self, quality: str) -> bool:
        """Set default quality"""
        if quality in self.QUALITY_OPTIONS:
            self.default_quality = quality
            return True
        return False

    # ✅ New: get_available_qualities method
    def get_available_qualities(self) -> List[str]:
        """Get list of available quality options"""
        return list(self.QUALITY_OPTIONS.keys())

    # ✅ New: get_quality_format method
    def get_quality_format(self, quality: str, stream_type: str) -> Optional[str]:
        """Get format string for specific quality and stream type"""
        if quality not in self.QUALITY_OPTIONS:
            return None
        return self.QUALITY_OPTIONS[quality].get(stream_type)


# ✅ Add time module import at top (if not already)
import time

# Create YouTube instance
YouTube = YouTubeAPI()
