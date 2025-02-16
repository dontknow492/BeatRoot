from qfluentwidgets import ImageLabel, BodyLabel, TitleLabel, TransparentToolButton, TransparentDropDownToolButton
from qfluentwidgets import FluentIcon, setCustomStyleSheet, PrimaryPushButton
from qfluentwidgets import SearchLineEdit, Pivot, ComboBox, Action


import sys
sys.path.append(r'D:\Program\Musify')
from src.common.myScroll import MyScrollWidgetBase, FlowScrollWidget, VerticalScrollWidget
from src.common.myFrame import VerticalFrame, HorizontalFrame
from src.common.myButton import PrimaryRotatingButton
from src.components.cards.infoCard import DisplayStats
from src.components.cards.statsCard import ArtistStatsCard, AudioStatsCard, AlbumStatsCard

from src.utility.database_utility import DatabaseManager
from src.utility.enums import ImageFolder
from src.utility.misc import is_online_song

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy, QStackedWidget
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect

import asyncio
from qasync import asyncSlot, QEventLoop, asyncClose
from loguru import logger

from enum import Enum

class StatsFilter(Enum):
    DAY = 1
    WEEK = 2
    MONTH = 3
    SIX_MONTHS = 4
    YEAR = 5
    ALL_TIME = 6

    @property
    def sql_interval(self):
        """Returns the corresponding SQLite datetime interval string."""
        intervals = {
            StatsFilter.DAY: "-1 day",
            StatsFilter.WEEK: "-7 days",
            StatsFilter.MONTH: "-1 month",
            StatsFilter.SIX_MONTHS: "-6 months",
            StatsFilter.YEAR: "-1 year",
            StatsFilter.ALL_TIME: None,  # No filter for all-time
        }
        return intervals[self]

    @property
    def description(self):
        """Returns a human-readable description of the filter."""
        descriptions = {
            StatsFilter.DAY: "Last 24 hours",
            StatsFilter.WEEK: "Last 7 days",
            StatsFilter.MONTH: "Last 30 days",
            StatsFilter.SIX_MONTHS: "Last 6 months",
            StatsFilter.YEAR: "Last 12 months",
            StatsFilter.ALL_TIME: "All time",
        }
        return descriptions[self]


