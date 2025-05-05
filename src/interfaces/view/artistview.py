import sys



from PySide6.QtWidgets import QStackedWidget, QApplication
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import Signal, QTimer

from qasync import QEventLoop, asyncSlot, asyncClose

from src.interfaces.view.baseview import ViewInterface
from src.interfaces.view.base.artistbase import ArtistViewBase
from src.utility.database_utility import DatabaseManager
from src.api.data_fetcher import DataFetcherWorker, YTMusicMethod
from loguru import logger

import asyncio
import json


class ArtistView(ViewInterface):
    def __init__(self, data_fetcher, database_manager:DatabaseManager, parent=None):
        super().__init__(data_fetcher, ArtistViewBase, database_manager, parent)
        self.view_interface.viewCard.addToButton.hide()
        
    def fetch_view_data(self, artist_id):
        self.view_request_id = self.data_fetcher.add_request(YTMusicMethod.GET_ARTIST, artist_id)
        
    def ready_data(self):
        data = {
            "id": self.get_id(),
            "name": self.get_title()
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
    view = ArtistView(data_fetcher, database_manager)
    with open ("data/app/artist.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        view.load_from_data(data, "UC6ut5W-0MQfHwGcllDnGfN4")
    # QTimer.singleShot(1000, lambda: view.load_from_database("YALvuUpY_b0"))
    view.show()
    with loop:
        loop.run_until_complete(app_end_event.wait())