from qfluentwidgets import ImageLabel, BodyLabel, TitleLabel, TransparentToolButton, TransparentPushButton

import aiofiles
import asyncio
import sys

from pathlib import Path

from src.common.myScroll import SideScrollWidget, HorizontalScrollWidget, VerticalScrollWidget
from src.common.myFrame import VerticalFrame, HorizontalFrame, FlowFrame
from src.components.cards.infoCard import DisplayStats
from src.components.cards.portraitCard import PlaylistCard, PortraitAudioCard, PortraitAlbumCard, PortraitCardBase
from src.components.cards.groupCard import GroupCard
from src.components.cards.genreCard import SimpleGenreCard
from src.components.cards.artistCard import ArtistCard
from src.utility.iconManager import ThemedIcon
from src.utility.downloader.thumbnail_downloader import ThumbnailDownloader
from src.utility.enums import DataPath, ImageFolder


from PySide6.QtWidgets import QFrame, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QSize, Signal


from enum import Enum
import sys

from queue import Queue
from loguru import logger


class ContentType(Enum):
    SONG = "song"
    PLAYLIST = "playlist"
    VIDEO = "video"
    ARTIST = "artist"
    ALBUM = "album"
    UNKNOWN = "unknown"

    # Define a dictionary mapping each content type to its keys
    # Define a dictionary mapping each content type to its keys with data types
    _keys_mapping = {
        "song": [
            {"title": "str"},
            {"videoId": "str"},
            {"artists": "list[dict{name: str, id: str}]"},
            {"album": "dict[name: str, id: str]"},
            {"thumbnails": "list[dict[url: str, width: int, height: int]]"}
        ],
        "playlist": [
            {"title": "str"},
            {"playlistId": "str"},
            {"description": "str"},
            {"count": "int"},
            {"author": "list[dict{name: str, id: str}]"},
            {"thumbnails": "list[dict[url: str, width: int, height: int]]"}
        ],
        "video": [
            {"title": "str"},
            {"videoId": "str"},
            {"artists": "list[dict{name: str, id: str}]"},
            {"views": "int"},
            {"thumbnails": "list[dict[url: str, width: int, height: int]]"}
        ],
        "artist": [
            {"title": "str"},
            {"browseId": "str"},
            {"subscribers": "int"},
            {"thumbnails": "list[dict[url: str, width: int, height: int]]"}
        ],
        "album": [
            {"title": "str"},
            {"browseId": "str"},
            {"year": "int"},
            {"thumbnails": "list[dict[url: str, width: int, height: int]]"}
        ],
        "unknown": []
    }
    
    @property
    def keys(self):
        # Fetch keys with data types for the current enum value
        return self._keys_mapping.get(self.value, [])
    
    
    
