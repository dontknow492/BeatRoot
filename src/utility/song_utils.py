from typing import Optional, Dict, Any, Union, List
from mutagen import File
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.ogg import OggFileType

from pathlib import Path
from loguru import logger
from PIL import Image
from io import BytesIO
import xxhash
import yt_dlp
# import 

from typing import Optional, Dict, Any
from mutagen import File
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.ogg import OggFileType
from pathlib import Path
import logging

from src.utility.duration_parse import seconds_to_duration

logger = logging.getLogger(__name__)

def get_metadata(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Extracts metadata from an audio file.

    Args:
        file_path (str): Path to the audio file.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing metadata (title, artist, duration, etc.),
                                   or None if the file is not supported or an error occurs.
    """
    try:
        # Load the audio file
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return None

        # Load file using Mutagen's File handler (supports multiple formats)
        audio = File(file_path)
        if audio is None:
            logger.error(f"Unsupported file format: {file_path}")
            return None

        # Extract common metadata
        metadata: Dict[str, Any] = {
            "title": "Unknown",
            "artists": "Unknown",
            "album": "Unknown",  # Album (MP4 specific)
            "duration": seconds_to_duration(int(audio.info.length)),  # Duration in seconds
            "duration_sec": audio.info.length,
            "bitrate": audio.info.bitrate,  # Bitrate in kbps
            "sample_rate": audio.info.sample_rate,  # Sample rate in Hz
            "channels": audio.info.channels,  # Number of audio channels
            "cover": None  # Placeholder for cover art
        }
        if isinstance(audio, MP3):
            metadata["title"] = audio.tags.get("TIT2", "Unknown").text[0] if "TIT2" in audio else "Unknown"
            metadata["artist"] = audio.tags.get("TPE1", "Unknown").text[0] if "TPE1" in audio else "Unknown"
            metadata["album"] = audio.tags.get("TALB", "Unknown").text[0] if "TALB" in audio else "Unknown"

        elif isinstance(audio, MP4):  # M4A, ALAC
            metadata["title"] = audio.tags.get("\xa9nam", ["Unknown"])[0]
            metadata["artist"] = audio.tags.get("\xa9ART", ["Unknown"])
            metadata["album"] = audio.tags.get("\xa9alb", ["Unknown"])[0]

        elif isinstance(audio, FLAC):
            metadata["title"] = audio.get("title", ["Unknown"])[0]
            metadata["artist"] = audio.get("artist", ["Unknown"])[0]
            metadata["album"] = audio.get("album", ["Unknown"])[0]

        elif isinstance(audio, OggFileType):
            metadata["title"] = audio.get("TITLE", ["Unknown"])[0]
            metadata["artist"] = audio.get("ARTIST", ["Unknown"])[0]
            metadata["album"] = audio.get("ALBUM", ["Unknown"])[0]

        # Extract cover art based on file format
        if isinstance(audio, MP3):  # MP3 files
            if 'APIC:' in audio.tags:
                metadata["cover"] = audio.tags['APIC:'].data
        elif isinstance(audio, FLAC):  # FLAC files
            if audio.pictures:
                metadata["cover"] = audio.pictures[0].data
        elif isinstance(audio, MP4):  # M4A files (AAC, ALAC)
            if 'covr' in audio.tags:
                metadata["cover"] = audio.tags['covr'][0]
        elif isinstance(audio, OggFileType):  # OGG files
            if 'metadata_block_picture' in audio.tags:
                metadata["cover"] = audio.tags['metadata_block_picture'][0]

        return metadata

    except Exception as e:
        logger.exception(f"Error extracting metadata from {file_path}: {e}")
        return None


def get_songs_from_dir(dir_path: str, limit: int = -1) -> List[str]:
    """
    Returns a list of all songs in the given directory.

    Args:
        dir_path (str): Path to the directory.

    Returns:
        List[str]: A list of file paths for all songs in the directory.
    """
    # Supported formats for mutagen and QMediaPlayer
    supported_formats = [
        # Mutagen-supported formats
        "mp3", "flac", "m4a", "ogg", "opus", "wav", "aiff", "ape", "wv", "mp4", "asf",
        # QMediaPlayer-supported formats (common formats)
        "aac", "alac", "wma", "m4b", "m4r", "3gp", "3g2", "amr", "au", "mid", "midi"
    ]

    count = 0
    songs: List[str] = []
    try:
        # Iterate through all files in the directory
        for file in Path(dir_path).iterdir():
            if file.is_file() and file.suffix.lower()[1:] in supported_formats:
                songs.append(str(file.absolute()))  # Use absolute path
                if count == limit:
                    break
    except Exception as e:
        print(f"Error reading directory {dir_path}: {e}")

    return songs

def create_dir_cover_art(dir_path: str, output_file: str = "folder.jpg") -> bool:
    """
    Creates a cover art for the directory.
    - If there are 4 or more songs, creates a collage of the first 4 cover arts.
    - If there are fewer than 4 songs, uses the first song's cover art.

    Args:
        dir_path (str): Path to the directory.
        output_file (str): Name of the output cover art file.

    Returns:
        bool: True if cover art was created, False otherwise.
    """
    songs = get_songs_from_dir(dir_path, 4)
    if not songs:
        print("No songs found in the directory.")
        return False

    # Extract cover arts from the first 4 songs
    cover_arts = []
    for song in songs[:4]:  # Only consider the first 4 songs
        metadata = get_metadata(song)
        if metadata and metadata.get("cover"):
            cover_arts.append(metadata["cover"])

    if not cover_arts:
        print("No cover arts found in any song.")
        return False

    # If fewer than 4 songs, use the first song's cover art
    if len(cover_arts) < 4:
        try:
            # Save the first song's cover art directly
            output_path = Path(dir_path) / output_file
            with open(output_path, "wb") as f:
                f.write(cover_arts[0])
            print(f"Cover art saved to {output_path} (first song's cover)")
            return True
        except Exception as e:
            print(f"Error saving cover art: {e}")
            return False

    # If 4 or more songs, create a collage
    collage = Image.new("RGB", (400, 400), "black")  # 400x400 for 2x2 grid
    for i, cover_art in enumerate(cover_arts):
        try:
            img = Image.open(BytesIO(cover_art))
            img = img.resize((200, 200))  # Resize for 2x2 grid
            x = (i % 2) * 200  # 0 or 200
            y = (i // 2) * 200  # 0 or 200
            collage.paste(img, (x, y))
        except Exception as e:
            print(f"Error processing cover art for {songs[i]}: {e}")

    # Save the collage
    output_path = Path(dir_path) / output_file
    collage.save(output_path)
    print(f"Collage saved to {output_path}")
    return True

def generate_xxhash_uid(path: str) -> str:
    """
    Generates a unique identifier (UID) for a file or folder using xxhash.

    Args:
        path (str): Path to the file or folder.

    Returns:
        str: A unique identifier based on xxhash, filename, size, and modification time.
              Returns None if an error occurs.
    """
    path = Path(path)  # Convert the input string to a Path object

    try:
        if path.is_file():
            # Handle single file
            file_stat = path.stat()
            # Include filename, size, and modification time in the hash
            hash_data = f"{path.name}{file_stat.st_size}{file_stat.st_ctime}"
            xxhash_uid = xxhash.xxh64(hash_data.encode("utf-8")).hexdigest()
        elif path.is_dir():
            # Handle folder
            xxhash_uid = xxhash.xxh64()
            for file_path in sorted(path.rglob("*")):  # Recursively get all files
                if file_path.is_file():  # Ensure it's a file (not a directory)
                    file_stat = file_path.stat()
                    # Include filename, size, modification time, and file path in the hash
                    hash_data = f"{file_path.name}{file_stat.st_size}{file_stat.st_mtime}{file_path}"
                    xxhash_uid.update(hash_data.encode("utf-8"))
            xxhash_uid = xxhash_uid.hexdigest()
        else:
            print(f"Error: {path} is not a valid file or folder.")
            return None

        return xxhash_uid  # Return the xxhash-based UID
    except Exception as e:
        print(f"Error generating UID for {path}: {e}")
        return None

def get_stream_url(video_url):
    ydl_opts = {
        # "quiet": True,
        "format": "bestaudio",  # Get the best audio stream
        "extract_flat": True,   # Avoid downloading the video
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return info["url"]

# if(__name__ == "__main__"):
#     url = "https://music.youtube.com/watch?v=YALvuUpY_b0"
#     stream_url = get_stream_url(url)
#     print(stream_url)

if(__name__ == "__main__"):
    import time
    import uuid
    start =time.time()
    dir_path = r"D:\Media\Music\Song"
    dirs = [
        r"D:\Media\Music\Dance",
        r"D:\Media\Music\Party",
        r"D:\Media\Music\Sad Song",
        r"D:\Media\Music\Romantic",
        r"D:\Media\Music\Song"
    ]
    
    xxid = list()
    for directory in dirs:
        xxid.append(generate_xxhash_uid(directory))
        print(uuid.uuid3(uuid.NAMESPACE_URL, directory))
        
    print(dirs)
    print(xxid)