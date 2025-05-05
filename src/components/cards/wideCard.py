from qfluentwidgets import ImageLabel, BodyLabel, TitleLabel, TransparentToolButton, TransparentDropDownToolButton
from qfluentwidgets import FluentIcon, setCustomStyleSheet, setThemeColor, setTheme, Theme, ThemeColor
from qfluentwidgets import TogglePushButton, TransparentToolButton, PillPushButton, PrimaryPushButton, FlowLayout
from qfluentwidgets import FluentIcon

from pathlib import Path

import sys


# print(sys.path)
from src.utility.iconManager import ThemedIcon
from src.common.myLabel import MyBodyLabel, MyTitleLabel
from src.utility.enums import PlaceHolder
from src.common.myFrame import VerticalFrame, HorizontalFrame


from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QSize, Signal, QMimeData
from PySide6.QtGui import QFont, QColor, QDrag, QPixmap
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QGraphicsBlurEffect

class WideCard(HorizontalFrame):
    playClicked = Signal(bool)
    shuffleClicked = Signal(bool)
    likeClicked = Signal(bool)
    shareClicked = Signal()
    addClicked = Signal(bool)
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("WidePlaylistCard")
        
        self.is_playing = False
        self.is_liked = False
        self.is_added = False
        self.cover_path = PlaceHolder.SONG.path
        
        self.setContentSpacing(10)
        
        self.setupUi()
        
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        self.initCursor()
        self.initToolTips()
        self.signalHangler()
        
    def initCursor(self):
        self.playButton.setCursor(Qt.PointingHandCursor)
        self.shuffleButton.setCursor(Qt.PointingHandCursor)
        self.likeButton.setCursor(Qt.PointingHandCursor)
        self.shareButton.setCursor(Qt.PointingHandCursor)
        self.addToButton.setCursor(Qt.PointingHandCursor)
            
    def initToolTips(self):
        self.likeButton.setToolTip("Like")
        self.shareButton.setToolTip("Share")
        self.addToButton.setToolTip("Add To")
        
    def setupUi(self):
        self.coverLabel = ImageLabel(self.cover_path, self)
        self.coverLabel.setStyleSheet("background: gray; border-radius: 10px;")
        self.coverLabel.setBorderRadius(10, 10, 10, 10)
        self.coverLabel.setFixedSize(200, 200)
        self.coverLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.initInfo()
        
    def initInfo(self):
        self.infoContainer = VerticalFrame(self)
        self.infoContainer.setLayoutMargins(0, 0, 0, 0)
        self.infoContainer.setMaximumHeight(200)
        self.infoContainer.setObjectName(u"frame")
        self.infoContainer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.infoContainer.setFrameShadow(QFrame.Shadow.Raised)
        
        self.titleLabel = TitleLabel("HELLSEED: All Chapters", self.infoContainer)
        self.titleLabel.setObjectName(u"titleLabel")


        self.bodyLabel = BodyLabel("Based on hellseed stream release version 1.2.11 and patched by fitgirl.",self.infoContainer)
        self.bodyLabel.setObjectName(u"bodyLabel")
        self.bodyLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.bodyLabel.setWordWrap(True)


        self.toolContainer = HorizontalFrame(self.infoContainer)
        self.toolContainer.setObjectName(u"frame_2")
        # self.toolContainer.setFrameShape(QFrame.Shape.StyledPanel)
        self.toolContainer.setFrameShadow(QFrame.Shadow.Raised)
        self.toolContainer.setLayoutMargins(0, 0, 0, 0)
        
        self.toolLeftSpace = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.shareButton = TransparentToolButton(FluentIcon.SHARE, self.toolContainer)
        self.shareButton.setObjectName(u"shareButton")
        self.addToButton = TransparentToolButton(ThemedIcon.PLAYLIST_MUSIC, self.toolContainer)
        self.addToButton.setObjectName(u"addToButton")
        self.likeButton = TransparentToolButton(FluentIcon.HEART, self.toolContainer)
        self.likeButton.setObjectName(u"likeButton")
        self.toolRightSpace = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        self.toolContainer.addSpacerItem(self.toolLeftSpace)
        self.toolContainer.addWidget(self.shareButton)
        self.toolContainer.addWidget(self.addToButton)
        self.toolContainer.addWidget(self.likeButton)
        self.toolContainer.addSpacerItem(self.toolRightSpace)

        self.buttonContainer = HorizontalFrame(self.infoContainer)
        self.buttonContainer.setLayoutMargins(0, 0, 0, 0)
        self.buttonContainer.setContentSpacing(15)
        self.shuffleButton = PillPushButton(ThemedIcon.SHUFFLE, "Shuffle", self.buttonContainer)
        self.shuffleButton.setObjectName(u"shuffleButton")
        self.shuffleButton.setFixedSize(QSize(125, 36))
        self.playButton = PrimaryPushButton(FluentIcon.PLAY_SOLID, "Play", self.buttonContainer)
        self.playButton.setObjectName(u"playButton")
        self.playButton.setFixedSize(self.shuffleButton.size())
        height = self.playButton.size().height()
        qss = "PrimaryPushButton {border-radius: " + int(height/2).__str__() + "px;}"
        setCustomStyleSheet(self.playButton, qss, qss)
        self.buttonRightSpace = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.buttonContainer.addWidget(self.shuffleButton)
        self.buttonContainer.addWidget(self.playButton)
        self.buttonContainer.addSpacerItem(self.buttonRightSpace)
        
        spacer_top = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.infoContainer.addSpacerItem(spacer_top)
        
        self.infoContainer.addWidget(self.titleLabel)
        self.infoContainer.addWidget(self.bodyLabel)
        self.infoContainer.addWidget(self.toolContainer)
        self.infoContainer.addWidget(self.buttonContainer)
        
        spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.infoContainer.addSpacerItem(spacer)
        
        self.addWidget(self.coverLabel)
        self.addWidget(self.infoContainer)

    def setImage(self, image_path):
        size = self.coverLabel.size()
        if Path(image_path).exists():
            self.cover_path = image_path
            self.coverLabel.setImage(image_path)
            self.coverLabel.setFixedSize(size)
    
    def setTitle(self, title: str):
        self.titleLabel.setText(title)
        
    def getTitle(self):
        return self.titleLabel.text()
    
    
    def setBody(self, body):
        self.bodyLabel.setText(body)
        
    def getBody(self):
        return self.bodyLabel.text()
    
    def signalHangler(self):
        self.shuffleButton.clicked.connect(self.shuffleClicked.emit)
        self.playButton.clicked.connect(self.toggle_playButton)
        self.likeButton.clicked.connect(self.toggle_likeButton)
        self.shareButton.clicked.connect(self.shareClicked.emit)
        self.addToButton.clicked.connect(self.toggle_addToButton)
        
    def setPlaying(self, state):
        if state != self.is_playing:  # Only update if the state is different
            self.toggle_playButton()
    
    def setLiked(self, state):
        if state != self.is_liked:
            self.toggle_likeButton()
            
    def setAddTo(self, state):
        if state != self.is_added:
            self.toggle_addToButton()
        
    def toggle_playButton(self):
        if not self.is_playing:
            self.playButton.setIcon(FluentIcon.PAUSE_BOLD)
            self.playButton.setText("Pause")
            self.playClicked.emit(True)
            self.is_playing = True
        else:
            self.playButton.setIcon(FluentIcon.PLAY_SOLID)
            self.playButton.setText("Play")
            self.playClicked.emit(False)
            self.is_playing = False
    
    def toggle_likeButton(self):
        if not self.is_liked:
            self.likeButton.setIcon(ThemedIcon.HEART_SOLID)
            self.is_liked = True
            self.likeClicked.emit(True)
        else:
            self.likeButton.setIcon(FluentIcon.HEART)
            self.is_liked = False
            self.likeClicked.emit(False)
    
    def toggle_addToButton(self):
        if not self.is_added:
            self.is_added = True
            self.addClicked.emit(True)
        else:
            self.is_added = False
            self.addClicked.emit(False)
        
    


