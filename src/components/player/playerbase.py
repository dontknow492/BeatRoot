from qfluentwidgets import setCustomStyleSheet
from qfluentwidgets import FluentIcon
from qfluentwidgets import setTheme, Theme, ToggleToolButton, BodyLabel, ImageLabel, TitleLabel
from qfluentwidgets import Slider, TransparentToolButton, PrimaryToolButton, TransparentPushButton, TransparentDropDownToolButton
from qfluentwidgets import PillToolButton, SimpleCardWidget, themeColor, ThemeColor

import sys
sys.path.append(r'D:\Program\Musify')
# print(sys.path)
from src.utility.iconManager import ThemedIcon
from src.utility.enums import PlaceHolder
from src.common.myLabel import ClickableBodyLabel, ClickableTitleLabel, MyTitleLabel
from src.common.myButton import GifPrimaryToolButton
from src.animation.loading_circle import LoadingCircle
from src.common.myFrame import HorizontalFrame,VerticalFrame
from src.components.dialogs.audio_control import MusicControlPanel

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import QGraphicsOpacityEffect, QGraphicsBlurEffect

class PlayerScreen(SimpleCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.cover_path = PlaceHolder.SONG.path
        self.setContentsMargins(10, 0, 10, 0)
        self.setupUi()
        self.initToolTip()
        self.initCursor()
        self.setQss()
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        
    def setupUi(self):
        self.coverLabel = ImageLabel(image = self.cover_path, parent=self)
        self.coverLabel.setScaledContents(True)
        self.coverLabel.setFixedSize(QSize(84, 84))
        self.coverLabel.setBorderRadius(4, 4, 4, 4)
        
        self.initTitleAuthorContainer()
        
        self.initPlayerContainer()
        # self.playerContainer_layout.setAlignment(Qt.AlignHCenter)
        
        self.initExtraContainer()
        # self.extraContainer_layout.setAlignment(Qt.AlignRight)
        
        self.music_control_panel = MusicControlPanel()
        
        self.hBoxLayout.addWidget(self.coverLabel, Qt.AlignmentFlag.AlignLeading)
        self.hBoxLayout.addWidget(self.title_author_container, alignment= Qt.AlignmentFlag.AlignLeading)
        self.hBoxLayout.addWidget(self.playerContainer)
        self.hBoxLayout.addWidget(self.extraContainer)
        
    def initTitleAuthorContainer(self):
        self.title_author_container = VerticalFrame(self)
        self.title_author_container.setContentsMargins(0, 0, 0, 0)
        self.title_author_container.setMaximumWidth(300)
        self.title_author_container.setMinimumWidth(210)
        self.titleLabel = ClickableTitleLabel("Title", parent=self.title_author_container)
        # self.titleLabel.setStyleSheet("background: red;")
        self.titleLabel.setFont(QFont("Segoe UI", 16, weight=550))
        self.authorLabel = ClickableBodyLabel("Author", self.title_author_container)
        # self.authorLabel.setStyleSheet("background: green;")
        self.title_author_container.addWidget(self.titleLabel, alignment=Qt.AlignmentFlag.AlignBottom)
        self.title_author_container.addWidget(self.authorLabel, alignment=Qt.AlignmentFlag.AlignTop)
        
    def initPlayerContainer(self):
        self.playerContainer = VerticalFrame(self)
        # self.playerContainer.layout().setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.playerContainer.setContentSpacing(0)
        self.playerContainer.setContentsMargins(0, 0, 0, 0)
        self.playerContainer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        # self.playerContainer.setLayoutMargins(0, 9, 0, 9)
        # self.playerContainer.setMaximumWidth(400)
        
        self.progressContainer = VerticalFrame(self.playerContainer)
        self.progressContainer.setMaximumHeight(40)
        self.progressContainer.setContentsMargins(0, 0, 0, 0)
        self.progressContainer.setLayoutMargins(0, 0, 0, 0)
        self.progressContainer.setContentSpacing(0)
        
        self.audioSlider = Slider(Qt.Horizontal, self.progressContainer)
        self.audioSlider.setRange(0, 100)
        self.timerContainer = HorizontalFrame(self.progressContainer)
        self.timerContainer.layout().setContentsMargins(0, 0, 0, 0)
        self.current_time_label = BodyLabel("00:00", self.timerContainer)
        self.total_time_label = BodyLabel("00:00", self.timerContainer)
        
        self.timerContainer.addWidget(self.current_time_label, alignment= Qt.AlignmentFlag.AlignLeft)
        self.timerContainer.addWidget(self.total_time_label, alignment= Qt.AlignmentFlag.AlignRight)
        
        self.progressContainer.addWidget(self.audioSlider)
        self.progressContainer.addWidget(self.timerContainer)
        
        self.optionContainer = HorizontalFrame(self.playerContainer)
        self.optionContainer.setContentsMargins(0, 0, 0, 0)
        self.optionContainer.setMaximumHeight(40)
        self.optionContainer.layout().setContentsMargins(0, 0, 0, 0)
        self.shuffleButton = PillToolButton(ThemedIcon.SHUFFLE, self.optionContainer)
        self.shuffleButton.setFixedSize(QSize(34, 34))
        self.prevButton = TransparentToolButton(ThemedIcon.PREV_SOLID, self.optionContainer)
        self.prevButton.setIconSize(QSize(20, 20))
        self.playButton = PrimaryToolButton(FluentIcon.PLAY_SOLID, self.optionContainer)
        self.playButton.setFixedSize(QSize(38, 38))
        self.loadingCircle = LoadingCircle(self.optionContainer)
        self.loadingCircle.setAttribute(10, 3)
        self.loadingCircle.setFixedSize(QSize(38, 38))
        self.loadingCircle.setStyleSheet(f"background-color: {ThemeColor.DARK_3.color().name()}; border-radius: {self.loadingCircle.width()//2}")
        self.nextButton = TransparentToolButton(ThemedIcon.NEXT_SOLID, self.optionContainer)
        self.nextButton.setIconSize(QSize(20, 20))
        self.repeatButton = PillToolButton(ThemedIcon.REPEAT, self.optionContainer)
        self.repeatButton.setFixedSize(QSize(34, 34))
        
        self.optionContainer.addWidget(self.shuffleButton)   
        self.optionContainer.addWidget(self.prevButton)
        self.optionContainer.addWidget(self.playButton)
        self.optionContainer.addWidget(self.loadingCircle)
        self.optionContainer.addWidget(self.nextButton)
        self.optionContainer.addWidget(self.repeatButton)
        
        self.playerContainer.addWidget(self.progressContainer)
        self.playerContainer.addWidget(self.optionContainer)
        
    def initExtraContainer(self):
        self.extraContainer = VerticalFrame(self)
        self.extraContainer.setContentSpacing(0)
        self.extraContainer.setContentsMargins(0, 0, 0, 0)
        self.extraContainer.setLayoutMargins(0, 0, 0, 0)
        self.extraContainer.setMaximumWidth(300)
        # self.extraContainer.setFixedHeight(80)
        #init title, author label
        
        self.moreOptionContainer = HorizontalFrame(self.extraContainer)
        self.moreOptionContainer.setContentsMargins(0, 0, 0, 0)
        self.moreOptionContainer.setLayoutMargins(0, 0, 0, 0)
        self.moreOptionContainer.setContentSpacing(10)
        self.moreOptionContainer.layout().setAlignment(Qt.AlignHCenter)
        
        self.queuesButton = TransparentToolButton(ThemedIcon.QUEUE, self.moreOptionContainer)
        self.speedButton = TransparentDropDownToolButton(ThemedIcon.PLAYBACK_SPEED, self.moreOptionContainer)
        self.likeButton = TransparentToolButton(FluentIcon.HEART, self.moreOptionContainer)
        self.downloadButton = TransparentToolButton(FluentIcon.DOWNLOAD, self.moreOptionContainer)
        self.controlPanel = TransparentToolButton(FluentIcon.SETTING, self.moreOptionContainer)
        
        self.moreOptionContainer.addWidget(self.queuesButton)
        self.moreOptionContainer.addWidget(self.speedButton)
        self.moreOptionContainer.addWidget(self.likeButton)
        self.moreOptionContainer.addWidget(self.downloadButton)
        self.moreOptionContainer.addWidget(self.controlPanel)
        
        self.volumeContainer = HorizontalFrame(self.extraContainer)
        self.volumeContainer.setContentSpacing(0)
        self.volumeContainer.setLayoutMargins(0, 0, 0, 0)

        self.volumeButton = TransparentToolButton(FluentIcon.VOLUME, self.volumeContainer)
        self.volumeSlider = Slider(Qt.Horizontal, self.volumeContainer)
        self.volumeSlider.setRange(0, 100)
        self.volumeSlider.setMaximumWidth(300)
        self.volumeValue = BodyLabel("100", self.volumeContainer)
        
        self.volumeContainer.addWidget(self.volumeButton)
        self.volumeContainer.addWidget(self.volumeSlider)
        self.volumeContainer.addWidget(self.volumeValue)
        
        self.extraContainer.addWidget(self.moreOptionContainer, alignment= Qt.AlignmentFlag.AlignBottom)
        self.extraContainer.addWidget(self.volumeContainer)
        
    def initToolTip(self):
        self.playButton.setToolTip("Play")
        self.prevButton.setToolTip("Previous")
        self.nextButton.setToolTip("Next")
        self.queuesButton.setToolTip("Queues")
        self.likeButton.setToolTip("Like")
        self.repeatButton.setToolTip("Repeat")
        self.shuffleButton.setToolTip("Shuffle")
        self.volumeButton.setToolTip("Volume")
        self.speedButton.setToolTip("Playback Speed")
        self.downloadButton.setToolTip("Download")
        self.controlPanel.setToolTip("Audio Control")
    
    def initCursor(self):
        self.playButton.setCursor(Qt.PointingHandCursor)
        self.prevButton.setCursor(Qt.PointingHandCursor)
        self.nextButton.setCursor(Qt.PointingHandCursor)
        self.queuesButton.setCursor(Qt.PointingHandCursor)
        self.likeButton.setCursor(Qt.PointingHandCursor)
        self.repeatButton.setCursor(Qt.PointingHandCursor)
        self.volumeButton.setCursor(Qt.PointingHandCursor)
        self.volumeSlider.setCursor(Qt.PointingHandCursor)
        self.speedButton.setCursor(Qt.PointingHandCursor)
        self.shuffleButton.setCursor(Qt.PointingHandCursor)
        self.titleLabel.setCursor(Qt.PointingHandCursor)
        self.authorLabel.setCursor(Qt.PointingHandCursor)
        self.audioSlider.setCursor(Qt.PointingHandCursor)
        self.downloadButton.setCursor(Qt.PointingHandCursor)
        self.controlPanel.setCursor(Qt.PointingHandCursor)
    
    def setQss(self):
        qss = "PrimaryToolButton{border-radius: 19px;}"
        setCustomStyleSheet(self.playButton, qss, qss)
        
    def resizeEvent(self, event):
        print("resize", self.height())
        if self.width() < 900:
            # self.title_author_container.setMaximumWidth(200)
            self.title_author_container.setMinimumWidth(100)
        if self.width() > 900:
            self.title_author_container.setMinimumWidth(210)
        return super().resizeEvent(event)
        
    def set_loading(self, loading: bool):
        if loading:
            self.nextButton.setEnabled(False)
            self.prevButton.setEnabled(False)
            self.start_animation()
        else:
            self.nextButton.setEnabled(True)
            self.prevButton.setEnabled(True)
            self.stop_animation()
        
    def start_animation(self):
        # self.loadingCircle.start_gif("Loading")
        self.playButton.hide()
        self.loadingCircle.show()
        self.loadingCircle.start_animation()

    def stop_animation(self):
        # self.loadingCircle.stop_gif()
        self.loadingCircle.stop_animation()
        self.loadingCircle.hide()
        self.playButton.show()
        # self.playButton.setStopIcon(FluentIcon.PLAY_SOLID)    
    
if __name__ == '__main__':
    setTheme(Theme.DARK)
    app = QApplication(sys.argv)
    window = PlayerScreen()
    # print(themeColor(), ThemeColor.PRIMARY.color())
    # window.setFixedHeight(100)
    window.setMaximumHeight(100)
    window.resize(1200, 90)
    window.show()
    # window.start_animation()
    # window.loadingCircle.setPalette(QColor(100, 100, 100,100))
    # print(f"background-color: {ThemeColor.DARK_3.color().name()}; border-radius: {self.width()//2}")
    print(window.repeatButton.size())
    app.exec()