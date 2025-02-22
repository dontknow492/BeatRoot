
import re
from typing import Optional

def get_thumbnail_url(videoId):
    if len(videoId)>11:
        return None
    return f"https://i.ytimg.com/vi/{videoId}/maxresdefault.jpg"

def get_audio_url(videoId):
    if len(videoId)>11:
        return None
    return f"https://music.youtube.com/watch?v={videoId}"

def is_valid_youtube_url(url: str) -> bool:
    """
    Robustly checks if a given string is a valid YouTube URL, handling query parameters and edge cases.

    This function expands upon the basic validation to account for common variations
    in YouTube URLs, including different protocols, domains, paths, and query parameters.
    It also handles edge cases like empty strings and URLs with only the domain.

    Args:
        url: The string to check.

    Returns:
        True if the URL is a valid YouTube URL, False otherwise.
    """
    youtube_regex = re.compile(
        r"^(https?://)?(music\.)?(youtube\.com|youtu\.be)/"
        r"(watch\?v=|embed/|v/|shorts/)?(?P<id>[a-zA-Z0-9_-]{11})"
        # r"^(https?://)?(music\.)?(youtube\.com|youtu\.be)/"
    )
    match = youtube_regex.match(url)
    return bool(match)

def is_online_song(song_id: str) -> bool:
    return len(song_id) == 11

if (__name__ == "__main__"):
    print(is_online_song("YALvuUpY_b0"))