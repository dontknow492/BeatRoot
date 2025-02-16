import platform
import os
import sys
from typing import Optional

from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import Qt, QObject, QTimer
from PySide6.QtGui import QAction
import vlc


class MusicPlayer(QObject):
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.vlc_instance = vlc.Instance("--no-xlib --no-video")
        self.media: Optional[vlc.Media] = None
        self.is_paused: bool = True
        self.media_player = self.vlc_instance.media_player_new()
        self.media_player.set_fullscreen(False)  # Optional, just in case fullscreen mode is enabled
        self.media_player.set_xwindow(0)  # Disable video output on specific window (useful on some systems)
        # Optional: Uncomment if you want to use a timer for periodic updates
        # self.timer = QTimer(self)
        # self.timer.setSingleShot(True)
        # self.timer.setInterval(500)
        # self.timer.timeout.connect(self.update_playback_status)

    def set_media(self, file_path: str) -> None:
        """Load a media file from the given path."""
        self.media = self.vlc_instance.media_new(file_path)
        self.media.parse()
        print("loaded")
        self.media_player.set_media(self.media)
        # self.play()
        # self.pause()

    def play(self) -> None:
        """Play the loaded media only if not already playing."""
        state = self.media_player.get_state()

        if state in [vlc.State.Playing, vlc.State.Buffering]:
            print("Media is already playing.")
            return

        if self.media_player.play() == -1:
            print("Error: Unable to play media.")
            return

        self.is_paused = False
        print(f"Current Time: {self.media_player.get_time()} ms")


    def pause(self) -> None:
        """Pause the currently playing media."""
        if self.media_player.get_state() == vlc.State.Playing:
            self.media_player.pause()
            self.is_paused = True

    def stop(self) -> None:
        """Stop the media playback."""
        self.media_player.stop()
        self.is_paused = True

    def set_volume(self, volume: int) -> None:
        """Set the volume level (0-100)."""
        if 0 <= volume <= 100:
            self.media_player.audio_set_volume(volume)
        else:
            print("Error: Volume must be between 0 and 100.")

    def get_volume(self) -> int:
        """Get the current volume level."""
        return self.media_player.audio_get_volume()

    def get_state(self) -> vlc.State:
        """Get the current state of the media player."""
        return self.media_player.get_state()

    def get_position(self) -> float:
        """Get the current playback position (0.0 to 1.0)."""
        return self.media_player.get_position()

    def get_length(self) -> int:
        """Get the total length of the media in milliseconds."""
        return self.media_player.get_length()
    
    def get_duration(self) -> int:
        """Get the total duration of the media in milliseconds."""
        return self.media.get_duration()
    
    def toggle_play_pause(self) -> None:
        """Toggle between play and pause states."""
        if self.is_paused:
            self.play()
        else:
            self.pause()

    def get_time(self) -> int:
        """Get the current playback time in milliseconds."""
        return self.media_player.get_time()
    
    def set_time(self, time_ms: int) -> None:
        """Set the current playback time in milliseconds."""
        print(self.media_player.set_time(time_ms))

    def get_title(self) -> int:
        """Get the title of the currently playing media."""
        return self.media.get_meta(vlc.MediaMeta.Title)
    
    def get_artist(self) -> int:
        """Get the artist of the currently playing media."""
        return self.media.get_meta(vlc.MediaMeta.Artist)
    
    def set_position(self, value):
        """Set the playback position (0.0 to 1.0)."""
        self.media_player.set_position(value)
        
    def set_state(self, state: vlc.State):
        """Set the state of the media player."""
        self.media_player.set_state(state)
        
    def set_playback_speed(self, speed: float):
        """Set the playback speed (e.g., 1.0 for normal speed)."""
        print(speed)
        self.media_player.set_rate(speed)
    
    # Optional: Uncomment if you want to use a timer for periodic updates
    # def update_playback_status(self) -> None:
    #     """Update playback status (e.g., current time, position)."""
    #     if not self.is_paused:
    #         print(f"Current Time: {self.get_current_time()} ms")
    #         print(f"Current Position: {self.get_position()}")
    
if(__name__ == "__main__"):
    import time
    from loguru import logger
    player = MusicPlayer()
    song = "https://rr5---sn-ci5gup-qxaes.googlevideo.com/videoplayback?expire=1738149506&ei=IrqZZ8fTBamDjuMPlryL0Q8&ip=2401%3A4900%3A1c5f%3A30e3%3Aed5a%3A9156%3Aa1c9%3A6c15&id=o-AC_Lbn5V9mF7VTPOshe2stChBey4kkfOQGKC9PeCKdUa&itag=251&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&met=1738127906%2C&mh=io&mm=31%2C26&mn=sn-ci5gup-qxaes%2Csn-cvh7knzd&ms=au%2Conr&mv=m&mvi=5&pl=51&rms=au%2Cau&gcr=in&initcwndbps=1848750&bui=AY2Et-NZa-FHBWUFSb8kqBUukrMRvOc5bNwxkK8T2JW3OgPTaZH_9wCCTZZflLcpkJ_wPqhak8QvGXZ7&vprv=1&svpuc=1&mime=audio%2Fwebm&ns=jg3nYfWQ_j6gTD_cNFBcZnkQ&rqh=1&gir=yes&clen=4557294&dur=261.721&lmt=1714680806091857&mt=1738127570&fvip=3&keepalive=yes&lmw=1&fexp=51326932%2C51353498%2C51371294&c=TVHTML5&sefc=1&txp=2318224&n=ywH6rxmw_L0FSw&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Cgcr%2Cbui%2Cvprv%2Csvpuc%2Cmime%2Cns%2Crqh%2Cgir%2Cclen%2Cdur%2Clmt&lsparams=met%2Cmh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Crms%2Cinitcwndbps&lsig=AGluJ3MwRQIgTgHLv0OSV5z7aT9Ysjr9fiEMKwwAIsqe16hhHkrtO7oCIQDJpIMyjxV8ncTXdDPavzES5WAOngE3OPx6IGgehT9M_A%3D%3D&sig=AJfQdSswRQIhANTPdG1fnON0ohCF7p3xOWdn25Cd-RNVfWoMlhUlwaKxAiB3dOoY8sRUvXPcJOP4Zb_oVcRcA569cBT8StLcBAW5CQ%3D%3D"
    player.set_media(song)
    player.play()
    player.set_volume(50)
    print(player.get_volume())
    print(player.get_length())
    # player.pause()
    logger.catch(lambda: player.play())
    while player.get_state() != vlc.State.Ended:
        time.sleep(1)  # Check every second
        print(f"Current Time: {player.get_time()} ms")
        if player.get_time() > 12000:
            print("duration: ", player.get_length())
            player.pause()
            break
    # player.stop()