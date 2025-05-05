from qfluentwidgets import ScrollArea, PrimaryPushButton, PrimaryToolButton, StrongBodyLabel, RoundMenu, Action

import sys
from src.common.myScroll import VerticalScrollWidget
from src.common.myFrame import HorizontalFrame
from src.components.filters.filter import FilterView
from src.components.cards.audioCard import AudioCard
from src.utility.song_utils import generate_xxhash_uid, get_metadata, get_songs_from_dir
from src.utility.duration_parse import seconds_to_duration
from src.utility.enums import SortType, ImageFolder
from src.utility.database_utility import DatabaseManager

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPixmap

from qasync import QEventLoop, asyncClose, asyncSlot

from loguru import logger
import asyncio

class LocalView(VerticalScrollWidget):
    add_audio_to_queue = Signal(dict)
    play_dir = Signal(str)
    audioClicked = Signal(dict, int) #data, index(for selected in queue)
    BATCH_SIZE = 5
    def __init__(self, folder_id: str, directroy_path: str, database_manager: DatabaseManager, parent=None):
        self.title = directroy_path.split('/')[-1]
        super().__init__(self.title, parent)
        
        self.folder_id = folder_id
        self.directory_path = directroy_path
        self.semaphore = asyncio.Semaphore(5)  # Limit concurrent add_song calls
        self.database_manager = database_manager
        self.songs = dict() #{path: {card, metadata}}
        self.song_count = 1
        
        
        self.setObjectName("LocalView")
        self.initUi()
        self.init_sort_menu()
        self._signal_handler()
        
    def initUi(self):
        self.filterView = FilterView(self)
        self.addWidget(self.filterView)
        self.not_found_label = StrongBodyLabel(self)
        
    def init_sort_menu(self):
        menu = RoundMenu()
        
        for sort_type in SortType:
            action = Action(sort_type.description)
        #     action.triggered.connect(lambda _, st=sort_type: self.sort_songs(st))
            menu.addAction(action)
        self.filterView.set_menu(menu)
        
    def _signal_handler(self):
        self.filterView.sortingChanged.connect(self.sort_songs)
        self.filterView.searchBar.searchSignal.connect(self.search_song)
        self.filterView.searchBar.textChanged.connect(self.on_search_text_changed)
        self.filterView.refreshClicked.connect(self.scan_dir)
        
    def _create_menu(self, card):
        menu = RoundMenu()
        menu.addAction(Action("Add to Queue",parent = card, triggered= lambda: self.add_to_queue(card)))
        menu.addAction(Action("Delete", parent = card, triggered= lambda: self.on_remove_song(card)))
        return menu
        
    @asyncSlot()
    async def scan_dir(self):
        """Scans directory for songs and adds them asynchronously in batches."""
        logger.info(f"Scanning directory: {self.directory_path}")

        song_paths = get_songs_from_dir(self.directory_path)

        for i in range(0, len(song_paths), self.BATCH_SIZE):
            batch = song_paths[i : i + self.BATCH_SIZE]
            await asyncio.gather(*(self.add_song(song) for song in batch))
            await asyncio.sleep(0.1)

    
    @asyncSlot()
    async def add_song(self, song_path: str):
        """Adds a song to the UI and metadata storage."""
        async with self.semaphore:  # Limit concurrent executions
            if self.check_song_exists(song_path):
                logger.debug(f"Card with path: {song_path} already exists")
                return

            card = await self.create_audio_card(song_path)
            if card:
                self.songs[song_path] = {
                    "card": card,
                    "metadata": card.get_card_data()
                }
                self.addWidget(card)

            await asyncio.sleep(0.9)  # Correctly await the sleep

    @asyncSlot()            
    async def create_audio_card(self, song_path: str):
        """Creates an audio card with metadata."""
        logger.debug(f"Creating card for: {song_path}")
        
        metadata = await self.song_metadata(song_path)
        if not metadata:
            logger.warning(f"Skipping {song_path}: No metadata found.")
            return None

        logger.debug(f"Metadata retrieved for {song_path}-{metadata["videoId"]}")
        
        audio_card = AudioCard(False)
        audio_card.setCardInfo(metadata)
        cover = metadata.get('cover')
        if cover:
            self.set_card_cover_from_data(audio_card, cover)
        else:
            cover = f"{ImageFolder.SONG.path}\\{metadata.get('videoId')}.png"
            audio_card.setCover(cover)
        audio_card.setMenu(self._create_menu(audio_card))
        
        audio_card.setCount(self.song_count)
        audio_card.clicked.connect(lambda: self.audioClicked.emit(audio_card.get_card_data(), audio_card.getCount() - 1))
        self.song_count += 1

        return audio_card

    @asyncSlot()
    async def song_metadata(self, song_path: str):
        """Retrieves song metadata from the database or extracts it if missing."""
        song_id = generate_xxhash_uid(song_path)
        
        # Fetch metadata from database
        metadata = await self.database_manager.get_local_song(song_id)
        if metadata:
            metadata.update({"videoId": song_id, "path": song_path})
        if metadata:
            logger.info("Loading data from database: ")
            return metadata

        # Extract metadata if not in the database
        metadata = get_metadata(song_path)
        metadata.update({"videoId": song_id, "path": song_path})
        if not metadata:
            logger.warning(f"Failed to extract metadata for {song_path}")
            return None

        # metadata.update({"videoId": song_id, "path": song_path})
        # Insert into database asynchronously
        asyncio.create_task(self.database_manager.insert_local_song(metadata))
        asyncio.create_task(self.database_manager.insert_directory_songs(song_id, self.folder_id, song_path))
        return metadata
        
    def check_song_exists(self, song_path: str):
        if song_path in self.songs.keys():
            return True
        return False
    
    def search_song(self, text):
        # print(matching_tracks)
        for key, value in self.songs.items():
            file_name = key.split("\\")[-1]
            # logger.debug(f"Searching for {text} in {file_name}")
            if text.lower() in file_name.lower():
                value['card'].show()
            else:
                value['card'].hide()
                        
    def set_card_cover_from_data(self, card: AudioCard, data):
        if data is None:
            return
        size = card.coverLabel.size()
        pixamp = QPixmap()
        pixamp.loadFromData(data)
        card.coverLabel.setImage(pixamp)
        card.coverLabel.setFixedSize(size)
        path = f"{ImageFolder.SONG.path}\\{card.getAudioId()}.png"
        logger.info(f"Saving cover to {path}")
        pixamp.save(path, "PNG", 100)
        
    def update_count(self):
        self.song_count = 1
        for value in self.songs.values():
            value['card'].setCount(self.song_count)
            self.song_count += 1
        
    def on_search_text_changed(self, text):
        if not text:
            self.reset_search()
        
    def reset_search(self):
        for i in range(self.count()):
            self.itemAt(i).widget().show()
            
    def on_remove_song(self, card: AudioCard):
        self.removeWidget(card)
        self.remove_card_from_songs(card)
        card.deleteLater()
        self.update_count()
        
    def remove_card_from_songs(self, card):
        key_to_remove = None  # Store key to remove

        for key, value in self.songs.items():
            if value['card'] == card:
                key_to_remove = key
                break  # Stop once found

        if key_to_remove is not None:
            del self.songs[key_to_remove]  # Remove the entire key

        
    def add_to_queue(self, card: AudioCard):
        data = card.get_card_data()
        logger.debug(f"Adding to queue: {data}")
        self.add_audio_to_queue.emit(data)
    
    def sort_songs(self, sort_by: str):
        pass
        
    def get_tracks(self):
        tracks = list()
        for value in self.songs.values():
            tracks.append(value['metadata'])
                    
        return tracks
    def get_id(self):
        return self.folder_id
        
if(__name__ == "__main__"):
    app = QApplication([])
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    app_end_event = asyncio.Event()
    
    app.aboutToQuit.connect(app_end_event.set)
    
    database_manager = DatabaseManager(r"data/user/database.db")
    view = LocalView("P97ASBQMTRESV03N62", r"D:\Media\Music\Dance", database_manager)
    
    view.show()
    # QTimer.singleShot(1000, view.scan_dir)
    # QTimer.singleShot(1000, lambda: view.load_from_database("RDCLAK5uy_kiDNaS5nAXxdzsqFElFKKKs0GUEFJE26w"))
    view.audioClicked.connect(lambda data, index: logger.info(f"Clicked: {data} - {index}"))
    
    with loop:
        loop.run_until_complete(app_end_event.wait())
        
    sys.exit()
