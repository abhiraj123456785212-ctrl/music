import os
import aiohttp
import aiofiles
from config import YOUTUBE_IMG_URL

async def get_thumb(videoid, user_id):
    """
    Download YouTube video thumbnail and return local cached file path.
    If download fails, return default YOUTUBE_IMG_URL.
    """
    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    cache_path = os.path.join(cache_dir, f"{videoid}_{user_id}.jpg")
    
    # Return cached file if exists
    if os.path.isfile(cache_path):
        return cache_path
    
    # YouTube thumbnail URL (high quality)
    thumb_url = f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(cache_path, mode="wb")
                    await f.write(await resp.read())
                    await f.close()
                    return cache_path
    except Exception:
        pass
    
    # Fallback to default image
    return YOUTUBE_IMG_URL
