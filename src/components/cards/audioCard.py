from qfluentwidgets import ImageLabel, BodyLabel, TitleLabel, TransparentToolButton, TransparentDropDownToolButton
from qfluentwidgets import FluentIcon, setCustomStyleSheet, setThemeColor, setTheme, Theme, ThemeColor
from qfluentwidgets import RoundMenu, Action

import sys

from src.utility.enums import PlaceHolder
from pathlib import Path

from loguru import logger
from enum import Enum

from src.common.myLabel import MyTitleLabel, MyBodyLabel, HoverOverlayImageLabel, ClickableTitleLabel, ClickableBodyLabel
from src.common.myFrame import VerticalFrame, HorizontalFrame, FlowFrame
from src.utility.enums import ImageFolder


from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy, QLabel
from PySide6.QtCore import Qt, QSize, Signal, QMimeData
from PySide6.QtGui import QFont, QColor, QDrag, QPixmap, QMovie
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from pathlib import Path



class AudioCardBase(HorizontalFrame):
    class AudioState(Enum):
        PLAYING = 1
        PAUSED = 2
        LOADING = 3
        
        @property
        def icon(self):
            if self == AudioCard.AudioState.PLAYING:
                return FluentIcon.PAUSE_BOLD
            elif self == AudioCard.AudioState.PAUSED:
                return FluentIcon.PLAY_SOLID
    clicked = Signal()
    albumClicked = Signal(str)
    artistClicked = Signal(str)
    cardClicked = Signal(dict)
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayoutMargins(0, 0, 0, 0)
        self.setContextMenuPolicy(Qt.CustomContextMenu) 
        self.setMaximumHeight(76)
        
        self.cover_path = PlaceHolder.SONG.path
        self.state = self.AudioState.PAUSED
        self.selected:bool = False
        
        self.setupUi()
        # self.shadowEffect()
        self.selectedQss = "AudioCardBase{background-color: #e0f7f7}"
        self.normalQss = "AudioCardBase{background-color: transparent;} AudioCardBase::hover{background-color: rgba(68, 68, 68,0.1);}"
        self.setStyleSheet(self.normalQss)
        
        
        self.loading_movie = QMovie(r"D:\Downloads\Images\loading-loading-forever.gif")
        self.loading_movie.setScaledSize(self.loading_movie.scaledSize().scaled(25, 25, Qt.KeepAspectRatio)) 
        self.loadingLabel.setMovie(self.loading_movie)
        self.loadingLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loadingLabel.hide()
        
        self.dragButton.released.connect(self.dragTimeEnd)
        self.dragButton.pressed.connect(self.dragTime)
        
        
        
    def setupUi(self):
        self.init_thumbnail_container()
        self.init_title_author_container()
        self.init_end_container()
        
        self.addWidget(self.thumbnail_container, stretch= 0)
        self.addWidget(self.title_author_container, stretch= 4)
        self.addWidget(self.end_container, stretch= 2)
        
    def init_thumbnail_container(self):
        self.thumbnail_container = HorizontalFrame(self)
        self.thumbnail_container.setContentsMargins(0, 0, 0, 0)
        self.thumbnail_container.setLayoutMargins(0, 0, 0, 0)
        self.dragButton = TransparentToolButton(FluentIcon.MENU, self.thumbnail_container)
        self.dragButton.setFixedSize(QSize(32, 32))
        self.dragButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        
        self.countLabel = BodyLabel("1", self.thumbnail_container)
        
        # self.countLabel.setMaximumWidth(20)
        self.loadingLabel = QLabel(self.thumbnail_container)
        self.loadingLabel.setStyleSheet("background-color: gray; border-radius: 4px;")
        self.coverLabel = HoverOverlayImageLabel(image = self.cover_path, icon = FluentIcon.PLAY_SOLID, parent=self.thumbnail_container)
        self.coverLabel.setStyleSheet("background: gray; border-radius: 4px;")
        self.coverLabel.setScaledContents(True)
        self.coverLabel.setFixedSize(QSize(64, 64))
        self.coverLabel.setBorderRadius(4, 4, 4, 4)
        
        self.thumbnail_container.addWidget(self.dragButton)
        self.thumbnail_container.addWidget(self.countLabel)
        self.thumbnail_container.addWidget(self.coverLabel)
        self.thumbnail_container.addWidget(self.loadingLabel)
        
    def init_title_author_container(self):
        self.title_author_container = VerticalFrame(self)
        self.title_author_container.setLayoutMargins(0, 0, 0, 0)
        self.title_author_container.setContentsMargins(0, 0, 0, 0)
        self.title_author_container.setContentSpacing(0)
        
        self.titleLabel = MyTitleLabel("Title", self.title_author_container, is_underline= False)
        self.titleLabel.setMaximumHeight(30)
        self.titleLabel.setWordWrap(True)
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.titleLabel.setFont(QFont("Segoe UI", 16))
        self.authorContainer = FlowFrame(self.title_author_container)
        self.authorContainer.setContentsMargins(0, 0, 0, 0)
        self.authorContainer.setLayoutMargins(0, 0, 0, 0)
        self.authorContainer.setHorizantalSpacing(4)
        self.authorContainer.setVerticalSpacing(0)
        self.title_author_container.addWidget(self.titleLabel)
        self.title_author_container.addWidget(self.authorContainer, alignment= Qt.AlignmentFlag.AlignTop)
        
    def init_end_container(self):
        self.end_container =HorizontalFrame(self)
        self.end_container.setContentsMargins(0, 0, 0, 0)
        self.end_container.setLayoutMargins(0, 0, 0, 0)
        
        self.albumLabel = ClickableTitleLabel("Album", parent = self.end_container)
        # self.albumLabel.setStyleSheet('background: red;')
        self.albumLabel.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.albumLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.albumLabel.setWordWrap(True)
        self.albumLabel.setFont(QFont("Segoe UI", 16))
        # self.albumLabel.setContentsMargins(0, 0, 0, 0)
        
        self.durationLabel = BodyLabel("Duration", self.end_container)
        # self.durationLabel.setMaximumWidth(60)
        self.durationLabel.setAlignment(Qt.AlignRight | Qt.AlignCenter)
        # self.durationLabel.setContentsMargins(0, 0, 0, 10)
        self.optionButton = TransparentDropDownToolButton(FluentIcon.MORE, self.end_container)
        
        self.end_container.addWidget(self.albumLabel, alignment=Qt.AlignmentFlag.AlignTop)
        self.end_container.addWidget(self.durationLabel)
        self.end_container.addWidget(self.optionButton)
        
    def shadowEffect(self):
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(15)  # How blurry the self.shadow should be
        self.shadow.setXOffset(2)      # Horizontal offset
        self.shadow.setYOffset(2)      # Vertical offset
        self.shadow.setColor(QColor(0, 0, 0, 160))  # self.Shadow color with alpha
        # self.setGraphicsEffect(self.shadow)
        self.coverLabel.setGraphicsEffect(self.shadow)
        # self.setStyleSheet("background-color: white;")
        
    def revertStyle(self):
        pass
    
    def dragTime(self):
        self.dragButton.setCursor(Qt.CursorShape.SizeAllCursor)
        # self.setStyleSheet("background-color: #e0f7f7")
        drag = QDrag(self)
        mime = QMimeData()
        drag.setMimeData(mime)
        
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.transparent)
        self.render(pixmap)
        drag.setPixmap(pixmap)

        drag.exec(Qt.MoveAction)
        
        drag.exec(Qt.CopyAction | Qt.MoveAction)
        
    def dragTimeEnd(self):
        self.dragButton.setCursor(Qt.OpenHandCursor)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.state == self.AudioState.LOADING:
                return  # Prevent further action when loading
            else:
                self.toggle_state()
            self.clicked.emit()
        elif event.button() == Qt.RightButton:
            print("Right button clicked")
            menu = self.optionButton.menu()
            if menu:
                menu.popup(self.mapToGlobal(event.position().toPoint()))  # Correct way to show the menu
        else:
            super().mousePressEvent(event)  # Pass other events to parent class

    def setCoverLoading(self, state: bool):
        size = self.coverLabel.size()
        self.loadingLabel.setFixedSize(size)
        
        if state:
            self.loading_movie.start()
            self.coverLabel.hide()
            self.loadingLabel.show()
        else:
            self.loadingLabel.hide()
            self.coverLabel.show()
            self.loading_movie.stop()
            
    def enterEvent(self, event):
        self.coverLabel.enterEvent(event)
        return super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.coverLabel.leaveEvent(event)
        return super().leaveEvent(event)
            
    def set_state(self, state: AudioState):
        self.coverLabel.set_overlay_icon(state.icon)
        self.state = state
        
        
    def toggle_state(self):
        if self.state == self.AudioState.PLAYING:
            self.set_state(self.AudioState.PAUSED)
        elif self.state == self.AudioState.PAUSED:
            self.set_state(self.AudioState.PLAYING)
        
    def set_selected(self, selected: bool):
        self.selected = selected
        if selected:
            self.setStyleSheet(self.selectedQss)
        else:
            self.setStyleSheet(self.normalQss)
            
    def is_selected(self):
        return self.selected


