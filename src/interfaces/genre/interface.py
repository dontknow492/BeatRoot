from qfluentwidgets import FlowLayout, TitleLabel, PrimaryPushButton

import sys
sys.path.append(r'D:\Program\Musify')

from src.api.data_fetcher import DataFetcherWorker, YTMusicMethod
from src.utility.check_net_connectivity import is_connected_to_internet
from src.interfaces.genre.genre_playlist_interface import GenrePlaylistView
from src.interfaces.genre.sketeton_animation import GenrePlaylistsSkeleton

from PySide6.QtWidgets import QStackedWidget
from PySide6.QtCore import QTimer, Qt, Signal
import sys
from loguru import logger



class GenrePlaylistsInterface(QStackedWidget):
    noInternet = Signal()
    playlistCardClicked = Signal(str)
    # errorSignal = Signal(str)
    def __init__(self, data_fetcher: DataFetcherWorker, parent=None):
        super().__init__(parent)
        self.setObjectName('Genres')
        
        self.data_fetcher = data_fetcher
        self.data_fetcher.error_occurred.connect(self._on_fetch_error)
        self.data_fetcher.data_fetched.connect(self._on_genre_data_ready)
        self.genre_id = None
        self.genre_request_id = None
        
        self.genre_playlists = GenrePlaylistView()
        self.loading_screen = GenrePlaylistsSkeleton()
        self.addWidget(self.genre_playlists)
        self.addWidget(self.loading_screen)
        # self.setCurrentIndex(2)
        self._setup_signal_handlers()
        
        self.button = PrimaryPushButton("hello", self)
        self.button.clicked.connect(lambda: self.load_genre("ggMPOg1uX09LWkhnTjRGRUJh"))
        self.button.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.button.move(200, 200)
        
        
    
        
    def _setup_signal_handlers(self):
        self.genre_playlists.playlistCardClicked.connect(self.playlistCardClicked.emit)
        
    def on_fetch_error(self, error):
        print("error occured here brok do something")
        sys.exit()
        self.loading_screen.stop_animation()
        
    def switch_to(self, widget):
        """
        Switches the current widget to the specified one, starting or stopping animations as needed.

        Args:
            widget (QWidget): The widget to switch to.
        """
        if widget not in [self.genre_playlists, self.loading_screen]:
            logger.exception(f"Invalid widget: {widget}")
            raise ValueError(f"Invalid widget: {widget}")
        if widget == self.genre_playlists:
            self.loading_screen.stop_animation()
        elif widget == self.loading_screen:
            self.loading_screen.start_animation()
        self.setCurrentWidget(widget)

    def load_genre(self, genre_id):
        if genre_id is self.genre_id:
            logger.info("allready loaded")
            return
        if not is_connected_to_internet():
            self.noInternet.emit()
            return
        if genre_id:
            self.genre_id = genre_id
            self._fetch_genre_data(genre_id)

    def _fetch_genre_data(self, genre_id):
        """
        Initiates data fetching for the search screen. Saves the fetched data to the file 
        and sets it up for the UI once ready.
        """
        logger.info("Fetching search data...")
        self.switch_to(self.loading_screen)
        # self.data_fetcher.data_fetched.connect(self._on_genre_data_ready)
        # self.data_fetcher.error_occurred.connect(self._on_fetch_error)
        try:
            
            self.genre_request_id = self.data_fetcher.add_request(YTMusicMethod.GET_MOOD_PLAYLISTS, genre_id)
        except Exception as e:
            logger.exception(f"Error starting data fetcher: {e}")
            self.switch_to(self.genre_playlists)

    def _on_genre_data_ready(self, data, uid):
        """
        Handles the event when search data is fetched. Saves the data to a file and sets 
        it up on the search screen.

        Args:
            data: The fetched data for the search screen.
        """
        if uid != self.genre_request_id:
            return
        logger.info("Genre data fetched successfully.")
        # Set the data to the search screen
        self.genre_playlists.setGenreData(data)
        self.genre_playlists.ui_loaded.connect(self._on_genre_ui_loaded)
        self.genre_playlists.loadData()

    
    def _on_genre_ui_loaded(self):
        """Handles the event when the search UI has finished loading."""
        logger.info("search UI loaded.")
        self.loading_screen.stop_animation()
        self.switch_to(self.genre_playlists) 
        self.button.raise_()
        
    def _on_fetch_error(self, error):
        logger.error(f"Error fetching data: {error}")
        
    