class HomeScreen(VerticalScrollWidget):
    audioCardClicked = Signal(str)
    artistCardClicked = Signal(str)
    albumCardClicked = Signal(str)
    playlistCardClicked = Signal(str)
    genreSelected = Signal(str)
    moreGenreClicked = Signal()
    audioPlayClicked = Signal(dict)
    audioAddToPlaylistClicked = Signal(dict)
    playlistPlayClicked = Signal(str)
    playlistAddtoClicked = Signal(dict)
    albumPlayClicked = Signal(str)
    albumAddtoClicked = Signal(dict)
    def __init__(self, title: str = None, parent=None):
        super().__init__(title, parent)
        self.setObjectName('HomeScreen')
        
        self.thumbnail_downloader = ThumbnailDownloader(self)
        self.thumbnail_downloader.download_finished.connect(self.set_card_cover)
        self.thumbnail_urls = list()
        self.thumbnail_names = list()
        self.thumbnail_output_dirs = list()
        self.cover_queue = Queue()
        
        self.initGenre()
        # self.initRecent()
        # self.readHomeJson()
        
    def initGenre(self):
        self.genreInfoContainer = HorizontalFrame(self)
        self.genreTitle = TitleLabel("Genres", self.genreInfoContainer)
        self.moreGenreButton = TransparentPushButton(ThemedIcon.NEXT_ARROW, "Browse All", self.genreInfoContainer)
        self.moreGenreButton.setIconSize(QSize(12, 12))
        self.moreGenreButton.clicked.connect(self.moreGenreClicked.emit)
        self.moreGenreButton.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.genreInfoContainer.addWidget(self.genreTitle, alignment= Qt.AlignmentFlag.AlignLeading)
        spacer = QSpacerItem(10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.genreInfoContainer.addWidget(spacer)
        self.genreInfoContainer.addWidget(self.moreGenreButton, alignment= Qt.AlignmentFlag.AlignLeft)
        
        self.genreContainer = FlowFrame(self)
        self.genreContainer.setObjectName("genreContainer")
        
        self.addWidget(self.genreInfoContainer)
        self.addWidget(self.genreContainer)
        
    def addHomeGenre(self, genre):
        name = genre.get("title", "???")
        genre_id = genre.get("params", None)
        if genre_id is None:
            logger.error(f"genre_id not found for genre: {name}")
            return False
        card = SimpleGenreCard(image_path= None, text = name)
        card.setGenreId(genre_id)
        card.clicked.connect(lambda: self.genreSelected.emit(genre_id))
        self.genreContainer.addWidget(card)
        return True
        
    def loadGenres(self, genres: list):
        for genre in genres:
            self.addHomeGenre(genre)
        
    
    def initRecent(self):
        self.recentContainer = SideScrollWidget("Recently PLayed", self)
        self.recentContainer.setObjectName("recentContainer")
        self.addWidget(self.recentContainer)
        
    def addRecent(self, recent):
        card = self.createAudioCard(recent)
        if card:
            self.recentContainer.addWidget(card)
        
    def setHomeData(self, data):
        self.home_data = data
    
    def loadData(self):
        if hasattr(self, "home_data") is False:
            return
        for data in self.home_data:
            title = data.get("title", None)
            scroll_area = self.createSideScrollArea(title)
            logger.info(f"Loading ui for: {title}")
            for content in data.get("contents", []):
                # logger.info(self.categorizeContent(content).value)
                card = self.createCard(content)
                if card:
                    scroll_area.addWidget(card)
            self.addWidget(scroll_area)
            
        
        
    
    def set_card_cover(self, path, uid):
        object_name = f"{uid}_card"
        widget = self.findChild(QFrame, object_name)
        if widget:
            widget.setCover(path)
        else:
            self.cover_queue.put((path, uid))
            logger.info(f"Card not found for: {object_name} so appending it to queue")
    
    def set_cover_from_queue(self):
        while not self.cover_queue.empty():
            path, uid = self.cover_queue.get()
            object_name = f"{uid}_card"
            card = self.findChild(QFrame, object_name)
            if card:
                logger.info(f"Setting cover for: {object_name} from queue")
                card.setCover(path)
                # card.loadingLabel.hide()
                card.coverLabel.show()
            else:
                logger.error(f"Card not found for: {object_name}")
        
    def createSideScrollArea(self, title):
        scroll_area = SideScrollWidget(title, self)
        return scroll_area
    
    def createCard(self, content):
        type_ = self.categorizeContent(content)
        match type_:
            case ContentType.SONG:
                return self.createAudioCard(content)
            case ContentType.PLAYLIST:
                return self.createPlaylistCard(content)
            case ContentType.VIDEO:
                return self.createAudioCard(content)
            case ContentType.ARTIST:
                return self.createArtistCard(content)
            case ContentType.ALBUM:
                return self.createAlbumCard(content)
            case ContentType.UNKNOWN:
                return None
        
    def createPlaylistCard(self, playlist):
        playlist_id = playlist.get("playlistId", None)
        if playlist_id is None:
            logger.error(f"playlist_id not found for playlist: {playlist.get("title")}")
            return None
        thumbnail = playlist.get("thumbnails", [{}])[-1].get("url", None)
        card = PlaylistCard()
        card.setCardInfo(playlist)
        self.thumbnail_downloader.download_thumbnail(thumbnail, f"{playlist_id}.png", ImageFolder.PLAYLIST.path, playlist_id)
        card.clicked.connect(lambda: self.playlistCardClicked.emit(playlist_id))
        card.playButtonClicked.connect(lambda: self.playlistPlayClicked.emit(playlist_id))
        card.addButtonClicked.connect(self.playlistAddtoClicked.emit)
        return card
    
    def createArtistCard(self, artist):
        thumbnail = artist.get("thumbnails", [{}])[-1].get("url", None)
        browse_id = artist.get("browseId", None)
        if browse_id is None:
            logger.error(f"browse_id not found for artist: {thumbnail}")
            return None
        card = ArtistCard()
        card.setCardInfo(artist)
        self.thumbnail_downloader.download_thumbnail(thumbnail, f"{browse_id}.png", ImageFolder.ARTIST.path, browse_id)
        # card.setCover(thumbnail)
        card.clicked.connect(lambda: self.artistCardClicked.emit(browse_id))
        return card
    
    def createAlbumCard(self, album):
        browse_id = album.get("browseId", None)
        if browse_id is None:
            logger.error(f"browse_id not found for album: {album.get('title')}")
            return None
        thumbnail = album.get("thumbnails", [{}])[-1].get("url", None)
        card = PortraitAlbumCard()
        card.setCardInfo(album)
        self.thumbnail_downloader.download_thumbnail(thumbnail, f"{browse_id}.png", ImageFolder.ALBUM.path, browse_id)
        
        card.clicked.connect(lambda: self.albumCardClicked.emit(browse_id))
        card.playButtonClicked.connect(lambda: self.albumPlayClicked.emit(browse_id))
        card.addButtonClicked.connect(self.albumAddtoClicked.emit)
        return card
    
    def createAudioCard(self, audio: dict):
        song_id = audio.get("videoId", None)
        if song_id is None:
            logger.error(f"song_id not found for audio: {audio.get("title")}")
            return None
        thumbnail = audio.get("thumbnails", [{}])[-1].get("url", None)
        
        card = PortraitAudioCard()
        card.setCardInfo(audio)
        
        path = Path(ImageFolder.SONG.path, f"{song_id}.png")
        if path.exists():
            card.setCover(str(path))
        else:
            self.thumbnail_downloader.download_thumbnail(thumbnail, f"{song_id}.png", ImageFolder.SONG.path, song_id)
        
        card.clicked.connect(lambda: self.audioCardClicked.emit(song_id))
        card.playButtonClicked.connect(lambda: self.audioPlayClicked.emit(audio))
        card.addButtonClicked.connect(self.audioAddToPlaylistClicked.emit)
        return card
        
    def initCursor(self):
        self.navigationPivot.setCursor(Qt.PointingHandCursor)
        
    def categorizeContent(self, content)->ContentType:
        keys = set(content.keys())  # Convert keys to a set for easier comparison

        if {'videoId', 'artists', 'album'}.issubset(keys):
            return ContentType.SONG
        elif 'playlistId' in keys:
            return ContentType.PLAYLIST
        elif {'videoId', 'artists', 'views'}.issubset(keys):
            return ContentType.VIDEO
        elif {'browserId', 'subscriber'}.issubset(keys):
            return ContentType.ARTIST
        elif {'title', 'browseId', 'year', 'thumbnails'}.issubset(keys) or len(keys) == 3:
            return ContentType.ALBUM
        else:
            return ContentType.UNKNOWN

