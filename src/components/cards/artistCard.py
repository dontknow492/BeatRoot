from qfluentwidgets import ImageLabel, BodyLabel, TitleLabel, TransparentToolButton, TransparentDropDownToolButton
from qfluentwidgets import FluentIcon, setCustomStyleSheet, CardWidget, ElevatedCardWidget, SimpleCardWidget
from qfluentwidgets import AvatarWidget, FluentIcon, InfoBadge, InfoBadgePosition


import sys

from src.utility.enums import PlaceHolder
from src.utility.enums import ImageFolder
from pathlib import Path

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QSize, Signal, QObject
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect


class ArtistCard(CardWidget):
    # clicked = Signal()
    cardClicked = Signal(dict)
    def __init__(self, cover_path: str= None, name: str = "Name", artist_id: str = "Unknown", parent = None):
        super().__init__(parent=parent)
        
        self.artistID = artist_id
        self.name = name
        if cover_path and Path(cover_path).exists():
            self.cover_path = cover_path
            
        else:
            self.cover_path = PlaceHolder.ARTIST.path
            # print(self.cover_path.absolutePath())
        self.setCursor(Qt.PointingHandCursor)
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setSpacing(10)
        self.setFixedSize(QSize(170,  230))
        self.setupUi()
        self.overlayTag()

    def setupUi(self):
        self.coverLabel = AvatarWidget(self.cover_path,self)
        self.coverLabel.setRadius(75)
        
        self.nameLabel = TitleLabel(self.name, self)
        self.nameLabel.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.nameLabel.setAlignment(Qt.AlignCenter)
        self.nameLabel.setWordWrap(True)
        
        self.mainLayout.addWidget(self.coverLabel, alignment=Qt.AlignHCenter | Qt.AlignTop)
        self.mainLayout.addWidget(self.nameLabel, alignment=Qt.AlignHCenter | Qt.AlignTop)
        
    def overlayTag(self):
        self.artistTag = InfoBadge.success("Artist", self.coverLabel)
        InfoBadge.setCustomBackgroundColor(self.artistTag, QColor("#3e90e8"), QColor("#3e727f"))
        self.artistTag.setFixedSize(QSize(45, 20))
        self.artistTag.setAlignment(Qt.AlignCenter)
        # self.artistTag.move(120, 10)
    
    
    def setCardInfo(self, artist_data: dict):
        title = artist_data.get("title", None)
        if title is None:
            title = artist_data.get("artist", "Unknown")
        browse_id = artist_data.get("browseId", None)
        if browse_id is None:
            # logger.error(f"browse_id not found for artist: {title}")
            return None
        path = Path(ImageFolder.ARTIST.path, f"{browse_id}.png")
        if path.exists():
            self.setCover(str(path))
        subscribers = artist_data.get("subscribers", None)
        # artists = album.get("artists", [])
        # self.setObjectName(f"{browse_id}_card") done in set artistid function
        self.setArtistName(title)
        self.setArtistId(browse_id)
        self.setSubscribers(subscribers)
        
        emit_data = {
            "name": title,
            "id": browse_id
        }
        # self.clicked.connect(lambda: self.cardClicked.emit(emit_data))
        return True
    
    
    def setArtistId(self, artist_id):
        self.artistID = artist_id
        self.setObjectName(f"{artist_id}_card")
        
    def getArtistID(self):
        return self.artistID
    
    def setTitle(self, title):
        self.setArtistName(title)
    
    def setArtistName(self, name):
        self.name = name
        self.nameLabel.setText(name)
        
    def getArtistName(self):
        return self.name
    
    def setSubscribers(self, subscribers):
        self.subscribers = subscribers
    
    def setCover(self, cover_path):
        if Path(cover_path).exists() and self.cover_path != cover_path:
            self.cover_path = cover_path
            self.coverLabel.clear()
            self.coverLabel.setImage(cover_path)
            self.coverLabel.setRadius(75)
            
    
    
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()
        return super().mousePressEvent(e)
        
        

        
if(__name__ == '__main__'):
    app = QApplication(sys.argv)
    frame = QFrame()
    w = 0 
    for x in range(3):
        card = ArtistCard(parent = frame)
        card.setObjectName(f"card_{x}")
        card.move(w, 0)
        w += 170
    frame.show()
    print(frame.findChild(QObject, "card_0"))
    app.exec()