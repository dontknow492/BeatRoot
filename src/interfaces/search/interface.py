
from qfluentwidgets import Theme, setTheme


import sys


from loguru import logger

from src.api.data_fetcher import DataFetcherWorker, YTMusicMethod
from src.interfaces.search.results_screen import SearchResultScreen
from src.interfaces.search.sketeton_animation import SearchResultSkeleton
from src.utility.check_net_connectivity import is_connected_to_internet

from PySide6.QtWidgets import QApplication, QStackedWidget, QScrollArea
from PySide6.QtCore import Signal


from enum import Enum
import queue

class SearchResultInterface(QStackedWidget):
    noInternet = Signal()
    playlistCardClicked = Signal(str)
    playlistPlayClicked = Signal(str)
    playlistAddtoClicked = Signal(dict)
    artistCardClicked = Signal(str)
    albumCardClicked = Signal(str)
    albumPlayClicked = Signal(str)
    albumAddtoClicked = Signal(dict)
    audioCardClicked = Signal(dict)
    def __init__(self, data_fetcher: DataFetcherWorker, parent=None):
        super().__init__(parent)
        self.setObjectName('Search')
        
        self.data_fetcher = data_fetcher
        self.data_fetcher.data_fetched.connect(self._on_fetching_finished)
        self.query = None
        self.search_request_id = None
        
        
        self.search_results_screen = SearchResultScreen(self)
        self.loading_screen= SearchResultSkeleton(self)
        
        
        
        self.addWidget(self.search_results_screen)
        self.addWidget(self.loading_screen)
        
        self._setup_signal_handler()
        
        
    def _setup_signal_handler(self):
        self.search_results_screen.playlistCardClicked.connect(self.playlistCardClicked.emit)
        self.search_results_screen.artistCardClicked.connect(self.artistCardClicked.emit)
        self.search_results_screen.albumCardClicked.connect(self.albumCardClicked.emit)
        self.search_results_screen.audioCardClicked.connect(self.audioCardClicked.emit)
        self.search_results_screen.searchBar.searchSignal.connect(self.load_search)
        self.search_results_screen.playlistPlayClicked.connect(self.playlistPlayClicked.emit)
        self.search_results_screen.playlistAddtoClicked.connect(self.playlistAddtoClicked.emit)
        self.search_results_screen.albumPlayClicked.connect(self.albumPlayClicked.emit)
        self.search_results_screen.albumAddtoClicked.connect(self.albumAddtoClicked.emit)
        self.search_results_screen.loadMoreButton.clicked.connect(self.load_more)
        
    def switch_to(self, widget):
        """
        Switches the current widget to the specified one, starting or stopping animations as needed.

        Args:
            widget (QWidget): The widget to switch to.
        """
        if widget not in [self.search_results_screen, self.loading_screen]:
            logger.exception(f"Invalid widget: {widget}")
            raise ValueError(f"Invalid widget: {widget}")
        if widget == self.search_results_screen:
            logger.info("Switching to search results screen")
            self.loading_screen.stop_animation()
            logger.info("Animation stopped")
        elif widget == self.loading_screen:
            logger.info("Switching to loading screen")
            self.loading_screen.start_animation()
            logger.info("Animation started")
        self.setCurrentWidget(widget)

    def _on_fetching_finished(self, data, uid):
        if uid == self.search_request_id:
            logger.success(f"Data succesfully fetched for search query: {self.query}")
            self._on_search_fetched(data)
            return
            
        logger.info(f"uid didnt match: { uid}")
    
    def load_search(self, query):
        if query == "":
            return
        if self.query == query:
            logger.info(f"Allready loaded for query: {query}")
            return
        self.clear_results()
        self.search_results_screen.searchBar.setText(query)
        self.query = query
        if not is_connected_to_internet():
            self.noInternet.emit()
            return
        self._fetch_search_data(query)
        
    def load_more(self):
        if not is_connected_to_internet():
            self.noInternet.emit()
            return
        if self.query is None or self.query == "":
            logger.warning("No query to load more results for.")
            return
        limit = self.search_results_screen.song_count + 10
        try:
            self.search_request_id = self.data_fetcher.add_request(YTMusicMethod.SEARCH, self.query, filter="songs", limit= limit)
        except Exception as e:
            logger.exception(f"Error starting data fetcher: {e}")
            self.switch_to(self.search_results_screen)
            
        if limit > 50:
            self.search_results_screen.loadMoreButton.hide()

    def _fetch_search_data(self, query):
        """
        Initiates data fetching for the search screen. Saves the fetched data to the file 
        and sets it up for the UI once ready.
        """
        logger.info(f"Fetching search data for query: {query}")
        self.switch_to(self.loading_screen)
        try:
            self.search_request_id = self.data_fetcher.add_request(YTMusicMethod.SEARCH, query)
        except Exception as e:
            logger.exception(f"Error starting data fetcher: {e}")
            self.switch_to(self.search_results_screen)

    def _on_search_fetched(self, data):
        """
        Handles the event when search data is fetched. Saves the data to a file and sets 
        it up on the search screen.

        Args:
            data: The fetched data for the search screen.
        """
        # Set the data to the search screen
        self.search_results_screen.loadData(data)
        logger.success("search UI loaded.")
        self.loading_screen.stop_animation()
        self.switch_to(self.search_results_screen) 
    
    def clear_results(self):
        self.search_results_screen.clear_results()

        
category = ["Albums", "Songs", "Featured playlists", "Community playlists", "Artists"]

if(__name__ == "__main__"):
    import json
    app = QApplication(sys.argv)
    setTheme(Theme.DARK)
    data_fetcher = DataFetcherWorker()
    data_fetcher.start()
    w = SearchResultInterface(data_fetcher)
    with open("data/app/search.json", "r") as f:
        data = json.load(f)
    w._on_fetching_finished(data, None)
    w.query = "arijit singh"
    # w.load_search("arijit singh")
    w.search_results_screen.searchBar.clearSignal.connect(w.clear_results)
    w.show()
    
    # print(frame.findChild(QObject, "card_0"))
    
    sys.exit(app.exec())