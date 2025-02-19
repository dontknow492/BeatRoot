from qfluentwidgets import ImageLabel, BodyLabel, TitleLabel, TransparentToolButton, TransparentDropDownToolButton
from qfluentwidgets import FluentIcon, setCustomStyleSheet, setThemeColor, setTheme, Theme, ThemeColor
from qfluentwidgets import RoundMenu, Action

import sys
sys.path.append(r'D:\Program\Musify')
# print(sys.path)
from src.components.player.playerbase import PlayerScreen
from src.utility.iconManager import ThemedIcon
from src.utility.duration_parse import milliseconds_to_duration
from src.utility.enums import PlaceHolder, ImageFolder
from src.utility.song_utils import get_stream_url

from enum import Enum
from loguru import logger
from typing import Optional, Union

from src.components.player.musicplayer import MusicPlayer
from src.api.data_fetcher import YTMusicMethod, DataFetcherWorker
from src.utility.database_utility import DatabaseManager
from src.utility.misc import is_online_song

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QSize, Signal, QTimer, QObject
from PySide6.QtGui import QFont, QColor, QAction
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from pathlib import Path
import vlc
import time


from qasync import QEventLoop, asyncSlot, asyncClose
import asyncio
# from torchvision.datasets import ImageFolder

class PlayerState(Enum):
    PLAYING = 0
    PAUSED = 1
    LOADING = 2
    FINISHED = 3
    BUFFERING = 4
    READY = 5



