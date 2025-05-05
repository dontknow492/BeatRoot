import sys



from PySide6.QtWidgets import QStackedWidget, QApplication
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import Signal

from qasync import QEventLoop, asyncSlot, asyncClose

from src.interfaces.view.baseview import ViewInterface
from src.interfaces.view.base.audiobase import AudioViewBase
from src.utility.database_utility import DatabaseManager
from src.utility.enums import ImageFolder
from src.api.data_fetcher import DataFetcherWorker, YTMusicMethod
from loguru import logger

import asyncio
from pathlib import Path

class AudioView(ViewInterface):
    addToPlaylistSignal = Signal(dict)
    def __init__(self, data_fetcher, database_manager:DatabaseManager, parent=None):
        super().__init__(data_fetcher, AudioViewBase, database_manager, parent)
        self.view_interface.addedTo.connect(self.on_add_to)
        self.selected = 0

    def fetch_view_data(self, audio_id):
        self.view_request_id = self.data_fetcher.add_request(YTMusicMethod.GET_WATCH_PLAYLIST, audio_id)
    
    def on_add_to(self):
        emit_data = self.ready_data()
        self.addToPlaylistSignal.emit(emit_data)
        logger.debug(emit_data)
    
    def ready_data(self):
        return self.get_tracks()[self.selected]
        # watch_playlist_data = self.ready_watch_playlist_data()
        # if not self.get_id():
        #     logger.error("Audio ID is not available")
        # await self.database_manager.insert_playlist(watch_playlist_data)
        # asyncio.create_task(self.database_manager.insert_liked_playlist(self.get_id()))
    
    
    
    
if(__name__ == "__main__"):
    import json
    app = QApplication([])
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    app_end_event = asyncio.Event()
    
    app.aboutToQuit.connect(app_end_event.set)
    
    data_fetcher = DataFetcherWorker()
    database_manager = DatabaseManager(r"data/user/database.db")
    view = AudioView(data_fetcher, database_manager)
    
    with open ("data/app/watch_playlist.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        view.load_from_data(data, "MPREb_GdL2zr1Ks0v")
    
    view.show()
    with loop:
        loop.run_until_complete(app_end_event.wait())