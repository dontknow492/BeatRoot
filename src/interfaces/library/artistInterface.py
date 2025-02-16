from qfluentwidgets import ImageLabel, BodyLabel, TitleLabel, TransparentToolButton, TransparentDropDownToolButton
from qfluentwidgets import FluentIcon, setCustomStyleSheet, CardWidget, ElevatedCardWidget, SimpleCardWidget
from qfluentwidgets import SearchLineEdit, PrimaryPushButton


import sys
sys.path.append('d:\\Program\\Musify')
from src.common import FlowScrollWidget
from src.components.cards.portraitCard import PlaylistCard
from src.components.cards.artistCard import ArtistCard
from src.interfaces.library.base import LibraryInterfaceBase
from src.utility.database_utility import DatabaseManager
from src.utility.enums import ImageFolder
from src.utility.misc import get_thumbnail_url

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect

import asyncio
from qasync import asyncSlot, asyncClose, QEventLoop
from loguru import logger
from pathlib import Path


class ArtistInterface(LibraryInterfaceBase):
    artistClicked = Signal(str) 
    def __init__(self, database_manager: DatabaseManager, parent = None):
        super().__init__(parent=parent)
        self.setObjectName("artistInterface")
        # self.setupUi()
        self.database_manager = database_manager
        # self.hideOptions()
        
        QTimer.singleShot(1000, self.fetch_data)
        
        
    @asyncSlot()
    async def fetch_data(self):
        asyncio.create_task(self.database_manager.get_liked_artists(self.on_fetched))
        
    
    async def on_fetched(self, results: list):
        if results is None:
            return
        logger.debug(results)
        for artist in results:
            artist_id = artist.get('id')
            artist_name = artist.get('name')
            self.add_artist(artist_id, artist_name)
            
    def add_artist(self, artist_id: str, artist_name: str):
        if self.findChild(ArtistCard, f"{artist_id}_card"):
            logger.debug(f"Artist {artist_name} already exists")
            return
        artist_card = ArtistCard()
        artist_card.setObjectName(f"{artist_id}_card")
        artist_card.setArtistName(artist_name)
        artist_card.setArtistId(artist_id)
        path = f"{ImageFolder.ARTIST.path}\\{artist_id}.png"
        artist_card.setCover(path)
        artist_card.clicked.connect(lambda: self.artistClicked.emit(artist_id))
        self.addCard(artist_card)
            
    @asyncClose
    async def closeEvent(self, event):
        logger.info("PlaylistInterface closed")
        super().closeEvent(event)
        
if(__name__ == '__main__'):
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)
    
    database_manager = DatabaseManager("d:/Program/Musify/data/user/database.db")
    
    window = ArtistInterface(database_manager)
    # window.tempMedia(5)
    window.show()
    window.resize(800, 600)
    with loop:
        loop.run_until_complete(app_close_event.wait())
            