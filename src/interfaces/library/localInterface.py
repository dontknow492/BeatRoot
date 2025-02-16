from qfluentwidgets import ImageLabel, BodyLabel, TitleLabel, TransparentToolButton, TransparentDropDownToolButton
from qfluentwidgets import FluentIcon, setCustomStyleSheet, CardWidget, ElevatedCardWidget, SimpleCardWidget
from qfluentwidgets import TransparentPushButton, PopUpAniStackedWidget

from qasync import QEventLoop, asyncSlot, asyncClose
import asyncio
from loguru import logger

import sys
sys.path.append('d:\\Program\\Musify')
from src.common.myScroll import FlowScrollWidget
from src.components.cards.groupCard import GroupCard
from src.interfaces.library.base import LibraryInterfaceBase
from src.utility.song_utils import get_songs_from_dir, get_metadata, create_dir_cover_art, generate_xxhash_uid
from src.utility.database_utility import DatabaseManager

from pathlib import Path

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy, QFileDialog, QStackedWidget
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPixmap
from PySide6.QtWidgets import QGraphicsDropShadowEffect



class LocalInterface(LibraryInterfaceBase):
    directoryClicked = Signal(str, str)
    def __init__(self, database_manager: DatabaseManager, parent = None):
        super().__init__(parent=parent)
        self.setObjectName("localInterface")
        
        self.database_manager = database_manager
        self.addToLibrary = TransparentPushButton(FluentIcon.ADD, 'Add to library')
        self.addToLibrary.clicked.connect(self.on_add_music_folder)
        self.addOption(self.addToLibrary, alignment= Qt.AlignmentFlag.AlignLeft)
        self.add_refresh()
        
        
        QTimer.singleShot(1000, self.fetch_data)
        
        
    def on_add_music_folder(self):
        self.filepicker = QFileDialog(self)
        self.filepicker.setWindowTitle("Select a folder")
        self.filepicker.setFileMode(QFileDialog.Directory)
        self.filepicker.fileSelected.connect(self.on_folder_selected)
        self.filepicker.exec()
        # print(FluentIcon.FOLDER_ADD.path())
        
    @asyncSlot()
    async def on_folder_selected(self, path):
        print(path)
        path = Path(path)
        dir_songs = get_songs_from_dir(path)
        if len(dir_songs) > 0:
            # if create_dir_cover_art(path):
            #     cover_path = path / "folder.jpg"
            folder_id = generate_xxhash_uid(path)
            asyncio.create_task(self.database_manager.insert_local_directory(folder_id, path.__str__()))
            card = self._create_directory(folder_id, path.__str__())
            self.addWidget(card)
            
        else:
            print("No songs found in the directory.")
        
    # @asyncSlot()
    def _create_directory(self, folder_id: str, path: str, cover_path: str = None):
        if self.findChild(GroupCard, f"{folder_id}_card"):
            return
        card = GroupCard(self)
        card.setObjectName(f"{folder_id}_card")
        title = path.split('/')[-1]
        title = title.split("\\")[-1]
        card.setTitle(title)
        card.setPath(path)
        card.setCardId(folder_id)
        card.clicked.connect(lambda: self.directoryClicked.emit(folder_id, path))
        self.addCard(card)                    
    
    @asyncSlot()
    async def fetch_data(self):
        asyncio.create_task(self.database_manager.get_local_directories(self.on_fetched))
        
    
    async def on_fetched(self, results):
        if results is None:
            return
        logger.debug(results)
        for folder in results:
            folder_id = folder.get('id')
            folder_path = folder.get('path')
            self._create_directory(folder_id, folder_path)
        
        
    
        

            
        
        
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
    
    window = LocalInterface(database_manager)
    window.directoryClicked.connect(lambda folder_id, path: print(f"Directory clicked: {folder_id}, {path}"))
    # window.tempMedia(5)
    window.show()
    window.resize(800, 600)
    with loop:
        loop.run_until_complete(app_close_event.wait())