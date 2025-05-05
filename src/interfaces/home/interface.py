

import asyncio
import json
import sys
from pathlib import Path

import PySide6.QtAsyncio as QtAsyncio
import aiofiles
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication, QStackedWidget
from loguru import logger

from src.api.data_fetcher import DataFetcherWorker, YTMusicMethod
from src.interfaces.home.base import HomeScreen
from src.interfaces.home.sketeton_animation import HomeAnimationSkeleton
from src.utility.check_net_connectivity import is_connected_to_internet
from src.utility.enums import DataPath
from src.utility.validator import validate_path

import os
import time
import json





class HomeInterface(QStackedWidget):
    """
    The `HomeInterface` class manages the user interface for the home screen of the application. 
    It switches between different widgets (e.g., HomeScreen, HomeAnimationSkeleton), handles 
    signals for user interactions, and fetches data for the home screen when necessary.

    Attributes:
        data_fetcher (DataFetcherWorker): Worker responsible for fetching home screen data.
        homeScreen (HomeScreen): Widget for displaying the main home screen.
        homeAnimationSkeleton (HomeAnimationSkeleton): Widget for displaying loading animations.

    Signals:
        audioCardClicked (str): Emitted when an audio card is clicked.
        artistCardClicked (str): Emitted when an artist card is clicked.
        albumCardClicked (str): Emitted when an album card is clicked.
        playlistCardClicked (str): Emitted when a playlist card is clicked.
        genreSelected (str): Emitted when a genre is selected.
        moreGenreClicked: Emitted when the "More Genres" button is clicked.
        noInternet: Emitted when Not internet in device.
    """

    audioCardClicked = Signal(str)
    artistCardClicked = Signal(str)
    albumCardClicked = Signal(str)
    playlistCardClicked = Signal(str)
    audioPlayClicked = Signal(dict)
    audioAddToPlaylistClicked = Signal(dict)
    playlistPlayClicked = Signal(str)
    playlistAddtoClicked = Signal(dict)
    albumPlayClicked = Signal(str)  
    albumAddtoClicked = Signal(dict)
    genreSelected = Signal(str)
    moreGenreClicked = Signal()
    noInternet = Signal()
    errorOccured = Signal(str)

    MAX_AGE_SECONDS = 3 * 60 * 60  # 3 hours

    def __init__(self, data_fetcher: DataFetcherWorker, parent=None):
        """
        Initializes the HomeInterface with a data fetcher and sets up the UI.

        Args:
            data_fetcher (DataFetcherWorker): The worker responsible for fetching home data.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.setObjectName('HomeInterface')
        

        self.data_fetcher = data_fetcher
        self.data_fetcher.data_fetched.connect(self._on_fetch_finished)

        self.genre_request_id = None
        self.home_request_id = None 
        
        self.home_screen = HomeScreen()
        self.loading_screen = HomeAnimationSkeleton()
        self.addWidget(self.home_screen)
        self.addWidget(self.loading_screen)
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Connects signals from the home screen to the appropriate signals of this class."""
        self.home_screen.playlistCardClicked.connect(self.playlistCardClicked.emit)
        self.home_screen.artistCardClicked.connect(self.artistCardClicked.emit)
        self.home_screen.albumCardClicked.connect(self.albumCardClicked.emit)
        self.home_screen.genreSelected.connect(self.genreSelected.emit)
        self.home_screen.moreGenreClicked.connect(self.moreGenreClicked.emit)
        self.home_screen.audioCardClicked.connect(self.audioCardClicked.emit)
        self.home_screen.audioPlayClicked.connect(self.audioPlayClicked.emit)
        self.home_screen.audioAddToPlaylistClicked.connect(self.audioAddToPlaylistClicked.emit)
        self.home_screen.playlistPlayClicked.connect(self.playlistPlayClicked.emit)
        self.home_screen.playlistAddtoClicked.connect(self.playlistAddtoClicked.emit)
        
    def switch_to(self, widget):
        """
        Switches the current widget to the specified one, starting or stopping animations as needed.

        Args:
            widget (QWidget): The widget to switch to.
        """
        if widget not in [self.home_screen, self.loading_screen]:
            logger.exception(f"Invalid widget: {widget}")
            raise ValueError(f"Invalid widget: {widget}")
        if widget == self.home_screen:
            self.loading_screen.stop_animation()
        elif widget == self.loading_screen:
            self.loading_screen.start_animation()
        self.setCurrentWidget(widget)
    
    def _on_fetch_finished(self, data, uid):
        if uid == self.home_request_id:
            self._on_home_fetched(data)
            asyncio.create_task(self.save_data(data, DataPath.HOMEPAGE))
        elif uid == self.genre_request_id:
            self._on_genre_fetched(data)
            asyncio.create_task(self.save_data(data, DataPath.GENRE_CATEGORY))
            
    def _fetch_genres(self):
        self.genre_path =  DataPath.GENRE_CATEGORY.getAbsPath
        logger.info(self.genre_path)
        if Path(self.genre_path).exists():
            logger.info(f"loading genres form local file: {self.genre_path}")
            with open(self.genre_path, 'r') as file:
                data = json.load(file)
                self._on_genre_fetched(data)
        elif not is_connected_to_internet():
            logger.warning("No internet connection")
            self.noInternet.emit()
        else:
            logger.info("loading form api")
            self.genre_request_id = self.data_fetcher.add_request(YTMusicMethod.GET_GENRE)
        
    def _on_genre_fetched(self, data):
        count = 1
        for key in data.keys():
            for genre in data.get(key, []):
                if count > 10:
                        break
                if self.home_screen.addHomeGenre(genre):
                    count += 1
        self.save_data(data, DataPath.GENRE_CATEGORY)
                    
                    
    def load_home(self):
        """
        Checks if home data exists locally. If it exists, loads the data from the file 
        and sets up the UI. If it does not exist, fetches the data, saves it to the file, 
        and then sets up the UI.
        """
        
        if not is_connected_to_internet():
            logger.warning("No internet connection")
            self.noInternet.emit()
            return
        home_path = DataPath.HOMEPAGE.getAbsPath
        if validate_path(home_path, 'file'):
            try:
                file_age = time.time() - os.path.getmtime(home_path)
                if file_age > self.MAX_AGE_SECONDS:
                    logger.info(f"Home data file is older than 3 hours, deleting: {home_path}")
                    os.remove(home_path)
                    raise FileNotFoundError("Old home data file removed.")

                logger.info(f"Loading home data from existing file: {home_path}")
                with open(home_path, 'r') as file:
                    data = json.load(file)  # Assuming data is in JSON format
                self.home_screen.setHomeData(data)
                self.home_screen.loadData()
                self.switch_to(self.home_screen)
                logger.info("Home UI loaded from file.")
            except Exception as e:
                logger.exception(f"Error loading data from file: {e}")
                logger.info("Falling back to fetching home data.")
                self._fetch_home_data()
        else:
            logger.info("Home data file not found. Fetching home data.")
            self._fetch_home_data()

    def _fetch_home_data(self):
        """
        Initiates data fetching for the home screen. Saves the fetched data to the file 
        and sets it up for the UI once ready.
        """
        logger.info("Fetching home data...")
        self.switch_to(self.loading_screen)
        try:
            self.home_request_id = self.data_fetcher.add_request(YTMusicMethod.GET_HOME)
        except Exception as e:
            logger.exception(f"Error starting data fetcher: {e}")
            self.switch_to(self.home_screen)

    def _on_home_fetched(self, data):
        """
        Handles the event when home data is fetched. Saves the data to a file and sets 
        it up on the home screen.

        Args:
            data: The fetched data for the home screen.
        """
        try:
            logger.info("Home data fetched successfully.")
            self.home_screen.setHomeData(data)
            self.home_screen.loadData()
            self.save_data(data, DataPath.HOMEPAGE)
            logger.success("Home UI loaded.")
            self.loading_screen.stop_animation()
            self.switch_to(self.home_screen)
        except Exception as e:
            logger.exception(f"Error saving or setting home data: {e}")
            self.switch_to(self.home_screen)
            
    
    def save_data(self, data, path: DataPath):
        file_path = path.getAbsPath
        os.makedirs(Path(file_path).parent, exist_ok=True)
        try:
            with open(file_path, 'w') as file:
                file.write(json.dumps(data, indent=4))
            logger.info(f"Data saved to {file_path}")
        except Exception as e:
            logger.exception(f"Error saving data to {file_path}: {e}")



if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Initialize the DataFetcherWorker and start it
    dataFetcher = DataFetcherWorker()
    dataFetcher.start()

    # Create the window interface and set it up
    window = HomeInterface(dataFetcher)
    window._fetch_genres()
    window.resize(800, 600)
    window.show()
    # Connect the signals to log actions
    window.moreGenreClicked.connect(lambda: logger.info("more genre clicked"))
    window.genreSelected.connect(lambda x: logger.info(x))
    window.audioCardClicked.connect(lambda x: logger.info(x))
    window.artistCardClicked.connect(lambda x: logger.info(x))
    window.albumCardClicked.connect(lambda x: logger.info(x))
    window.playlistCardClicked.connect(lambda x: logger.info(x))
    window.audioPlayClicked.connect(lambda x: logger.info(x))
    window.audioAddToPlaylistClicked.connect(lambda x: logger.info(x))
    window.playlistAddtoClicked.connect(lambda x: logger.info(x))
    window.playlistPlayClicked.connect(lambda x: logger.info(x))
    # Load the home page
    window.load_home()
    QtAsyncio.run()
    # Start the Qt event loop with asyncio integration