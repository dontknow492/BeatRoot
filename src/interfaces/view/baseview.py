import sys

import asyncio

from PySide6.QtWidgets import QStackedWidget, QApplication
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import Signal

from qasync import QEventLoop, asyncSlot, asyncClose

from src.interfaces.view.base.viewbase import ViewBase, ViewBaseSkeleton
from src.utility.database_utility import DatabaseManager
from src.api.data_fetcher import DataFetcherWorker
from loguru import logger   


class ViewInterface(QStackedWidget):
    audioCardClicked = Signal(dict)
    artistCardClicked = Signal(str)
    albumCardClicked = Signal(str)
    playlistCardClicked = Signal(str)
    errorOccurred = Signal(str)
    play = Signal(bool)
    saveSignal = Signal(dict)
    likeSignal = Signal(dict)
    albumClicked = Signal(str)
    artistClicked = Signal(str)
    deleteSignal = Signal(str)
    downloadSong = Signal(str, str) #video_id, title
    openSongInBrowser = Signal(str) #video_id
    share = Signal(str) #video_id
    likedSong = Signal(dict)
    queueSong = Signal(dict)
    def __init__(self, data_fetcher: DataFetcherWorker, view_interface: ViewBase, database_manager:DatabaseManager, parent=None):
        super().__init__(parent = parent)
        self.setObjectName('ViewInterface')

        self.loading_screen = ViewBaseSkeleton()
        self.loading_screen.stop_animation()
        self.view_interface:ViewBase = view_interface(self)
        self.data_fetcher = data_fetcher
        self.database_manager = database_manager
        self.data_fetcher.data_fetched.connect(self.on_fetching_finished)
        self.view_request_id = None
        self.view_id = None
        
        self._signal_handler()
        self.addWidget(self.view_interface)
        self.addWidget(self.loading_screen)
        
    def fetch_data(self, fetch_id):
        if self.get_id() == fetch_id:
            logger.info(f"Data allready loaded: {fetch_id}")
            return
        self.set_id(fetch_id)
        logger.info(f"Loading data for: {fetch_id}")
        self.switch_to(self.loading_screen)
        self.fetch_view_data(fetch_id)
        
    def _signal_handler(self):
        self.view_interface.playlistCardClicked.connect(self.playlistCardClicked.emit)
        self.view_interface.audioCardClicked.connect(self.audioCardClicked.emit)
        self.view_interface.artistClicked.connect(self.artistClicked.emit)
        self.view_interface.albumClicked.connect(self.albumClicked.emit)
        # self.view_interface.audioPlayClicked.connect(self.audioPlayClicked.emit)
        self.view_interface.errorOccurred.connect(self.errorOccurred.emit)
        self.view_interface.play.connect(self.play.emit)
        self.view_interface.liked.connect(self.on_like)
        #
        self.view_interface.downloadSong.connect(self.downloadSong.emit)
        self.view_interface.share.connect(self.share.emit)
        self.view_interface.openSongInBrowser.connect(self.openSongInBrowser.emit)
        self.view_interface.likedSong.connect(self.likedSong.emit)
        self.view_interface.queueSong.connect(self.queueSong.emit)
        
    def fetch_view_data(self, data):
        raise NotImplementedError
        
    def on_fetching_finished(self, data, uid):
        if uid != self.view_request_id:
            return
        logger.info("data changed")
        self.load_from_data(data, self.view_id)
        
    def load_from_data(self, data, view_id):
        self.set_id(view_id)
        # self.view_interface.setViewData(data)
        if not self.view_interface.loadData(data):
            logger.error("Failed to load data")
            self.deleteSignal.emit(view_id)
            return
        self.view_interface.update_view_card()
        self.view_interface.create_media_cards()
        self.switch_to(self.view_interface)
        
    @asyncSlot()
    async def load_from_database(self, view_id):
        self.set_id(view_id)
        logger.info(f"Loading playlist from database: {view_id}")
        await self.database_manager.get_playlist_info(view_id, self.set_card_info)
        await self.database_manager.get_playlist_songs(view_id, self.song_fetched)
    
    async def set_card_info(self, info):
        logger.debug(info)
        self.view_interface.setCardTitle(info.get("title"))
        self.view_interface.setCardBody(info.get("description"))
        self.view_interface.setViewId(info.get("id"))
        self.view_interface.setCardImage(info.get("cover_art"))
    
    async def song_fetched(self, songs):
        for song in songs:
            logger.debug(song)
            asyncio.create_task( self.database_manager.get_song(song[1], self.add_track))
    
    async def add_track(self, track: dict):
        logger.debug(f"Adding track: {track.get('videoId')}")
        # if isinstance(duration, int):
        #     duration = seconds_to_duration(duration)
        #     track.update({'duration', duration})
        card = self.view_interface.createAudioCard(track)
        if card:
            self.view_interface.addWidget(card)
        
    
    def get_tracks(self)->list:
        return self.view_interface.get_tracks()
    
    def set_id(self, id_):
        self.view_id = id_
        
    def get_id(self):
        return self.view_id
    
    def get_title(self):
        return self.view_interface.getCardTitle()
    
    def get_description(self):
        return self.view_interface.getCardBody()
    
    def on_like(self):
        emit_data = self.ready_data()
        self.likeSignal.emit(emit_data)
        logger.debug(emit_data)
        
    def ready_data(self):
        raise NotImplementedError
    
        
        
    def switch_to(self, widget):
        """
        Switches the current widget to the specified one, starting or stopping animations as needed.

        Args:
            widget (QWidget): The widget to switch to.
        """
        if widget not in [self.view_interface, self.loading_screen]:
            raise ValueError(f"Invalid widget: {widget}")
        if widget == self.view_interface:
            self.loading_screen.stop_animation()
        elif widget == self.loading_screen:
            self.loading_screen.start_animation()
        self.setCurrentWidget(widget)
        
    # @asyncClose
    # async def closeEvent(self, event):
    #     await self.database_manager.close()
    #     return super().closeEvent(event)

