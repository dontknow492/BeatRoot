import sys

from qfluentwidgets import ElevatedCardWidget, PrimaryToolButton, setTheme, Theme
from qfluentwidgets import FluentIcon, setCustomStyleSheet
from qfluentwidgets import ImageLabel, BodyLabel, TitleLabel



import time


from src.common.myLabel import ClickableBodyLabel
from src.utility.enums import PlaceHolder, ImageFolder
# print(sys.path)

from PySide6.QtWidgets import QFrame, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect

from pathlib import Path

class PortraitCardBase(ElevatedCardWidget):
    addButtonClicked = Signal(dict)
    playButtonClicked = Signal()
    longPressed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.cover_path = PlaceHolder.ALBUM.path
        self.title = "Title"
        self.info = "Info"
        
        self.maxTitleLength = 30
        self.maxInfoLength = 42
        
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(11, 11, 10, 0)
        self.setupUi()
        # self.setFixedSize(173, 270)
        self.setMinimumSize(173, 280)
        self.setMaximumWidth(173)
        
        # self.shadowEffect()
        self.overlayOptions()
        self.setCursor(Qt.PointingHandCursor)
        self.setupQss()
        
        self.signalHandler()
        
    def setupUi(self):
        self.coverLabel = ImageLabel(self.cover_path, self)
        self.coverLabel.setScaledContents(True)
        self.coverLabel.setFixedSize(QSize(150, 150))
        self.coverLabel.setBorderRadius(15, 15, 15, 15)
        self.coverLabel.setStyleSheet("background: gray; border-radius: 15px;")
        # self.coverLabel.setAlignment(Qt.AlignTop | Qt.AlignVCenter)
        
        self.titleContainer = QFrame(self)
        # self.titleContainer.setStyleSheet("background: red;")
        self.titleContainer.setFixedWidth(160)
        self.titleContainer.setFixedHeight(120)
        self.titleContainer_layout = QVBoxLayout(self.titleContainer)
        # self.titleContainer_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.titleContainer_layout.setSpacing(0)
        self.titleLabel = TitleLabel(self.title, self.titleContainer)
        self.titleLabel.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.titleLabel.setWordWrap(True)
        # self.titleLabel.setMaximumHeight(55)
        self.titleLabel.setAlignment(Qt.AlignTop)
        
        
        self.infoLabel = BodyLabel(self.info, self.titleContainer)
        self.infoLabel.setWordWrap(True)
        # self.infoLabel.setMaximumHeight(40)
        self.infoLabel.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        
        self.titleContainer_layout.addWidget(self.titleLabel)
        self.titleContainer_layout.addWidget(self.infoLabel)
        self.titleContainer_layout.addItem(spacer)
        # self.titleContainer.setStyleSheet("background-color: green;")
        
        
        self.vBoxLayout.addWidget(self.coverLabel)
        self.vBoxLayout.addWidget(self.titleContainer)
        
    def shadowEffect(self):
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(15)  # How blurry the self.shadow should be
        self.shadow.setXOffset(2)      # Horizontal offset
        self.shadow.setYOffset(2)      # Vertical offset
        self.shadow.setColor(QColor(0, 0, 0, 160))  # self.Shadow color with alpha
        # self.setGraphicsEffect(self.shadow)
        self.coverLabel.setGraphicsEffect(self.shadow)
    
    def overlayOptions(self):
        self.playButton = PrimaryToolButton(FluentIcon.PLAY, self)
        self.playButton.setIconSize(QSize(12, 12))
        self.playButton.setFixedSize(32, 32)
        self.playButton.move(125, 110)
        self.playButton.setToolTip("Play")
        qss = """
            PrimaryToolButton {
                border-radius: 16px;
            }
        """
        setCustomStyleSheet(self.playButton, qss, qss)
        
        self.addButton = PrimaryToolButton(FluentIcon.ADD, self)
        self.addButton.setIconSize(QSize(12, 12))
        self.addButton.setFixedSize(32, 32)
        self.addButton.move(125, 147)
        self.addButton.setToolTip("Add to playlist")
        self.addButton
        
        setCustomStyleSheet(self.addButton, qss, qss)
        
    def setupQss(self):
        qss = "BodyLabel{color: #757575;}"
        qss_d = "BodyLabel{color: #B0B0B0;}"
        setCustomStyleSheet(self.infoLabel, qss, qss_d)
        
    def setTitle(self, title):
        # if len(title) > self.maxTitleLength:
        # title = title[:self.maxTitleLength] + "..."
        self.titleLabel.setText(title)
        # title_size = self.titleLabel.sizeHint()
        # body_size = self.infoLabel.sizeHint()
        # if (title_size.height() + body_size.height()) > 100:
        #     self.titleLabel.setFixedHeight(55)
        #     self.infoLabel.setMaximumHeight(40)
        
    def setInfo(self, info):
        if isinstance(info, list):
            if isinstance(info[0], dict):
                info = ", ".join(info.get("name", "Unknown") for info in info)
            else:
                info = ", ".join(info)
        if isinstance(info, dict):
            info = info.get("name", "Unknown")
        if info is None:
            info = ""
        if len(info) > self.maxInfoLength:
            info = info[:self.maxInfoLength] + "..."
        self.infoLabel.setText(info)
        # text = self.elided_text(self.infoLabel)
        # print(text)
        # self.infoLabel.setText(text)
        # if (title_size.height() + body_size.height()) > 100:
        #     self.titleLabel.setFixedHeight(55)
        #     self.infoLabel.setMaximumHeight(40)
        
    def setCover(self, cover_path: str):
        if cover_path and Path(cover_path).exists() and cover_path != self.cover_path:
            self.coverLabel.setImage(cover_path)
            self.cover_path = cover_path
            self.coverLabel.setFixedSize(150, 150)
        
    def getTitle(self):
        return self.titleLabel.text()
    
    def getInfo(self):
        return self.infoLabel.text()
    
    def getCover(self):
        return self.coverLabel.image
    
    def getCoverPath(self):
        return self.cover_path
    
    def signalHandler(self):
        self.addButton.clicked.connect(self.addButtonClicked.emit)
        self.playButton.clicked.connect(self.playButtonClicked.emit)
        
    def mousePressEvent(self, e):
        self.press_start_time = time.time()
        self.blockSignals(True)
        super().mouseReleaseEvent(e)
        
    def mouseReleaseEvent(self, e):
        print('release')
        self.blockSignals(False)
        if time.time() - self.press_start_time < 0.5:
            self.clicked.emit()
        else:
            self.longPressed.emit()
            
        
        
