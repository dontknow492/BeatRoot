from qfluentwidgets import TitleLabel, PrimaryPushButton
from qfluentwidgets import PrimaryPushButton, SearchLineEdit
from qfluentwidgets import SearchLineEdit, RoundMenu, Action, FluentIcon


import sys
sys.path.append(r'D:\Program\Musify')

from loguru import logger

from src.common.myScroll import SideScrollWidget, VerticalScrollWidget
from src.common.myFrame import VerticalFrame
from src.components.cards.infoCard import DisplayStats
from src.components.cards.portraitCard import PlaylistCard, PortraitAlbumCard
from src.components.cards.artistCard import ArtistCard
from src.components.cards.audioCard import AudioCard
from src.utility.downloader.thumbnail_downloader import ThumbnailDownloader
from src.utility.enums import ImageFolder
from src.utility.iconManager import ThemedIcon

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QSpacerItem, QSizePolicy, QStackedWidget
from PySide6.QtCore import Qt, QSize, Signal, QObject, QTimer


import queue


class SearchResultScreen(VerticalFrame):
    playlistCardClicked = Signal(str)
    playlistPlayClicked = Signal(str)
    playlistAddtoClicked = Signal(dict)
    artistCardClicked = Signal(str)
    albumCardClicked = Signal(str)
    albumPlayClicked = Signal(str)
    albumAddtoClicked = Signal(dict)
    audioCardClicked = Signal(dict)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('SearchResultInterface')
        
        self.thumbnail_downloader = ThumbnailDownloader(self)
        self.thumbnail_downloader.download_finished.connect(self.set_card_cover)
        self.has_songs = False
        self.song_count = 1
        self.cover_queue = queue.Queue()
        
        self.initUi()
        
    def set_card_cover(self, path, uid):
        object_name = f"{uid}_card"
        widget = self.findChild(QObject, object_name)
        if widget:
            widget.setCover(path)
        else:
            self.cover_queue.put((path, uid))
            logger.info(f"Card not found for: {object_name} so appending it to queue")
    
    def set_cover_from_queue(self):
        while not self.cover_queue.empty():
            path, uid = self.cover_queue.get()
            object_name = f"{uid}_card"
            card = self.findChild(QObject, object_name)
            if card:
                logger.info(f"Setting cover for: {object_name} from queue")
                card.setCover(path)
                # card.loadingLabel.hide()
                card.coverLabel.show()
            else:
                logger.error(f"Card not found for: {object_name}")

    def initUi(self):
        # Search Bar Setup
        self.searchBar = SearchLineEdit(self)
        self.searchBar.setPlaceholderText("Search")
        self.searchBar.setFixedHeight(50)

        # Media Containers Setup
        self.mediaContainer = VerticalScrollWidget(None, self)
        self.songsContainerTitle = TitleLabel("Songs", self.mediaContainer)
        self.songsContainer = VerticalFrame(parent=self.mediaContainer)
        self.loadMoreButton = PrimaryPushButton("Load More", self.mediaContainer)
        self.loadMoreButton.setCursor(Qt.PointingHandCursor)

        self.mediaContainer.addWidget(self.songsContainerTitle)
        self.mediaContainer.addWidget(self.songsContainer)
        self.mediaContainer.addWidget(self.loadMoreButton, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self._create_side_scroll_widgets()

        self.addWidget(self.searchBar)
        self.addWidget(self.mediaContainer)
    
    def _create_side_scroll_widgets(self):
        self.artistsContainer = SideScrollWidget("Artists", self.mediaContainer)
        self.albumsContainer = SideScrollWidget("Albums", self.mediaContainer)
        self.comunityPlaylistContainer = SideScrollWidget("Community Playlists", self.mediaContainer)
        self.featuredPlaylistContainer = SideScrollWidget("Featured Playlists", self.mediaContainer)
        
        
        self.mediaContainer.addWidget(self.artistsContainer)
        self.mediaContainer.addWidget(self.featuredPlaylistContainer)
        self.mediaContainer.addWidget(self.albumsContainer)
        self.mediaContainer.addWidget(self.comunityPlaylistContainer)
        
        
        self.addWidget(self.searchBar)
        self.addWidget(self.mediaContainer)
        
    
    
    def loadData(self, data):
        for content in data:
            self.create_add_MediaCard(content)
        self.toggle_containers()
    
        QTimer.singleShot(2000, self.set_cover_from_queue)
        
    def toggle_containers(self):
        contnaires = [self.artistsContainer
                    , self.albumsContainer,
                    self.featuredPlaylistContainer,
                    self.comunityPlaylistContainer
                    ]
        for container in contnaires:
            if not container.count():
                container.hide()

    def create_add_MediaCard(self, content):
        category = content.get("category", "Unknown")
        result_type = content.get("resultType", None)
        match(category):
            case "Songs":
                card = self.createAudioCard(content)
                if card:
                    self.songsContainer.addWidget(card)
            case "Artists":
                card = self.createArtistCard(content)
                if card:
                    self.artistsContainer.addWidget(card, alignment=Qt.AlignmentFlag.AlignLeft)
            case "Albums":
                card = self.createAlbumCard(content)
                if card:
                    self.albumsContainer.addWidget(card, alignment=Qt.AlignmentFlag.AlignLeft)                
            case "Featured playlists":
                card = self.createPlaylistCard(content)
                if card:
                    self.featuredPlaylistContainer.addWidget(card, alignment=Qt.AlignmentFlag.AlignLeft)                
            case "Community playlists":
                card = self.createPlaylistCard(content)
                if card:
                    self.comunityPlaylistContainer.addWidget(card, alignment=Qt.AlignmentFlag.AlignLeft)                
            case _:
                match(result_type):
                    case "artist":
                        card = self.createArtistCard(content)
                        if card:
                            self.artistsContainer.addWidget(card)
                    case "album":
                        card = self.createAlbumCard(content)
                        if card:
                            self.albumsContainer.addWidget(card)
                    case "playlist":
                        card = self.createPlaylistCard(content)
                        if card:
                            self.featuredPlaylistContainer.addWidget(card)
                    case "song":
                        card = self.createAudioCard(content)
                        if card:
                            self.songsContainer.addWidget(card)
                    case _:
                        logger.warning(f"Unknown result type:  {result_type}") 
            # case _:
            #     logger.info("Unknown category: ", category, result_type)
            
    def createPlaylistCard(self, playlist):
        playlist_id = playlist.get("playlistId", None)
        if playlist_id is None:
            logger.warning(f"Playlist ID not found: {playlist.keys()}")
            return None
        thumbnail = playlist.get("thumbnails", [{}])[-1].get("url", None)
        card = PlaylistCard()
        card.setCardInfo(playlist)
        
        self.thumbnail_downloader.download_thumbnail(
            thumbnail,
            f"{playlist_id}.png",
            ImageFolder.PLAYLIST.path,
            playlist_id
        )
        
        # card.setCover(thumbnail)
        card.clicked.connect(lambda: self.playlistCardClicked.emit(playlist_id))
        card.playButtonClicked.connect(lambda: self.playlistPlayClicked.emit(playlist_id))
        card.addButtonClicked.connect(self.playlistAddtoClicked.emit)
        return card
    
    def createArtistCard(self, artist):
        browse_id = artist.get("browseId", None)
        if browse_id is None:
            logger.warning(f"Artist ID not found: {artist.keys()}")
            return None
        thumbnail = artist.get("thumbnails", [{}])[-1].get("url", None)
        card = ArtistCard()
        card.setCardInfo(artist)
        # card.setObjectName(f"{browse_id}_card")
        self.thumbnail_downloader.download_thumbnail(
            thumbnail,
            f"{browse_id}.png",
            ImageFolder.ARTIST.path,
            browse_id
        )
        logger.debug(f"Artist Card: {card}-{card.objectName()}")
        card.clicked.connect(lambda: self.artistCardClicked.emit(browse_id))
        return card
    
    def createAlbumCard(self, album):
        browse_id = album.get("browseId", None)
        if browse_id is None:
            logger.warning(f"Album ID not found in album: {album.keys()}")
            return None
        card = PortraitAlbumCard()
        card.setCardInfo(album)
        card.infoLabel.show()
        self.thumbnail_downloader.download_thumbnail(
            album.get("thumbnails", [{}])[-1].get("url", None),
            f"{browse_id}.png",
            ImageFolder.ALBUM.path,
            browse_id
        )
        card.clicked.connect(lambda: self.albumCardClicked.emit(browse_id))
        card.playButtonClicked.connect(lambda: self.albumPlayClicked.emit(browse_id))
        card.addButtonClicked.connect(self.albumAddtoClicked.emit)
        return card
    
    def createAudioCard(self, audio):
        video_id = audio.get("videoId", None)
        if video_id is None:
            logger.warning(f"Audio ID not found: {audio.keys()}")
            return None
        if self.findChild(AudioCard, f"{video_id}_card"):
            logger.warning(f"Audio card already exists: {video_id}")
            return None
        thumbnail = audio.get("thumbnails", [{}])[-1].get("url", None)
        
        card = AudioCard()
        card.setObjectName(f"{video_id}_card")
        card.setCardInfo(audio)
        card.setCount(self.song_count)
        self.song_count +=1
        self.thumbnail_downloader.download_thumbnail(
            thumbnail,
            f"{video_id}.png",
            ImageFolder.SONG.path,
            video_id
        )
        card.clicked.connect(lambda: self.audioCardClicked.emit(audio))
        self.create_audio_menu(card)
        return card
    
    def create_audio_menu(self, card: AudioCard):
        menu = RoundMenu()
        menu.setCursor(Qt.CursorShape.PointingHandCursor)
        menu.addActions([
            Action(FluentIcon.RIGHT_ARROW,"Add to queue"),
            Action(FluentIcon.ADD_TO,"Add to playlist"),
            Action(FluentIcon.HEART,"Add to favorites"),
            Action(FluentIcon.ALBUM,"Go to album")
            ])
        menu.addSeparator()
        menu.addActions([
            Action(FluentIcon.DOWNLOAD, "Download"),
            Action(FluentIcon.GLOBE,"Open in Browser"),
            Action(FluentIcon.SHARE,"Share")
        ])
        card.setMenu(menu)
    
    def clear_results(self):
        self.songsContainer.clear()
        self.artistsContainer.clear()
        self.albumsContainer.clear()
        self.featuredPlaylistContainer.clear()
        self.comunityPlaylistContainer.clear()
        self.query = None
        self.song_count = 1
        self.has_songs = False
        

if (__name__ == "__main__"):
    import json
    app = QApplication([])
    widget = SearchResultScreen()
    with open("data/app/search.json", "r") as f:
        data = json.load(f)
        
    # widget.setSearchData()
    widget.loadData(data)
    widget.show()
    app.exec()