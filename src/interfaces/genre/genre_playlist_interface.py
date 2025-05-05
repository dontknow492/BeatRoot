import sys


from src.components.cards.portraitCard import PlaylistCard
from src.common.myScroll import FlowScrollWidget
from src.utility.enums import DataPath, ImageFolder
from src.utility.downloader.thumbnail_downloader import ThumbnailDownloader

from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Signal
import sys
from loguru import logger
import queue


class GenrePlaylistView(FlowScrollWidget):
    ui_loaded = Signal()
    playlistCardClicked = Signal(str)
    def __init__(self, title: str = "Unknown", parent = None):
        super().__init__(title, parent)
        self.loaded = 0
        self.cover_queue = queue.Queue()
        self.scrollArea.verticalScrollBar().valueChanged.connect(self.on_scroll)
        self.setObjectName('GenrePlaylistView')
        self.thumbnail_downloader = ThumbnailDownloader(self)
        self.thumbnail_downloader.download_finished.connect(self.set_card_cover)
        
    def set_card_cover(self, path, uid):
        object_name = f"{uid}_card"
        card = self.findChild(QFrame, object_name)
        if card:
            card.setCover(path)
            # card.loadingLabel.hide()
            card.coverLabel.show()    
        else:
            self.cover_queue.put((path, uid))
            logger.info(f"Card not found for: {object_name} so appending it to queue")
    
    def set_cover_from_queue(self):
        while not self.cover_queue.empty():
            path, uid = self.cover_queue.get()
            object_name = f"{uid}_card"
            card = self.findChild(QFrame, object_name)
            if card:
                logger.info(f"Setting cover for: {object_name} from queue")
                card.setCover(path)
                # card.loadingLabel.hide()
                card.coverLabel.show()
            else:
                logger.error(f"Card not found for: {object_name}")
        
    def setGenreData(self, data):
        self.data = data
        
    def loadData(self):
        for index, playlist in enumerate(self.data, start= 0):
            if index > 20:
                break
            self.loaded = index
            if index <= self.count() - 1:
                logger.info(F"{index}, {self.count()}")
                card = self.scrollContainer_layout.itemAt(index).widget()
                if self.updatePlaylistCard(card, playlist):
                    logger.info(f"update of card: {index}")
                    continue
                
            card = self.createPlaylistCard(playlist)
            if card:
                self.insertWidget(index, card)    
                
        self.ui_loaded.emit()
                
        # self.timer.start()    
        
    def loadMore(self):
        logger.info('loading more playlists')
        for x in range(self.loaded + 1, self.loaded + 10):
            if x >= len(self.data):
                return
            card = self.createPlaylistCard(self.data[x])
            self.loaded = x
            if card:
                self.addWidget(card)
        
        # self.timer.start()
            
            
    def createPlaylistCard(self, playlist):
        playlist_id = playlist.get("playlistId", None)
        if playlist_id is None:
            return
        card = PlaylistCard()
        if card.setCardInfo(playlist):
            thumbnails = playlist.get("thumbnails", None)
            if thumbnails:
                thumbnail = thumbnails[-1].get("url", None)
                if thumbnail:
                    self.thumbnail_downloader.download_thumbnail(thumbnail, f"{playlist_id}.png", ImageFolder.PLAYLIST.path, playlist_id)
            card.clicked.connect(lambda: self.playlistCardClicked.emit(card.getPlaylistId()))
            return card
        
    def updatePlaylistCard(self, card, playlist):
        if card.setCardInfo(playlist):
            playlist_id = playlist.get("playlistId", None)
            thumbnails = playlist.get("thumbnails", None)
            if thumbnails:
                thumbnail = thumbnails[-1].get("url", None)
                if thumbnail:
                    self.thumbnail_downloader.download_thumbnail(thumbnail, f"{playlist_id}.png", ImageFolder.PLAYLIST.path, playlist_id)
            return True
        else:
            return False
    
    def on_scroll(self):
        scrollbar = self.scrollArea.verticalScrollBar()
        if scrollbar.value() == scrollbar.maximum():
            self.loadMore()
            scrollbar.setValue(scrollbar.value() - 10)

    def count(self)-> int:
        """return no of card in the widget

        Returns:
            int: integer
        """
        return self.scrollContainer_layout.count()
    
    # def clear_data(self):
    #     self.
