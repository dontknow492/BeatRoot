from qfluentwidgets import FlowLayout, TitleLabel, PrimaryPushButton

import sys
sys.path.append(r'D:\Program\Musify')
from pathlib import Path

import json

from src.components.cards.portraitCard import PlaylistCard
from src.common.myScroll import FlowScrollWidget, VerticalScrollWidget
from src.components.cards.genreCard import SimpleGenreCard
from src.common.myFrame import FlowFrame
from src.animation.playlist_skeleton_animation import PlaylistSkeleton
from src.api.data_fetcher import DataFetcherWorker, YTMusicMethod
from src.utility.check_net_connectivity import is_connected_to_internet
from src.utility.enums import DataPath, ImageFolder
from src.utility.downloader.thumbnail_downloader import ThumbnailDownloader

from PySide6.QtWidgets import QWidget, QApplication, QStackedWidget, QFrame
from PySide6.QtCore import QTimer, Qt, Signal
import sys
from loguru import logger
import queue


class AllGenreInterface(VerticalScrollWidget):
    noInternet = Signal()
    genreSelected = Signal(str)
    def __init__(self, data_fetcher: DataFetcherWorker, parent = None):
        super().__init__(None, parent)
        self.loaded = 0
        self.data_fetcher = data_fetcher
        # self.scrollArea.verticalScrollBar().valueChanged.connect(self.on_scroll)
    
    def _fetch_genres(self):
        
        self.genre_path =  DataPath.GENRE_CATEGORY.getAbsPath
        logger.info(f"path of genre file: {self.genre_path}")
        if Path(self.genre_path).exists():
            logger.info(f"loading genre form local file: {self.genre_path}")
            with open(self.genre_path, 'r') as file:
                data = json.load(file)
                self._fetched_genres(data)
                
        elif not is_connected_to_internet():
            self.noInternet.emit()
        else:
            logger.info("loading form api")
            self.data_fetcher.data_fetched.connect(self._fetched_genres)
            self.data_fetcher.get_mood_categories()
            
    def _fetched_genres(self, data):
        self.setGenresData(data)
        self.loadData()
        if not Path(self.genre_path).exists():
            with open(self.genre_path, 'w') as file:
                json.dump(data, file)
        
    def setGenresData(self, data):
        self.data = data

    def loadData(self):
        for key in self.data.keys():
            title_label = TitleLabel(key, self)
            container = FlowFrame()
            for genre in self.data.get(key, []):
                card = self.createGenreCard(genre)
                if card:
                    container.addWidget(card)
            self.addWidget(title_label)
            self.addWidget(container)
        # self.timer.start()

    def loadMore(self):
        logger.info('loading more')
        self.timer.stop()
        for x in range(self.loaded, self.loaded + 10):
            logger.info(x)
            if x >= len(self.data):
                return
            card = self.createGenreCard(self.data[x])
            self.loaded = x
            if card:
                self.addWidget(card)

        # self.timer.start()

    def createGenreCard(self, genre):
        genre_id = genre.get("params", None)
        if genre_id is None:
            return
        title = genre.get("title", None)
        thumbnail = genre.get("thumbnails", [{}])[-1].get("url", None)
        card = SimpleGenreCard(None, title)
        card.setGenreId(genre_id)
        card.clicked.connect(lambda: self.genreSelected.emit(genre_id))
        # card.setCover(thumbnail)
        return card

    def on_scroll(self):
        scrollbar = self.scrollArea.verticalScrollBar()
        if scrollbar.value() == scrollbar.maximum():
            self.loadMore()
            scrollbar.setValue(scrollbar.value() - 10)

