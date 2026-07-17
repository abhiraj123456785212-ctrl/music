import os

from ..logging import LOGGER


def dirr():
    # Clean old image files
    for file in os.listdir():
        if file.endswith(".jpg"):
            os.remove(file)
        elif file.endswith(".jpeg"):
            os.remove(file)
        elif file.endswith(".png"):
            os.remove(file)

    # Create required directories
    if "downloads" not in os.listdir():
        os.mkdir("downloads")
    
    if "cache" not in os.listdir():
        os.mkdir("cache")
    
    # ========== VERSION 1.1 - NEW: Create cookies folder ==========
    if "cookies" not in os.listdir():
        os.mkdir("cookies")
    
    # ========== VERSION 1.1 - NEW: Create playback folder for speed control ==========
    if "playback" not in os.listdir():
        os.mkdir("playback")
        # Create subfolders for different speeds
        for speed in ["0.5", "0.75", "1.0", "1.5", "2.0"]:
            speed_path = os.path.join("playback", speed)
            if not os.path.exists(speed_path):
                os.makedirs(speed_path)

    LOGGER(__name__).info("Directories Updated Successfully!")