class PlayerInterface(PlayerScreen):
    prevClicked = Signal()
    nextClicked = Signal()
    queuesClicked = Signal()
    # repeatClicked = Signal(bool)
    shuffleClicked = Signal(bool)
    titleClicked = Signal()
    artistClicked = Signal()
    downloadClicked = Signal(str, str) #videoId, title
    error = Signal(str)
    likedSignal = Signal(str)
    unlikeSignal = Signal(str)

    def __init__(self, data_fetcher: DataFetcherWorker, database_manager: DatabaseManager, parent: QObject = None):
        super().__init__(parent)
        self.player_state = PlayerState.PAUSED
        self.music_player = MusicPlayer(self)
        self.data_fetcher = data_fetcher
        self.database_manager = database_manager
        self.data_fetcher.data_fetched.connect(self._on_fetching_finished)
        self.volume = 50
        self.volumeSlider.setValue(self.volume)
        self.volumeValue.setText(str(self.volume))
        self.is_liked = False
        
        self.playback = False
        
        self.song_id = None
        self.song_request_id = None
        self.file_path = None
        self.set_loading(False)
        
        self.signal_handler()
        self.init_speed_menu()

        self.timer = QTimer()
        self.timer.setSingleShot(False)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.update_ui)
        
    def reset_player_state(self):
        self.audioSlider.setValue(0)
        self.current_time_label.setText("00:00")
        self.total_time_label.setText("00:00")
        self.file_path = None
        self.set_liked(False)
        self.set_artist("Unknown")
        self.set_title("Unknown")
        self.set_cover(PlaceHolder.SONG.path)
        self.set_loading(True)
        self.music_player.stop()
        
    def init_speed_menu(self) -> None:
        """Initialize the playback speed menu."""
        self.speed_menu = RoundMenu(parent=self)
        speeds = [
            ("0.25", 0.25), ("0.5", 0.5), ("0.75", 0.75),
            ("Normal", 1.0), ("1.25", 1.25), ("1.5", 1.5),
            ("1.75", 1.75), ("2.0", 2.0)
        ]
        for label, speed in speeds:
            print(speed)
            action = Action(label, triggered=lambda checked, s=speed: self.music_player.set_playback_speed(s))
            self.speed_menu.addAction(action)
        self.speedButton.setMenu(self.speed_menu)

    def signal_handler(self) -> None:
        """Connect UI signals to their respective slots."""
        self.playButton.clicked.connect(self.on_play_clicked)
        self.prevButton.clicked.connect(self.prevClicked.emit)
        self.nextButton.clicked.connect(self.nextClicked.emit)
        self.queuesButton.clicked.connect(self.queuesClicked.emit)
        self.likeButton.clicked.connect(self.on_like_clicked)
        # self.repeatButton.toggled.connect(self.repeatClicked.emit)
        self.volumeSlider.valueChanged.connect(self.on_volume_changed)
        self.volumeButton.clicked.connect(self.on_volume_button_clicked)
        self.audioSlider.valueChanged.connect(self.slider_value_changed)
        self.audioSlider.sliderMoved.connect(self.slider_value_changed)
        self.audioSlider.sliderPressed.connect(self.set_pause)
        # self.audioSlider.sliderReleased.connect(self.set_play)
        self.shuffleButton.toggled.connect(self.shuffleClicked.emit)
        self.titleLabel.clicked.connect(self.titleClicked.emit)
        self.authorLabel.clicked.connect(self.artistClicked.emit)
        self.downloadButton.clicked.connect(self.on_download_clicked)

    def set_song(self, song_data: dict) -> None:
        """Set the current song by ID."""
        
        song_id = song_data.get('videoId', None)
        
        if self.song_id == song_id:
            return
        
        if self.song_id is not None:
            self.save_history(self.song_id, self.file_path, self.music_player.get_time())
            logger.critical("Song changed...")
            
        if self.music_player.media_player.is_playing():
            self.playback = True
            
        self.reset_player_state()  
            
        self.song_id = song_id
        
        if self.song_id is None:
            logger.error("Song ID not found in song data")
            self.error.emit("Song ID not found in song data")
            return
        
        title = song_data.get('title', None)
        artist = song_data.get('artists', None) or song_data.get('artist', [{}])
        cover = f"{ImageFolder.SONG.path}\\{self.song_id}.png"
        
        is_local = not is_online_song(self.song_id)
        logger.critical(f"Song_id: {self.song_id}")
        logger.debug(f"Is Local: {is_local}")
        if is_local:
            self.downloadButton.hide()
            stream_url = song_data.get('path', None)
            self.file_path = stream_url
            if stream_url and Path(stream_url).exists():
                self._set_stream(stream_url)
            else:
                logger.error(f"File not found: {stream_url}")
                self.error.emit(f"File not found: {stream_url}")
        else:
            self.set_loading(True)
            song_url = f"https://music.youtube.com/watch?v={self.song_id}"
            logger.info(f"Fetching song for web: {song_url}")
            self.song_request_id = self.data_fetcher.add_request(YTMusicMethod.GET_STREAM_URL, song_url)
            
        self.set_title(title)
        self.set_artist(artist)
        self.set_cover(cover)
        self.check_liked(self.song_id)
    
    def _set_stream(self, stream_url: str) -> None:
        """Set the stream URL and start playback."""
        self.music_player.set_media(stream_url)
        
        # self.music_player.play()
        
        self.set_play()
        time.sleep(0.5)
        self.set_pause()
        
        total_duration = self.music_player.get_duration()
        if self.music_player.get_duration() == -1:
            "if unable to find the duration setting timer to check again after 2 sec"
            timer = QTimer()
            timer.setInterval(2000)
            timer.timeout.connect(self._update_total_time)
            total_duration = 0
        self.set_total_duration(total_duration)
        #setting loading false
        self.set_loading(False)
        if self.playback:
            self.set_play()
            self.playback = False
        else:
            self.set_pause()
            
    def _on_fetching_finished(self, data, uid):
        if self.song_request_id != uid:
            return
        self._set_stream(data)
        
    def update_ui(self) -> None:
        """Update the UI elements."""
        if self.music_player.get_state() == vlc.State.Ended:
            self._update_play_button(FluentIcon.PLAY_SOLID, "Play", PlayerState.PAUSED)
            logger.info("Playback finished")
            
            if self.repeatButton.isChecked():
                self.music_player.stop()  # Ensure VLC resets properly
                self.save_history(self.song_id, self.file_path, self.music_player.get_time())
                self.music_player.set_time(0)  # Reset time to beginning
                self.set_play()  # Explicitly restart playback
                
            else:
                self.nextClicked.emit()
                self.playback = True
                self.timer.stop()
        elif self.music_player.get_state() == vlc.State.Paused:
            self.set_pause()
            
        elif self.music_player.get_state() == vlc.State.Playing:
            cur_dur = self.music_player.get_time()
            self.set_current_duration(cur_dur)

    def on_play_clicked(self) -> None:
        """Handle play/pause button click."""
        match self.player_state:
            case PlayerState.PLAYING:
                self.set_pause()
            case PlayerState.PAUSED:
                self.set_play()
                
    def set_pause(self):
        self._update_play_button(FluentIcon.PLAY_SOLID, "Play", PlayerState.PAUSED)
        logger.info("Pausing playback")
        self.music_player.pause()
        self.timer.stop()
        
    def set_play(self):
        self._update_play_button(FluentIcon.PAUSE_BOLD, "Pause", PlayerState.PLAYING)
        logger.info("Resuming playback")
        self.music_player.play()
        self.timer.start()
                
    def _update_play_button(self, icon, tooltip, state):
        """Helper method to update play button attributes."""
        self.playButton.setIcon(icon)
        self.playButton.setToolTip(tooltip)
        self.player_state = state

    def on_volume_changed(self, value: int) -> None:
        """Handle volume slider value change."""
        self.update_volume(value)

    def on_volume_button_clicked(self) -> None:
        """Handle volume button click (mute/unmute)."""
        current_volume = self.volumeSlider.value()

        if current_volume == 0:  # Unmute
            new_volume = self.volume
        else:  # Mute
            self.volume = current_volume  # Save the current volume
            new_volume = 0
        self.update_volume(new_volume)  # Mute by setting the slider to 0

    def update_volume(self, value: int) -> None:
        """Update the volume level and related UI elements."""
        self.volumeButton.setIcon(FluentIcon.MUTE if value == 0 else FluentIcon.VOLUME)
        self.volumeSlider.setValue(value)
        self.volumeValue.setText(str(value))
        self.music_player.set_volume(value)

    def on_like_clicked(self) -> None:
        """Handle like button click."""
        self.set_liked(not self.is_liked)
        if not self.is_liked:
            self.unlikeSignal.emit(self.song_id)
        else:
            self.likedSignal.emit(self.song_id)
    
    @asyncSlot()    
    async def check_liked(self, song_id):
        if await self.database_manager.check_liked_song(song_id):
            self.set_liked(True)

    def _update_total_time(self) -> None:
        """Update the total duration after a short delay."""
        total_duration = self.music_player.get_duration()
        self.set_total_duration(total_duration)
    
    def set_cover(self, cover_path: str) -> None:
        """Set the cover image."""
        if Path(cover_path).exists():
            size = self.coverLabel.size()
            self.coverLabel.setImage(cover_path)
            self.coverLabel.setFixedSize(size)
        else:
            logger.error(f"Cover image not found: {cover_path}")
            
    
    def set_title(self, title: str) -> None:
        """Set the title label text."""
        self.titleLabel.setText(title)
        
    def set_artist(self, artist: str|list) -> None:
        """Set the artist label text."""
        if isinstance(artist, list):
            artist = ", ".join(artist.get('name', "Unknown") for artist in artist)
            print(artist)
        self.authorLabel.setText(artist)
        
    def set_liked(self, state: bool):
        """Set the like button state."""
        if state:
            self.likeButton.setIcon(ThemedIcon.HEART_SOLID)
            self.likeButton.setToolTip("Unlike")
            self.is_liked = True
        else:
            self.likeButton.setIcon(FluentIcon.HEART)
            self.likeButton.setToolTip("Like")
            self.is_liked = False
            
    def seek_song(self, value: int) -> None:
        """Seek to a specific position in the song."""
        self.music_player.set_time(value)
        format_duration = milliseconds_to_duration(value)
        self.current_time_label.setText(format_duration)
        
        if value == self.audioSlider.maximum():
            if self.repeatButton.isChecked():
                self.music_player.set_time(0)
                self.set_play()
                return
            self.set_pause()
            self.nextClicked.emit()
    
    def slider_value_changed(self, value: int) -> None:
        """Handle audio slider value change."""
        self.seek_song(value)
    
    def set_current_duration(self, value: int) -> None:
        """Set the audio slider value."""
        self.audioSlider.valueChanged.disconnect(self.slider_value_changed)
        self.audioSlider.setValue(value)
        self.audioSlider.valueChanged.connect(self.slider_value_changed)
        
        # self.audioSlider.blockSignals(False)
        formated_duration = milliseconds_to_duration(value)
        self.current_time_label.setText(formated_duration)

    def set_total_duration(self, value: int) -> None:
        """Set the audio slider range."""
        logger.info(f"Setting total duration: {value}")
        self.audioSlider.setRange(0, value)
        formated_duration = milliseconds_to_duration(value)
        self.total_time_label.setText(formated_duration)
    
    def set_shuffle(self, shuffle: bool):
        self.shuffleButton.setChecked(shuffle)
    
    def get_song_id(self) -> str:
        return self.song_id
    
    def stop(self):
        self.music_player.stop()
        self.set_pause()
        self.set_current_duration(0)
    # def get    
    
    @asyncSlot()    
    async def save_history(self,song_id, file_path, duration: int ):
        """Save the song history to the database."""
        if duration <=0:
            return
        await self.database_manager.insert_play_history(song_id, duration, file_path)
        
    def on_download_clicked(self):
        if self.song_id is None:
            return
        self.downloadClicked.emit(self.song_id, self.titleLabel.text())
        