class StatsInterface(VerticalScrollWidget):
    audioClicked = Signal(str) #audio id 
    localAudioClicked = Signal(str) #emit file path
    albumClicked = Signal(str) #album id
    artistClicked = Signal(str) #artislt id
    def __init__(self, database_manager: DatabaseManager, parent = None):
        super().__init__(parent=parent)
        self.setObjectName("statsInterface")
        self.setContentsMargins(0, 0, 0, 0)
        self.setMargins(0, 0, 0, 0)
        self.setFrameStyle(QFrame.NoFrame)
        self.database_manager = database_manager
        
        self.setupUi()
        self.fetch_data()
        
    def setupUi(self):
        self.statsToast = DisplayStats(self)
        
        self.navigationPivot = Pivot(self)
        self.navigationPivot.setCursor(Qt.PointingHandCursor)
        # Add tab items
        self.navigationPivot.addItem(routeKey="songWidget", text="Top Songs", onClick=lambda: self.switchTo(0))
        self.navigationPivot.addItem(routeKey="artistWidget", text="Top Artists", onClick=lambda: self.switchTo(1))
        self.navigationPivot.addItem(routeKey="albumWidget", text="Top Albums", onClick=lambda: self.switchTo(2))
        self.navigationPivot.setCurrentItem("songWidget")
        
        self.option_container = HorizontalFrame(self)
        self.option_container.setContentsMargins(0, 0, 0, 0)
        self.option_container.setLayoutMargins(0, 0, 0, 0)
        
        self.refresh_button = PrimaryRotatingButton(FluentIcon.SYNC, "Refresh", self.option_container)
        self.refresh_button.clicked.connect(self.refresh)
        
        self.filterBox = ComboBox(self.option_container)
        for option in StatsFilter:
            self.filterBox.addItem(option.description, userData=option)
        #signal
        self.filterBox.currentIndexChanged.connect(lambda: self._fetch_card_data(self.filterBox.currentData().sql_interval))
        
        self.stackedWidget = QStackedWidget(self)
        self.song_container = VerticalFrame(self.stackedWidget)
        self.song_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.artist_container = VerticalFrame(self.stackedWidget)
        self.artist_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.album_container = VerticalFrame(self.stackedWidget)
        self.album_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.option_container.addWidget(self.refresh_button)
        self.option_container.addWidget(self.filterBox)
        
        self.stackedWidget.addWidget(self.song_container)
        self.stackedWidget.addWidget(self.artist_container)
        self.stackedWidget.addWidget(self.album_container)
        
        self.addWidget(self.statsToast)
        self.addWidget(self.navigationPivot, alignment=Qt.AlignTop | Qt.AlignLeft)
        self.addWidget(self.option_container, alignment=Qt.AlignTop | Qt.AlignRight)
        self.addWidget(self.stackedWidget)
        # self.vBoxLayout.addWidget(self)
        
    def initCursor(self):
        self.filterBox.setCursor(Qt.PointingHandCursor)
        self.navigationPivot.setCursor(Qt.PointingHandCursor)
            
            
    def refresh(self):
        QTimer.singleShot(1000, self.fetch_data)
    
    @asyncSlot()
    async def fetch_data(self):
        self._fetch_stats()
        self._fetch_card_data()
        
    def _fetch_stats(self):
        asyncio.create_task(self.database_manager.get_total_play_duration(self.set_play_time))
        asyncio.create_task(self.database_manager.get_unique_total_played_songs(self.set_songs_count))
        asyncio.create_task(self.database_manager.get_total_artists_played(self.set_artists_count))
        asyncio.create_task(self.database_manager.get_total_full_album_history(self.set_albums_count))
        asyncio.create_task(self.database_manager.get_total_liked_songs(self.set_liked_count))
        asyncio.create_task(self.database_manager.get_total_playlist_played(self.set_playlists_count))
        
    def _fetch_card_data(self, sql_interval: StatsFilter = StatsFilter.WEEK.sql_interval):
        asyncio.create_task(self.database_manager.get_top_songs(sql_interval, callback=self.top_songs))
        asyncio.create_task(self.database_manager.get_top_artists(sql_interval, 10, self.top_artists))
        asyncio.create_task(self.database_manager.get_top_albums(sql_interval, 10, self.top_albums))
        
    async def top_songs(self, results):
        for result in results:
            logger.debug(f"Top Song Result: {result}")
            song_id = result['id']
            is_online = is_online_song(song_id)
            if is_online:
                data = await self.database_manager.fetch_song(song_id)
            else:
                data = await self.database_manager.get_local_song(song_id)
            if data is None:
                continue
            logger.debug(f"Song: {data}")
            self.add_song(data['videoId'], data['title'], is_online, result['play_count'], result['file_path'])
        
    async def top_artists(self, results):
        for result in results:
            logger.debug(f"Top Artists Result: {result}")
            data = await self.database_manager.get_artist_info(result['id'])
            if data is None:
                continue
            logger.debug(f"Artist: {data}")
            self.add_artist(data[0], data[1], result['play_count'])
            
    
    async def top_albums(self, results):
        for result in results:
            logger.debug(f"Top Album Result: {result}")
            data = await self.database_manager.get_album_info(result['id'])
            if data is None:
                continue
            logger.debug(f"Album: {data}")
            self.add_album(data[0], data[1], result['play_count'])
    
    def add_song(self, song_id: str, title: str, is_online: bool, play_count: str, file_path: str = None):
        card = self.song_container.findChild(AudioStatsCard, f"{song_id}_card")
        if card:
            card.setRuns(play_count)
            return
        path = f"{ImageFolder.SONG.path}\\{song_id}.png"
        card = AudioStatsCard(title, play_count, cover_path=path)
        card.set_id(song_id)
        card.setObjectName(f"{song_id}_card")
        if is_online:
            card.clicked.connect(lambda: self.audioClicked.emit(song_id))
        else:
            card.clicked.connect(lambda: self.localAudioClicked.emit(file_path))
        self.song_container.addWidget(card)
    
    def add_artist(self, artist_id, name, play_count):
        card = self.artist_container.findChild(ArtistStatsCard, f"{artist_id}_card")
        if card:
            card.setRuns(play_count)
            return
        path = f"{ImageFolder.ARTIST.path}\\{artist_id}.png"
        card = ArtistStatsCard(name, play_count, cover_path=path)
        card.set_id(artist_id)
        card.setObjectName(f"{artist_id}_card")
        card.adjustSize()
        card.clicked.connect(lambda: self.artistClicked.emit(artist_id))
        self.artist_container.addWidget(card)    
    
    def add_album(self, album_id, title, play_count):
        card = self.album_container.findChild(AlbumStatsCard, f"{album_id}_card")
        if card:
            card.setRuns(play_count)
            return
        path = f"{ImageFolder.ALBUM.path}\\{album_id}.png"
        card = AlbumStatsCard(title, play_count, cover_path=path)
        card.set_id(album_id)
        card.setObjectName(f"{album_id}_card")
        card.clicked.connect(lambda: self.albumClicked.emit(album_id))
        self.album_container.addWidget(card)
    
        
    async def set_play_time(self, time: str | int):
        logger.debug(f"Total Play Time: {time}")
        if time is None:
            time = 0
        elif isinstance(time, int):
            time = (time/1000)/60
            time = f"{time:.2f}"
        self.statsToast.set_play_duration(time)
        
    async def set_songs_count(self, count: str | int):
        logger.debug(f"Total Song Count: {count}")
        self.statsToast.set_songs_count(count)
        
    async def set_artists_count(self, count: str | int):
        logger.debug(f"Total Artists Count: {count}")
        self.statsToast.set_artists_count(count)
        
    async def set_albums_count(self, count: str | int):
        logger.debug(f"Total Albums Count: {count}")
        self.statsToast.set_albums_count(count)
        
    async def set_playlists_count(self, count: str | int):
        logger.debug(f"Total Playlists Count: {count}")
        self.statsToast.set_playlists_count(count)
        
    async def set_liked_count(self, count: str | int):
        logger.debug(f"Total Liked Count: {count}")
        self.statsToast.set_liked_songs_count(count)
        
    def switchTo(self, index):
        self.stackedWidget.setCurrentIndex(index)
    
    
    @asyncClose
    async def closeEvent(self, event):
        logger.info("Stats Interface closed")
        
if(__name__ == '__main__'):
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)
    
    database_manager = DatabaseManager("d:/Program/Musify/data/user/database.db")
    
    window = StatsInterface(database_manager)
    # window.tempMedia(5)
    window.show()
    window.resize(800, 600)
    with loop:
        loop.run_until_complete(app_close_event.wait())