class BackgroundCard(QFrame):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.setMaximumHeight(500)
        self.card = WideCard(self)
        self.card.setMaximumWidth(700)
        
        self.vBoxLayout.addWidget(self.card)
        self.card.raise_()
        
                
        self.backgroundImage = ImageLabel(r"D:\Downloads\Images\4a725a8237e98108b860b03369563b9a.jpg", self)
        self.backgroundImage.setFixedHeight(500)
        self.card.raise_()
        self.blurBackground()
        # self.
        
    def blurBackground(self):
        # Create a QGraphicsBlurEffect
        blur_effect = QGraphicsBlurEffect(self)
        blur_effect.setBlurRadius(30)  # Set blur radius (higher values = more blur)
        self.backgroundImage.setGraphicsEffect(blur_effect)
        
        
    def resizeEvent(self, event):
        width = self.width()
        self.backgroundImage.scaledToWidth(width)
        if width < self.card.maximumWidth() + 100:
            self.vBoxLayout.setAlignment(self.card, Qt.AlignmentFlag.AlignTop)
        else:
            self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.card.resize(self.card.maximumWidth(), self.card.height())
        return super().resizeEvent(event)
        
        
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WideCard()
    # window = BackgroundCard()
    window.show()
    print(window.size())
    window.setPlaying(True)
    window.setLiked(True)
    app.exec()