class AudioCard(AudioCardBase):
    def __init__(self, is_dragable: bool= False, parent=None):
        super().__init__(parent=parent)
        self.setCursor(Qt.PointingHandCursor)
        self.isdragable = is_dragable
        self.thumbnailPath = r"src\resources\images\image_2.png"
        if not is_dragable:
            self.dragButton.hide()
            self.dragButton.setEnabled(False)
        # self.dragButton.setCursor(Qt.OpenHandCursor)

    def setTitle(self, title):
        if isinstance(title, str):
            self.titleLabel.setText(title)
    
    def setArtist(self, artist):
        self.artist = artist
        if isinstance(artist, list):
            for index, x in enumerate(artist):
                if isinstance(x, dict):
                    label:QLabel = self.create_artist_label(x)
                    self.authorContainer.addWidget(label)
                    if index == len(artist)-1:
                        label.setText(label.text().removesuffix(","))
        else: 
            if (isinstance(artist, str) and artist == "") or artist is None:
                artist = "Unknown"
            label = BodyLabel(artist, self.authorContainer)
            self.authorContainer.addWidget(label)
            
    def create_artist_label(self, artist):
        artist_name = artist.get("name", "Unknown")
        artist_id = artist.get("id", None)
        label = ClickableBodyLabel(f"{artist_name},", False, self.authorContainer)
        label.id = artist_id
        if artist_id is not None:
            label.clicked.connect(lambda: self.artistClicked.emit(label.id))
        return label
        
    def setAlbum(self, album):
        if isinstance(album, dict):
            name = album.get("name", "Unknown")
            self.albumId = album.get("id", None)
            self.albumLabel.clicked.connect(lambda: self.albumClicked.emit(self.albumId))
            album = name
            if album is None or album == "":
                album = "Unknown"
        elif isinstance(album, str):
            self.albumId = None
            if album == "":
                album = "Unknown"
            self.albumLabel.blockSignals(True)
        else:
            album = "Unknown"
            self.albumLabel.blockSignals(True)
        self.albumLabel.setText(album)
        
    def getAlbumId(self):
        if hasattr(self, "albumId"):
            return self.albumId
        
    def setAudioId(self, song_id: str | None):
        self.songId: str = song_id
        
    def getAudioId(self):
        if hasattr(self, "songId"):
            return self.songId
    
    def setMenu(self, menu: RoundMenu):
        self.optionButton.setMenu(menu)
    
    def setDuration(self, duration):
        if isinstance(duration, str):
            self.durationLabel.setText(duration)
        else:
            self.durationLabel.setText("00:00")
        
    def setCover(self, cover_path):
        if not Path(cover_path).exists():
            return
        self.coverLabel.clear()
        self.coverLabel.setImage(cover_path)
        self.coverLabel.setFixedSize(64, 64)
        
    def setCount(self, count):
        if isinstance(count, int):
            count = str(count)
        elif not isinstance(count, str):
            count = "1"
        self.countLabel.setText(count)
        
    def getCount(self)->int:
        return int(self.countLabel.text())
        
    def getTitle(self):
        return self.titleLabel.text()
    
    def getAuthor(self):
        return self.authorLabel.text()
    
    def getAlbum(self):
        return self.albumLabel.text()
    
    def getDuration(self):
        return self.durationLabel.text()
    
    def getCover(self):
        return self.coverLabel.image
    
    def getCoverPath(self):
        return self.thumbnailPath
        
    def setAttributes(self, **kwargs):
        """takes 5 argument title, author, album , duration, cover_path all string
        """
        if "title" in kwargs:
            self.titleLabel.setText(kwargs["title"])
        if "author" in kwargs:
            self.authorLabel.setText(kwargs["author"])
        if "album" in kwargs:
            self.albumLabel.setText(kwargs["album"])
        if "duration" in kwargs:
            self.durationLabel.setText(kwargs["duration"])
        if "cover_path" in kwargs:
            self.coverLabel.setImage(kwargs["cover_path"])
        
    def hideDuration(self, hide):
        if hide:
            self.durationLabel.hide()
        else:
            self.durationLabel.show()
            
    def showMenu(self):
        pass
        # self.optionButton.menu().show()
    
    def setCardInfo(self, audio_data: dict, is_single: bool = False):
        song_id = audio_data.get("videoId", None)
        if song_id is None:
            logger.warning(f"Song id is None: {audio_data}")
            return None
        self.setAudioId(song_id)
        self.setObjectName(f"{song_id}_card")
        title = audio_data.get("title", "Unknown")
        artists = audio_data.get("artists", "")
        duration = audio_data.get("duration", "Unknown")
        album = audio_data.get("album", "Unknown")
        if album == "Unknown" and is_single:
            album = "Single"
        if duration == "Unknown":
            duration = audio_data.get("length", "Unknown")
            if duration == "Unknown":
                self.hideDuration(True)
                
        self.setAudioId(song_id)
        # self.setSongId(songId)
        if album == "Unknown" and is_single:
            album = "Single"
        self.setTitle(title)
        self.setArtist(artists)
        self.setAlbum(album)
        self.setDuration(duration)
        
        path = Path(ImageFolder.SONG.path, f"{song_id}.png")
        if path.exists():
            self.setCover(str(path))
        self.card_data = audio_data
        # self.clicked.connect(lambda: self.cardClicked.emit(audio_data))
        return True
    
    def get_card_data(self):
        return self.card_data   

    def set_local(self, local: bool):
        self.is_local = local
        if local:
            self.albumClicked.disconnect()
            self.artistClicked.disconnect()
            
        

def create_audio_menu(card: AudioCard):
        menu = RoundMenu()
        # menu.setCursor(Qt.CursorShape.PointingHandCursor)
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
    
if(__name__ == '__main__'):
    app = QApplication(sys.argv)
    window =VerticalFrame()
    menu = RoundMenu()
    menu.addAction(Action("Add to playlist"))
    for _ in range(4):
        card = AudioCard(True)
        album = {
            "name": "this is gona be big bro",
            "id": "1234"
        }
        artist = [{
            "name": "Arijit",
            "id": "1234"
            },
            {
                "name": "Jubin",
                "id": "1234"
            }
        ]
        card.setAlbum(album)
        card.setArtist(artist)
        # card.setCoverLoading(True)
        window.addWidget(card)
        card.albumClicked.connect(lambda id_: print("album clicked: ", id_))
        card.artistClicked.connect(lambda id_: print("artist clicked: ", id_))
        create_audio_menu(card)
    # card.setCoverLoading(True)

    window.show()
    app.exec()