class PlaylistCard(PortraitCardBase):
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self.cover_path = PlaceHolder.PLAYLIST.path
        self.setCover(self.cover_path)
        
        # self.coverLabel.setStyleSheet("background: transparent;")
        
    def setCardInfo(self, playlist_data: dict):
        playlist_id = playlist_data.get("playlistId", None)
        if playlist_id is None:
            return None
        title = playlist_data.get("title", "Unknown")
        description = playlist_data.get("description", None)
        if description is None:
            description = playlist_data.get("author", "")
        self.setObjectName(f"{playlist_id}_card")
        self.setTitle(title)
        self.setPlaylistId(playlist_id)
        self.setInfo(description)
        path = Path(ImageFolder.PLAYLIST.path, f"{playlist_id}.png")
        if path.exists():
            self.setCover(str(path))
            
        emit_data = {
            'title': title,
            'description': description,
            'id': playlist_id,
            'cover_art': str(path)
        }
        self.addButton.clicked.connect(lambda: self.addButtonClicked.emit(emit_data))
        return True
        
    def setPlaylistId(self, id_):
        self.playListId = id_
        
    def getPlaylistId(self):
        return self.playListId
    
    def signalHandler(self):
        self.addButton.clicked.connect(self.addButtonClicked.emit)
        self.playButton.clicked.connect(self.playButtonClicked.emit)
        
    
        # return super().mouseReleaseEvent(e)
        
