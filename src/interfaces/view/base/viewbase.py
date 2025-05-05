from pathlib import Path

from qfluentwidgets import FluentIcon
from queue import Queue

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame
from loguru import logger
from qfluentwidgets import FluentIcon
from qfluentwidgets import RoundMenu, Action

from src.animation import WideCardSkeleton, LandscapeAudioSkeleton
from src.common.myFrame import VerticalFrame, HorizontalFrame
from src.common.myScroll import VerticalScrollWidget
from src.components.cards.artistCard import ArtistCard
from src.components.cards.audioCard import AudioCard
from src.components.cards.portraitCard import PortraitAlbumCard
from src.components.cards.wideCard import WideCard
from src.utility.downloader.thumbnail_downloader import ThumbnailDownloader
from src.utility.enums import ImageFolder
from src.utility.image_utility import blur_pixmap
from src.utility.misc import get_thumbnail_url


class ViewBase(VerticalScrollWidget):
    uiLoaded = Signal()
    audioCardClicked = Signal(dict)
    albumClicked = Signal(str)
    artistClicked = Signal(str)
    playlistCardClicked = Signal(str)
    errorOccurred = Signal(str)
    liked = Signal(bool)
    likedSong = Signal(dict)
    queueSong = Signal(dict)
    addedTo = Signal(bool)
    play = Signal(bool)
    downloadSong = Signal(str, str) #video_id, title
    openSongInBrowser = Signal(str) #video_id
    share = Signal(str) #video_id
    def __init__(self, parent=None):
        super().__init__(title= None, parent= parent)
        
        self.data = dict()
        self.song_count = 1
        self.view_id = None
        self.thumbnails_downloader = ThumbnailDownloader(self)
        self.thumbnails_downloader.download_finished.connect(self.set_card_cover)
        self.thumbnail = None
        self.description = "Unknown"
        self.set_cover_queue = Queue()
        self.tracks = None
        self.view_card_id = None
        self.initUi()
        self._wide_card_signal()
        
    def initUi(self):
        self.container = HorizontalFrame(self)
        self.container.setStyleSheet("border-radius: 10px;")
        # self.container.hide()
        self.container.setFixedHeight(500)
        self.container.setContentsMargins(0, 0, 0, 0)
        self.container.move(-10, 0)
        self.background_pixmap = QPixmap(r"/resources/images/image_2.png")
        blur_background = blur_pixmap(self.background_pixmap, 30)
        self.container.setBackgroundImage(blur_background)
        self.viewCard = WideCard(self.scrollArea.viewport())
        self.viewCard.bodyLabel.setWordWrap(False)
        self.viewCard.adjustSize()
        
        self.container.addWidget(self.viewCard, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # self.scrollArea.verticalScrollBar().valueChanged.connect(self.update_overlay_position)

        self.addWidget(self.container)
        # self.viewCard.hide()
        
    def _wide_card_signal(self):
        self.viewCard.playClicked.connect(self.play.emit)
        # self.viewCard.shuffleClicked.connect(self.shuffle.emit)
        self.viewCard.likeClicked.connect(self.liked.emit)
        # self.viewCard.shareClicked.connect(self.share.emit)
        self.viewCard.addClicked.connect(self.addedTo.emit)
        
    def load_data(self, data):
        raise NotImplementedError
        
    def setViewId(self, view_id):
        self.view_id = view_id
        
    def getViewId(self):
        return self.view_id
    
        
    def set_card_cover(self, path, uid):
        if uid == self.view_card_id:
            self.viewCard.setImage(path)
        object_name = f"{uid}_card"
        card= self.findChild(QFrame, object_name)
        if card:
            card.setCover(path)
            # card.loadingLabel.hide()
            logger.success(f"Setting cover for: {object_name} from signal") 
            card.update()
        else:
            self.set_cover_queue.put((path, uid))
    
    def set_cover_from_queue(self):
        while not self.set_cover_queue.empty():
            path, uid = self.set_cover_queue.get()
            object_name = f"{uid}_card"
            card = self.findChild(QFrame, object_name)
            if card:
                logger.info(f"Setting cover for: {object_name} from queue")
                card.setCover(path)
                # card.loadingLabel.hide()
                card.coverLabel.show()
            else:
                logger.error(f"Card not found for: {object_name}")
    
    
    def setViewData(self, data):
        self.data = data
        
    def get_view_data(self):
        return self.data
        
    
        
        
        
    def setCardTitle(self, title: str):
        self.viewCard.setTitle(title)
        
    def getCardTitle(self):
        return self.viewCard.getTitle()
        
    def setCardBody(self, body: str):
        self.viewCard.setBody(body)
    
    def getCardBody(self):
        return self.viewCard.getBody()
    
    logger.catch    
    def setCardImage(self, image):
        self.viewCard.setImage(image)
        
    def setCardLiked(self, liked: bool):
        self.viewCard.setLiked(liked)
        
    def setCardPlaying(self, playing: bool):
        self.viewCard.setPlaying(playing)
        
    def setCardAddedTo(self, added: bool):
        self.viewCard.setAddedTo(added)
        
    def setCardShuffle(self, shuffle: bool):
        self.viewCard.shuffleButton.setChecked(shuffle)
    
    def resizeEvent(self, event):
        if self.height() <= self.container.height():
            self.container.setFixedHeight(self.height())
        else:
            self.container.setFixedHeight(500)
        return super().resizeEvent(event)
    
    def createAudioCard(self, audio, is_single: bool = False):
        # card.setSongId(songId)
        song_id = audio.get("videoId", None)
        if song_id is None:
            logger.warning(f"Song id is None: {audio}")
            return None
        card = AudioCard()
        
        thumbnails = audio.get("thumbnails", None) or audio.get("thumbnail", None)
        path = Path(ImageFolder.SONG.path) / f"{song_id}.png"
        if not path.exists():
            if thumbnails:
                self.thumbnails_downloader.download_thumbnail(thumbnails[-1].get("url", None), f"{song_id}.png", ImageFolder.SONG.path, song_id)
            else:
                self.thumbnails_downloader.download_thumbnail(get_thumbnail_url(song_id), f"{song_id}.png", ImageFolder.SONG.path, song_id)
        else:
            logger.info(f"Thumbnail already exists in cache for: {song_id}")
        if card.setCardInfo(audio, is_single):
            card.setCount(self.song_count)
            self.song_count += 1
            card.clicked.connect(lambda: self.audioCardClicked.emit(audio))
            card.albumClicked.connect(self.albumClicked.emit)
            card.artistClicked.connect(self.artistClicked.emit)
            # self.
            self.create_audio_menu(card)
            return card
        
    def create_audio_menu(self, card: AudioCard):
        menu = RoundMenu()
        data = card.get_card_data()
        title = card.getTitle()
        song_id = card.getAudioId()
        album_id = card.getAlbumId()
        menu.setCursor(Qt.CursorShape.PointingHandCursor)
        menu.addActions([
            Action(FluentIcon.RIGHT_ARROW,"Add to queue", triggered=lambda: self.queueSong.emit(data)),
            Action(FluentIcon.ADD_TO,"Add to playlist", triggered=lambda: self.addedTo.emit()),
            Action(FluentIcon.HEART,"Add to favorites", triggered=lambda: self.likedSong.emit(data))
            ])
        if album_id:
            menu.addAction(Action(FluentIcon.ALBUM,"Go to album", triggered=lambda: self.albumClicked.emit(album_id)))
        menu.addSeparator()
        menu.addActions([
            Action(FluentIcon.DOWNLOAD, "Download", triggered=lambda: self.downloadSong.emit(song_id, title)),
            Action(FluentIcon.GLOBE,"Open in Browser", triggered=lambda: self.openSongInBrowser.emit(song_id)),
            Action(FluentIcon.SHARE,"Share", triggered=lambda: self.share.emit(song_id))
        ])
        card.setMenu(menu)
        
    def setPortraitAlbumCardInfo(self, card: PortraitAlbumCard, album_data: dict):
        album_id = album_data.get("browseId", None)
        if album_id is None:
            logger.warning(f"Album id is None: {album_data.keys()}")
            return None
        title = album_data.get("title", "Unknown")
        thumbnails = album_data.get("thumbnails", None)
        type_ = album_data.get("type", "Unknown")
        if type_ == "Album":
            path = Path(ImageFolder.ALBUM.path) / f"{album_id}.png"
            if not path.exists():
                if thumbnails:
                    self.thumbnails_downloader.download_thumbnail(thumbnails[-1].get("url", None), f"{album_id}.png", ImageFolder.ALBUM.path, album_id)
                else:
                    logger.warning(f"No Thumbnail found for the: {album_id}")
            else:
                logger.info(f"Thumbnail already exists in cache for: {album_id}")
            card.setAlbumId(album_id)
            card.setTitle(title)
            path = Path(ImageFolder.ALBUM.path) / f"{album_id}.png"
            card.setCover(str(path))
            card.clicked.connect(lambda: self.albumClicked.emit(album_id))
            return True
    
    def createPortraitAlbumCard(self, album):
        album_id = album.get("browseId", None)
        if album_id is None:
            logger.warning(f"Album id is None: {album}")
            return None
        card = PortraitAlbumCard()
        card.setObjectName(f"{album_id}_card")
        if self.setPortraitAlbumCardInfo(card, album):
            return card
            
    def createArtistCard(self, artist):
        artist_id = artist.get("browseId", None)
        if artist_id is None:
            logger.warning(f"Artist id is None: {artist}")
            return None
        thumbnails = artist.get("thumbnails", None)
        card = ArtistCard()
        card.clicked.connect(lambda: self.artistClicked.emit(artist_id))
        path = Path(ImageFolder.ARTIST.path) / f"{artist_id}.png"
        if not path.exists():
            if thumbnails:
                self.thumbnails_downloader.download_thumbnail(thumbnails[-1].get("url", None), f"{artist_id}.png", ImageFolder.ARTIST.path, artist_id)
            else:
                logger.warning(f"No Thumbnail found for the: {artist_id}")
        else:
            logger.info(f"Thumbnail already exists in cache for: {artist_id}")
        if card.setCardInfo(artist):
            self.artist_count += 1
            return card
        return None

    def count(self)-> dict:
        """return no of card in the widget

        Returns:
            int: integer
        """
        cnt = {"songs": self.song_count - 1} #because value of song count starts with 0
        if hasattr(self, "artist_count"):
            cnt["artists"] = self.artist_count - 1 #because value of artist count starts with 0 in artistview(child class)
        return cnt
    
    def count_widget_type(self, widget_type):
        count = 0
        for i in range(self.scrollContainer_layout.count()):
            widget = self.scrollContainer_layout.itemAt(i).widget()
            if isinstance(widget, widget_type):
                count += 1
        return count
        
    def update_view_card(self):
        self.setCardTitle(self.title)
        if self.description and len(self.description) > 150:
            self.description = self.description[:145] + "..."
            
        self.setCardBody(self.description)
        print(self.thumbnail)
        self.setCardImage(str(self.thumbnail))
        
        
    def get_tracks(self):
        return self.tracks


class ViewBaseSkeleton(VerticalScrollWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('ViewBaseSkeleton')
        
        self.ui_elements = list()
        
        self.initUi()
        self.setContentsMargins(0, 0, 0, 0)
        self.setContentSpacing(0)
        
        self.setCursor(Qt.CursorShape.WaitCursor)

    def initUi(self):
        self.container = VerticalFrame(self)
        self.container.setFixedHeight(500)
        self.infoCard = WideCardSkeleton(self.container)
        self.infoCard.show()
        self.infoCard.setFixedSize(547, 222)
        self.ui_elements.append(self.infoCard)
        self.container.addWidget(self.infoCard, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.addWidget(self.container, alignment=Qt.AlignmentFlag.AlignTop)
        for _ in range(3):
            card = LandscapeAudioSkeleton()
            if card:
                self.ui_elements.append(card)
                card.setFixedHeight(90)
                self.addWidget(card, alignment=Qt.AlignmentFlag.AlignTop)
                
    def start_animation(self):
        # Synchronize animation start using a QTimer
        QTimer.singleShot(100, self._start_all_Animations)
        
    def _start_all_Animations(self):
        for element in self.ui_elements:
            element.start_animation()
            
    def stop_animation(self):
        for element in self.ui_elements:
            element.stop_animation()
        