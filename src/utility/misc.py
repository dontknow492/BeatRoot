
import re
from typing import Optional
import vlc

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


def get_presets():
    """Returns a dictionary of equalizer presets and their band values."""
    vlc_presets = {
        "Flat": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "Classical": [0.0, 0.0, -6.6, -6.6, -3.9, -1.8, 1.5, 3.8, 4.6, 4.6],
        "Club": [3.0, 3.0, 2.4, 1.5, 0.0, -1.5, -1.5, 0.0, 1.5, 3.0],
        "Dance": [5.4, 4.8, 3.0, 0.0, -4.2, -5.1, -3.0, 0.0, 4.8, 6.0],
        "Full Bass": [4.8, 4.8, 3.0, 0.0, -4.2, -5.1, -4.8, -3.3, -1.5, -1.5],
        "Full Bass & Treble": [4.8, 3.0, 0.0, -3.9, -3.9, 0.0, 5.4, 6.0, 6.0, 6.0],
        "Full Treble": [-6.0, -6.0, -3.9, 0.0, 4.5, 8.1, 10.2, 11.7, 12.3, 12.3],
        "Headphones": [4.5, 3.0, 0.0, -2.1, -1.2, 2.1, 4.2, 5.4, 5.4, 5.4],
        "Large Hall": [6.0, 6.0, 3.9, 3.0, 0.0, -3.0, -3.0, 0.0, 3.9, 6.0],
        "Live": [-3.0, 0.0, 2.1, 3.0, 3.9, 5.1, 5.1, 5.1, 2.1, -3.0],
        "Party": [4.8, 4.8, 3.9, 0.0, 0.0, 0.0, 0.0, 3.9, 4.8, 4.8],
        "Pop": [-1.8, 2.1, 4.2, 5.1, 5.1, 3.9, 1.8, 0.0, -1.8, -3.9],
        "Reggae": [0.0, 0.0, 0.0, -3.0, 0.0, 3.9, 3.9, 0.0, 0.0, 0.0],
        "Rock": [4.5, 2.7, 0.0, -3.0, -3.9, 0.0, 4.8, 7.2, 7.8, 7.8],
        "Ska": [-1.8, -3.0, -3.0, 0.0, 3.0, 3.9, 3.9, 3.0, 0.0, 0.0],
        "Soft": [2.4, 0.0, -2.7, -1.8, 0.0, 3.0, 6.0, 7.2, 7.8, 8.1],
        "Soft Rock": [2.4, 2.4, 1.8, 0.0, -1.2, -1.8, 0.0, 2.1, 3.0, 3.0],
        "Techno": [6.0, 3.9, 0.0, -3.9, -4.8, -3.0, 0.0, 4.8, 5.4, 5.4]
    }
    return vlc_presets



def is_online_song(song_id: str) -> bool:
    return len(song_id) == 11

if (__name__ == "__main__"):
    for band, value in get_presets().items():
        print(band, value)
    # print(is_online_song("YALvuUpY_b0"))