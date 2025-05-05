from qfluentwidgets import ImageLabel, BodyLabel, TitleLabel, TransparentToolButton, TransparentDropDownToolButton
from qfluentwidgets import FluentIcon, setCustomStyleSheet, CardWidget, ElevatedCardWidget, SimpleCardWidget
from qfluentwidgets import TransparentPushButton, PrimaryPushButton


import sys

# sys.path.append('src')
from src.common.myScroll import FlowScrollWidget
from src.components.cards.portraitCard import PlaylistCard
from src.components.dialogs.add_playlist import AddPlaylistDialog
from src.interfaces.library.base import LibraryInterfaceBase
from src.utility.database_utility import DatabaseManager

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QSize, Signal, QTimer, Slot
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect

from qasync import QEventLoop, asyncSlot, asyncClose
import asyncio
from loguru import logger

import uuid


class PlaylistInterface(LibraryInterfaceBase):
    playlistClicked = Signal(str)
    playlistPlayClicked = Signal(str)
    def __init__(self, database_manager:DatabaseManager, parent = None):
        super().__init__(parent=parent)
        self.setObjectName("playlistInterface")
        
        self.database_manager = database_manager
        
        create_playlist_button = PrimaryPushButton(FluentIcon.ADD, 'Create playlist')
        create_playlist_button.clicked.connect(self.show_create_dialog)
        self.addOption(create_playlist_button, alignment= Qt.AlignmentFlag.AlignLeading)
        
        self.liked_id = uuid.uuid4().hex    
        self.likedTitle = "Liked Songs"
        self.likedInfo = "All your liked songs"
        self.add_playlist(self.liked_id, self.likedTitle, self.likedInfo, None)
        
        self.add_refresh()
        
        QTimer.singleShot(1000, self.fetch_data)
        
        
        
    def show_create_dialog(self):
        dialog = AddPlaylistDialog(self)
        if dialog.exec():
            playlist_id = uuid.uuid4().hex
            title = dialog.playlistName.text()
            description = dialog.description.toPlainText()
            cover_path = dialog.cover_path
            self.add_playlist(playlist_id, title, description, cover_path)
            asyncio.create_task(self.database_manager.insert_playlist({
                        "id": playlist_id,
                        "title": title,
                        "description": description,
                        "cover_art": cover_path}
                        )
                    )
    
    
        
    @asyncSlot()
    async def fetch_data(self):
        await self.database_manager.get_playlists(self.on_fetched)
        
    async def on_fetched(self, results: list[dict]):
        if results is None:
            logger.info("No Playlist found")
            return
        for result in results:
            logger.debug(result)
            playlist_id = result.get('id')
            title = result.get('title')
            description = result.get('description')
            cover_path = result.get('cover_art')
            self.add_playlist(playlist_id, title, description, cover_path)
        
            
    def add_playlist(self, playlist_id:str, title: str, info: str, cover_path: str):
        if self.findChild(PlaylistCard, f"{playlist_id}_card"):
            logger.debug(f"Playlist: {title} already exists")
            return
        logger.info(f"Adding playlist: {title}")
        playlist = PlaylistCard(self)
        playlist.setObjectName(f"{playlist_id}_card")
        pos = playlist.addButton.pos()
        playlist.addButton.setEnabled(False)
        playlist.addButton.setHidden(True)
        playlist.setTitle(title)
        playlist.setInfo(info)
        if cover_path is not None:
            playlist.setCover(cover_path)
        playlist.playButton.move(pos)
        playlist.clicked.connect(lambda: self.playlistClicked.emit(playlist_id))
        playlist.playButton.clicked.connect(lambda: self.playlistPlayClicked.emit(playlist_id))
        self.addCard(playlist)
            
    
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
    
    window = PlaylistInterface(database_manager)
    # window.tempMedia(5)
    window.show()
    window.resize(800, 600)
    with loop:
        loop.run_until_complete(app_close_event.wait())