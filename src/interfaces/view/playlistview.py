import sys
sys.path.append(r'D:\Program\Musify')


from PySide6.QtWidgets import QStackedWidget, QApplication
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import Signal, QTimer

from qasync import QEventLoop, asyncSlot, asyncClose

from src.interfaces.view.baseview import ViewInterface
from src.interfaces.view.base.playlistbase import PlaylistViewBase
from src.utility.database_utility import DatabaseManager
from src.utility.duration_parse import seconds_to_duration
from src.utility.enums import ImageFolder
from src.api.data_fetcher import DataFetcherWorker, YTMusicMethod
from loguru import logger

import asyncio
from pathlib import Path
import json


class PlaylistView(ViewInterface):
    def __init__(self, data_fetcher, database_manager:DatabaseManager, parent=None):
        super().__init__(data_fetcher, PlaylistViewBase, database_manager, parent)
        self.view_interface.viewCard.addToButton.hide()
        
    def fetch_view_data(self, playlist_id):
        self.view_request_id = self.data_fetcher.add_request(YTMusicMethod.GET_PLAYLIST, playlist_id)
        
    
    def ready_data(self):
        title = self.get_title()
        body = self.get_description()
        view_id = self.get_id()
        cover_path = Path(ImageFolder.PLAYLIST.path) / f"{view_id}.png"
        
        playlist_data = {
            "title": title,
            "description": body,
            "cover_art": str(cover_path),
            "id": view_id
        }
        return playlist_data
        # self.view_interface.songCardLoaded += 1    
    
    # def get_tracks_data(self):
        # return self.view_interface.get_tracks()
if(__name__ == "__main__"):
    app = QApplication([])
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    app_end_event = asyncio.Event()
    
    app.aboutToQuit.connect(app_end_event.set)
    
    data_fetcher = DataFetcherWorker()
    database_manager = DatabaseManager(r"data/user/database.db")
    view = PlaylistView(data_fetcher, database_manager)
    
    with open ("data/app/playlist.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        view.load_from_data(data, "MPREb_GdL2zr1Ks0v")
    view.show()
    
    # QTimer.singleShot(1000, lambda: view.load_from_database("RDCLAK5uy_kiDNaS5nAXxdzsqFElFKKKs0GUEFJE26w"))
    
    
    with loop:
        loop.run_until_complete(app_end_event.wait())