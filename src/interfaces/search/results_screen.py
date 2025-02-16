from qfluentwidgets import TitleLabel, PrimaryPushButton
from qfluentwidgets import PrimaryPushButton, SearchLineEdit
from qfluentwidgets import SearchLineEdit


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

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QSpacerItem, QSizePolicy, QStackedWidget
from PySide6.QtCore import Qt, QSize, Signal, QObject


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
        self.has_artists = False
        self.has_albums = False
        self.has_feature_playlists = False
        self.has_community_playlists = False
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
            card = self.findChild(QFrame, object_name)
            if card:
                logger.info(f"Setting cover for: {object_name} from queue")
                card.setCover(path)
                # card.loadingLabel.hide()
                card.coverLabel.show()
            else:
                logger.error(f"Card not found for: {object_name}")

    def initUi(self):
        self.searchBar = SearchLineEdit(self)
        self.searchBar.setPlaceholderText("Search")
        self.searchBar.setClearButtonEnabled(True)
        self.searchBar.setFixedHeight(50)
        self.searchBar.setClearButtonEnabled(True)
        self.searchBar.setClearButtonEnabled(True)
        
        
        self.mediaContainer = VerticalScrollWidget(None, self)
        self.mediaContainer.setObjectName("mediaContainer")
        
        # hidden by default show as there media was found in create_add_Media Function
        self.songsContainerTitle = TitleLabel("Songs", self.mediaContainer)
        self.songsContainer = VerticalFrame(parent = self.mediaContainer)
        self.songsContainer.setObjectName("songsContainer")
        self.songsContainer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.songsContainerSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        
        self.loadMoreButton = PrimaryPushButton("Load More", self.mediaContainer)
        self.loadMoreButton.setCursor(Qt.PointingHandCursor)
        
        
        self.artistsContainer = SideScrollWidget("Artists", self.mediaContainer)
        self.artistsContainer.setFixedHeight(300)
        self.artistsContainerSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.albumsContainer = SideScrollWidget("Albums", self.mediaContainer)
        self.albumsContainer.setFixedHeight(350)
        self.albumsContainerSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.comunityPlaylistContainer = SideScrollWidget("Community Playlists", self.mediaContainer)
        self.comunityPlaylistContainer.setFixedHeight(350)
        self.comunityPlaylistContainerSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.featuredPlaylistContainer = SideScrollWidget("Featured Playlists", self.mediaContainer)
        self.featuredPlaylistContainer.setFixedHeight(350)
        self.featuredPlaylistContainerSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        
        self.mediaContainer.addWidget(self.songsContainerTitle)
        self.mediaContainer.addWidget(self.songsContainer)
        self.mediaContainer.addWidget(self.loadMoreButton, alignment=Qt.AlignmentFlag.AlignCenter)
        self.mediaContainer.addWidget(self.artistsContainer)
        self.mediaContainer.addWidget(self.featuredPlaylistContainer)
        self.mediaContainer.addWidget(self.albumsContainer)
        self.mediaContainer.addWidget(self.comunityPlaylistContainer)
        
        
        self.addWidget(self.searchBar)
        self.addWidget(self.mediaContainer)
        
    
    def setSearchData(self, data):
        self.searchData = data
    
    def loadData(self):
        if not hasattr(self, "searchData"):
            return
        for content in self.searchData:
            self.create_add_MediaCard(content)
        self.toggle_containers()
        
        self.songsContainer.addSpacerItem(self.songsContainerSpacer)
        self.artistsContainer.addSpacerItem(self.artistsContainerSpacer)
        self.albumsContainer.addSpacerItem(self.albumsContainerSpacer)
        self.featuredPlaylistContainer.addSpacerItem(self.featuredPlaylistContainerSpacer)
        self.comunityPlaylistContainer.addSpacerItem(self.comunityPlaylistContainerSpacer)
        
    def toggle_containers(self):
        self.query = self.searchBar.text()        
        if not self.has_songs:
            self.songsContainer.hide()
            self.songsContainerTitle.hide()
            self.loadMoreButton.hide()
            logger.info(f"No songs found for query: {self.query}")
            
        if not self.has_artists:
            self.artistsContainer.hide()
            logger.info(f"No artists found for query: {self.query}")
            
        if not self.has_albums:
            self.albumsContainer.hide()
            logger.info(f"No albums found for query: {self.query}")
            
        if not self.has_feature_playlists:
            self.featuredPlaylistContainer.hide()
            logger.info(f"No featured playlists found for query: {self.query}")
            
        if not self.has_community_playlists:
            self.comunityPlaylistContainer.hide()
            logger.info(f"No community playlists found for query: {self.query}")
    
    def create_add_MediaCard(self, content):
        category = content.get("category", "Unknown")
        result_type = content.get("resultType", None)
        match(category):
            case "Songs":
                card = self.createAudioCard(content)
                if card:
                    self.songsContainer.addWidget(card)
                    self.has_songs = True
            case "Artists":
                card = self.createArtistCard(content)
                if card:
                    self.artistsContainer.addWidget(card, alignment=Qt.AlignmentFlag.AlignLeft)
                    self.has_artists = True
            case "Albums":
                card = self.createAlbumCard(content)
                if card:
                    self.albumsContainer.addWidget(card, alignment=Qt.AlignmentFlag.AlignLeft)
                    self.has_albums = True
            case "Featured playlists":
                card = self.createPlaylistCard(content)
                if card:
                    self.featuredPlaylistContainer.addWidget(card, alignment=Qt.AlignmentFlag.AlignLeft)
                    self.has_feature_playlists = True
            case "Community playlists":
                card = self.createPlaylistCard(content)
                if card:
                    self.comunityPlaylistContainer.addWidget(card, alignment=Qt.AlignmentFlag.AlignLeft)
                    self.has_community_playlists = True
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
        self.thumbnail_downloader.download_thumbnail(
            thumbnail,
            f"{browse_id}.png",
            ImageFolder.ARTIST.path,
            browse_id
        )
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
        thumbnail = audio.get("thumbnails", [{}])[-1].get("url", None)
        
        card = AudioCard()
        card.setCardInfo(audio)
        self.thumbnail_downloader.download_thumbnail(
            thumbnail,
            f"{video_id}.png",
            ImageFolder.SONG.path,
            video_id
        )
        card.clicked.connect(lambda: self.audioCardClicked.emit(audio))
        return card
    
    def clear_results(self):
        self.songsContainer.clear()
        self.artistsContainer.clear()
        self.albumsContainer.clear()
        self.featuredPlaylistContainer.clear()
        self.comunityPlaylistContainer.clear()
        self.has_songs = False
        self.has_artists = False
        self.has_albums = False
        self.has_feature_playlists = False
        self.has_community_playlists = False
        
        