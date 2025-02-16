from qfluentwidgets import ImageLabel, BodyLabel, TitleLabel
from qfluentwidgets import setCustomStyleSheet, CardWidget, AvatarWidget

import sys
sys.path.append('Musify')
sys.path.append('src')
# print(sys.path)
from src.utility.enums import PlaceHolder

from src.common.myLabel import ClickableBodyLabel, MyTitleLabel
from src.common.myFrame import HorizontalFrame, VerticalFrame

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QPushButton, QSizePolicy, QLabel
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QColor, QFontMetrics
from PySide6.QtWidgets import QGraphicsDropShadowEffect

from pathlib import Path


class StatsCard(CardWidget):
    def __init__(self, title: str, runs: int, cover_path: str = None, is_artist: bool = False, parent=None):
        super().__init__(parent)
        self.id = None
        self.title = title
        self.cover_path = cover_path
        self.runs = runs
        self.isArtistType = is_artist
        self.strRuns = f"{runs} play"
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.horizontalLayout = QHBoxLayout(self)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        # self.horizontalLayout.setContentsMargins(9, 0, 9, 0)
        self.setupUi()
        self.adjustSize()
        
    def setupUi(self):
        if not self.objectName():
            self.setObjectName(u"StatsCard")
        self.resize(744, 82)
        
        
        if self.isArtistType:
            self.coverLabel = AvatarWidget(self.cover_path, self)
            self.coverLabel.setRadius(32)
        else:
            self.coverLabel = ImageLabel(self.cover_path, self)
            self.coverLabel.setBorderRadius(4, 4, 4, 4)
            self.coverLabel.setStyleSheet("background: gray; border-radius: 4px;")
        self.coverLabel.setObjectName(u"coverLabel")
        self.coverLabel.setFixedSize(QSize(64, 64))

        self.infoContainer = VerticalFrame(self)
        self.infoContainer.setObjectName(u"infoContainer")
        self.infoContainer.setMaximumHeight(64)
        self.infoContainer.setFrameShadow(QFrame.Shadow.Raised)
        self.titleLabel = MyTitleLabel(self.title, is_underline= False, parent = self.infoContainer)
        self.titleLabel.setFont(QFont("Segoe UI", 16))
        self.titleLabel.setObjectName(u"titleLabel")
        
        self.infoContainer.addWidget(self.titleLabel)
        # self.infoContainer.addWidget(self.bodyLabel)

        self.runsLabel = BodyLabel(self.strRuns, self)
        self.runsLabel.setObjectName(u"runsLabel")

        self.horizontalLayout.addWidget(self.coverLabel)
        self.horizontalLayout.addWidget(self.infoContainer, stretch=1)
        self.horizontalLayout.addWidget(self.runsLabel)

        
    def shadowEffect(self):
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(15)  # How blurry the self.shadow should be
        self.shadow.setXOffset(2)      # Horizontal offset
        self.shadow.setYOffset(2)      # Vertical offset
        self.shadow.setColor(QColor(0, 0, 0, 160))  # self.Shadow color with alpha
        self.setGraphicsEffect(self.shadow)
    
    def set_id(self, id_):
        self.id = id_
        
    def get_id(self):
        return self.id
    
    def setRuns(self, runs: int):
        self.runs = runs
        self.strRuns = f"{runs} play"
        self.runsLabel.setText(self.strRuns)
        
    def getRuns(self):
        return self.runs

    
    
class ArtistStatsCard(StatsCard):
    def __init__(self, title: str, runs: int, cover_path: str = None, parent=None):
        if cover_path is None or not Path(cover_path).exists():
            cover_path = PlaceHolder.ARTIST.path
        super().__init__(title, runs, cover_path, True, parent)
        
        
class AudioStatsCard(StatsCard):
    def __init__(self, title: str, runs: int, cover_path: str = None, parent=None):
        if cover_path is None or not Path(cover_path).exists():
            cover_path = PlaceHolder.SONG.path
        super().__init__(title, runs, cover_path, False, parent)
        
class AlbumStatsCard(StatsCard):
    def __init__(self, title: str, runs: int, cover_path: str = None, parent=None):
        if cover_path is None or not Path(cover_path).exists():
            cover_path = PlaceHolder.ALBUM.path
        super().__init__(title, runs, cover_path, False, parent)
    
class PlaylistStatsCard(StatsCard):
    def __init__(self, title: str, runs: int, cover_path: str = None, parent=None):
        if cover_path is None or not Path(cover_path).exists():
            cover_path = PlaceHolder.PLAYLIST.path
        super().__init__(title, runs, cover_path, False, parent)

    
if(__name__ == '__main__'):
    app = QApplication(sys.argv)
    window = AlbumStatsCard("Title es bid borg", 10)
    
    window.resize(500, 200)
    window.show()
    
    app.exec()