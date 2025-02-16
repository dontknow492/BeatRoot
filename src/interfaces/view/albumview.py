import sys
sys.path.append(r'D:\Program\Musify')


from PySide6.QtWidgets import QStackedWidget, QApplication
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import Signal, QTimer

from qasync import QEventLoop, asyncSlot, asyncClose

from src.interfaces.view.baseview import ViewInterface
from src.interfaces.view.base.albumbase import AlbumViewBase
from src.utility.database_utility import DatabaseManager
from src.utility.enums import ImageFolder
from src.api.data_fetcher import DataFetcherWorker, YTMusicMethod
from loguru import logger

import asyncio
import json
from pathlib import Path

class AlbumView(ViewInterface):
    def __init__(self, data_fetcher, database_manager:DatabaseManager, parent=None):
        super().__init__(data_fetcher, AlbumViewBase, database_manager, parent)
        self.view_interface.viewCard.addToButton.hide()
        self.view_interface.viewCard.bodyLabel.hide()
                
    def fetch_view_data(self, album_id):
        self.view_request_id = self.data_fetcher.add_request(YTMusicMethod.GET_ALBUM, album_id)
        
            # asyncio.create_task()
        # asyncio.create_task(self.save_view())
        
    def ready_data(self):
        title = self.get_title()
        view_id = self.get_id()
        track_count = self.get_data().get("trackCount", 0)
        
        data = {
            'title': title,
            'id': view_id,
            'trackCount': track_count
        }    
        return data
    
    
if(__name__ == "__main__"):
    app = QApplication([])
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    app_end_event = asyncio.Event()
    
    app.aboutToQuit.connect(app_end_event.set)
    
    data_fetcher = DataFetcherWorker()
    database_manager = DatabaseManager(r"data/user/database.db")
    view = AlbumView(data_fetcher, database_manager)
    
    with open ("data/app/album.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        view.load_from_data(data, "MPREb_GdL2zr1Ks0v")
    
    view.show()
    # QTimer.singleShot(1000, lambda: view.load_from_database("MPREb_Kmxm9sTicVF"))
    # view.load_from_database("MPREb_Kmxm9sTicVF")
    with loop:
        loop.run_until_complete(app_end_event.wait())