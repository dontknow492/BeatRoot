from qfluentwidgets import ImageLabel, BodyLabel, TitleLabel, TransparentToolButton, ElevatedCardWidget
from qfluentwidgets import FluentIcon, setCustomStyleSheet, setThemeColor, setTheme, Theme, ThemeColor

import sys


from src.common.myFrame import VerticalFrame, HorizontalFrame
from src.utility.enums import PlaceHolder
# print(sys.path)

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect

class GroupCardBase(ElevatedCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(6)
        self.vBoxLayout.setContentsMargins(0, 8, 0, 0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setupUi()
        self.setFixedSize(166, 240)
        self.setCursor(Qt.PointingHandCursor)
        self.setupQss()
        self.shadowEffect()
        
    def setupUi(self):
        
        self.coverLabel = ImageLabel(PlaceHolder.PLAYLIST.path, self)
        self.coverLabel.setScaledContents(True)
        self.coverLabel.setFixedSize(QSize(150, 150))
        self.coverLabel.setBorderRadius(8, 8, 8, 8)
        # self.coverLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        
        
        self.titleLabel = TitleLabel("Title is big ", self)
        self.titleLabel.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        
        self.pathLabel = BodyLabel("Path", self)
        self.pathLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.pathLabel.setWordWrap(True)
        
        spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        
        self.vBoxLayout.addWidget(self.coverLabel, alignment=Qt.AlignmentFlag.AlignAbsolute)
        self.vBoxLayout.addWidget(self.titleLabel, alignment= Qt.AlignmentFlag.AlignTop)
        self.vBoxLayout.addWidget(self.pathLabel, alignment=Qt.AlignmentFlag.AlignTop)
        self.vBoxLayout.addItem(spacer)
        
    def shadowEffect(self):
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(15)  # How blurry the self.shadow should be
        self.shadow.setXOffset(2)      # Horizontal offset
        self.shadow.setYOffset(2)      # Vertical offset
        self.shadow.setColor(QColor(0, 0, 0, 160))  # self.Shadow color with alpha
        # self.setGraphicsEffect(self.shadow)
        # self.coverLabel.setGraphicsEffect(self.shadow)
        # self.titleLabel.setGraphicsEffect(self.shadow)
        self.setGraphicsEffect(self.shadow)
        
    def setupQss(self):
        qss = "BodyLabel{color: #4DA1A9;}"
        qss_d = "BodyLabel{color: #4DA1A9;}"
        setCustomStyleSheet(self.pathLabel, qss, qss)
    

class GroupCard(GroupCardBase):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setCursor(Qt.PointingHandCursor)
        self.coverPath = r"src\resources\images\image_2.png"
        self.setMouseTracking(True)
        
    def setTitle(self, title):
        self.titleLabel.setText(title)
        
    def setPath(self, path):
        self.pathLabel.setText(path)
        
    def setCardId(self, card_id):
        self.cardId = card_id
        
    def getCardId(self):
        return self.cardId
        
    def setCover(self, cover_path):
        self.coverLabel.setImage(cover_path)
        self.coverLabel.setFixedSize(QSize(150, 150))
        
    def getTitle(self):
        return self.titleLabel.text()
    
    def getPath(self):
        return self.pathLabel.text()
    
    def getCover(self):
        return self.coverLabel.image
    
    def getCoverPath(self):
        return self.coverPath
    
    
    
if(__name__ == "__main__"):
    app = QApplication(sys.argv)
    window = GroupCardBase()
    # window.resize(300, 96)
    window.show()
    # setThemeColor(QColor(34, 34, 34))
    app.exec()