class PortraitAudioCard(PlaylistCard):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.cover_path = PlaceHolder.SONG.path
        self.albumId = None
        self.setCover(self.cover_path)
    
    
    def setCardInfo(self, audio_data: dict):
        title = audio_data.get("title", None)
        video_id = audio_data.get("videoId", None)
        if video_id is None:
            return None
        artists = audio_data.get("artists", [])
        album = audio_data.get("album", {})
        self.setObjectName(f"{video_id}_card")
        self.setTitle(title)
        self.setAudioId(video_id)
        self.setArtistsInfo(artists)
        self.setAlbumInfo(album)
        
        path = Path(ImageFolder.SONG.path, f"{video_id}.png")
        if path.exists():
            self.setCover(str(path))
            
        self.addButton.clicked.connect(lambda: self.addButtonClicked.emit(audio_data))
        
        return True
    
    
    def setAlbumInfo(self, album: dict):
        self.albumId = album.get("browseId", None)
        
    # @overload
    def setArtistsInfo(self, artists: list):
        """
        Sets artist information by extracting and formatting their names.
        
        Args:
            artists (list): A list of dictionaries, where each dictionary 
                            represents an artist with a 'name' key.
        """
        if not artists:  # Handle None or empty list
            self.artists = []
            self.setInfo("Unknown Artist")
            return
        
        self.artists = artists
        # Extract artist names, using "Unknown" as a default for missing names
        names = [artist.get("name", "Unknown") for artist in artists]
        formatted_names = ", ".join(names)
        self.setInfo(formatted_names)
        
    def tempMedia(self, range_):
        for x in range(range_):
            self.infoContainer_layout.addWidget(ClickableBodyLabel(f"Artist_{x},"))
    
    def setAudioId(self, id_):
        self.audioId = id_
        
    def getAudioId(self):
        return self.audioId
    
        
class PortraitAlbumCard(PortraitCardBase):
    playButtonClicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setCursor(Qt.PointingHandCursor)
        self.cover_path = r"src\resources\images\image_2.png"
        self.setMouseTracking(True)
        self.signalHandler()
        self.infoLabel.hide()
        
    def setCardInfo(self, album_data: dict):
        title = album_data.get("title", None)
        browse_id = album_data.get("browseId", None)
        if browse_id is None:
            # logger.error(f"browse_id not found for album: {title}")
            return None
        year = album_data.get("year", None)
        path = Path(ImageFolder.ALBUM.path, f"{browse_id}.png")
        artists = album_data.get("artists", [])
        if path.exists():
            self.setCover(str(path))
        self.setObjectName(f"{browse_id}_card")
        self.setTitle(title)
        self.setAlbumId(browse_id)
        self.setYear(year)
        self.setInfo(artists)
        
        emit_data = {
            'name': title,
            'id': browse_id
        }
        self.addButton.clicked.connect(lambda: self.addButtonClicked.emit(emit_data))
        return True
    
        
    def setAlbumId(self, id_):
        self.albumId = id_
        
    def getAlbumId(self):
        return self.albumId
        
    def setYear(self, year):
        if year is None:
            year = "Unknown"
        self.year = year
        self.titleLabel.setText(f"{self.titleLabel.text()} ({year})")
    
if(__name__ == "__main__"):
    setTheme(Theme.DARK)
    app = QApplication(sys.argv)
    title = "This is a title."
    info = "hello"
    window = PlaylistCard()
    data = {
        "title": title,
        "info": info,
        "cover": r"src\resources\images\image_2.png",
        "playlistId": "XXXX"
    }
    window.setCardInfo(data)
    # window.cardClicked.connect(print)
    
    window.show()
    # window.elided_text(window.titleLabel)
    print(window.size())
    app.exec()
    