if(__name__ == "__main__"):
    setTheme(Theme.DARK)
    database_manager = DatabaseManager("data/user/database.db")
    app = QApplication(sys.argv)
    song = r"D:\Media\Music\Song\Abhijeet - Woh Ladki Jo.m4a"
    song_data = {
        "videoId": "YALvuUpY_b0",
        "title": "Woh Ladki Jo",
        "artists": [{"name": "Abhijeet"}],
        "path": song
    }
    data_fetcher = DataFetcherWorker()
    data_fetcher.start()
    
    window = PlayerInterface(data_fetcher, database_manager)
    window.set_song(song_data)
    
    # song_data = {
    #     "videoId": "5zTSjLw18LU",
    #     "title": "Pal to dede",
    #     "artists": [{"name": "Some Bihari"}],
    #     "path": song
    # }
    # QTimer.singleShot(2000, lambda: window.set_song(song_data))
    
    # player.load_media(song)
    # duration = player.get_length()
    # window.setPlayerAttribute(title="Woh Ladki Jo.m4a",
    #                         author="Author",
    #                         isLiked=True,
    #                         volume=46,
    #                         current_duration="00:00",
    #                         total_duration="03:00")
    window.show()
    window.move(200, 300)
    window.resize(1200, 90)
    
    
    
    
    
    # window.repeatClicked.connect(lambda x: print(x))
    # window.likeClicked.connect(lambda x: print(x))
    # window.volumeChanged.connect(lambda x: print(x))
    # window.playbackSpeedChanged.connect(lambda x: print(x))
    # window.audioPositionChanged.connect(lambda x: print(x))
    # window.nextClicked.connect(lambda x: print(x))
    # window.prevClicked.connect(lambda x: print(x))
    # window.queuesClicked.connect(lambda x: print(x))
    # window.shuffleClicked.connect(lambda x: print(x))
    # window.titleClicked.connect(lambda : print(window.titleLabel.text()))
    # window.artistClicked.connect(lambda : print(window.authorLabel.text()))
    app.exec()