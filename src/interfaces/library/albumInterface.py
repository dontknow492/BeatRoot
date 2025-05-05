import asyncio
import sys

from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import QApplication
from loguru import logger
from qasync import QEventLoop, asyncSlot, asyncClose

from src.components.cards.portraitCard import PortraitAlbumCard
from src.interfaces.library.base import LibraryInterfaceBase
from src.utility.database_utility import DatabaseManager
from src.utility.enums import ImageFolder


class AlbumInterface(LibraryInterfaceBase):
    albumClicked = Signal(str)
    albumPlayClicked = Signal(str)
    def __init__(self, database_manager: DatabaseManager, parent = None):
        super().__init__(parent=parent)
        self.database_manager = database_manager
        self.setObjectName("albumInterface")
        self.hideOptions()
        
        QTimer.singleShot(1000, self.fetch_data)
        
    # def load_data()
    @asyncSlot()
    async def fetch_data(self):
        asyncio.create_task(self.database_manager.get_liked_albums(self.on_fetched))
        
    async def on_fetched(self, results: list[dict]):
        if results is None:
            return
        for album in results:
            logger.debug(album)
            album_id = album.get('id')
            album_name = album.get('name')
            self.add_album(album_id, album_name)
            
    def add_album(self, album_id: str, album_name: str):
        if self.findChild(PortraitAlbumCard, f"{album_id}_card"):
            logger.debug(f"Album {album_name} already exists")
            return
        album = PortraitAlbumCard(self)
        pos = album.addButton.pos()
        album.addButton.hide()
        album.playButton.move(pos)
        album.setObjectName(f"{album_id}_card")
        album.setTitle(album_name)
        album.setAlbumId(album_id)
        path = f"{ImageFolder.ALBUM.path}\\{album_id}.png"
        album.setCover(path)
        album.clicked.connect(lambda: self.albumClicked.emit(album_id))
        album.playButton.clicked.connect(lambda: self.albumPlayClicked.emit(album_id))
        self.addCard(album)
        
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
    
    window = AlbumInterface(database_manager)
    # window.tempMedia(5)
    window.show()
    window.resize(800, 600)
    with loop:
        loop.run_until_complete(app_close_event.wait())