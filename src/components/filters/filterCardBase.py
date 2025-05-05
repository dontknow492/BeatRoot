from qfluentwidgets import ImageLabel, BodyLabel, TitleLabel, TransparentToolButton, PrimaryPushButton, TransparentDropDownPushButton
from qfluentwidgets import FluentIcon, setCustomStyleSheet, PrimaryToolButton, SearchLineEdit, PillToolButton

import sys

from src.common.myButton import PrimaryRotatingButton

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy, QStackedLayout
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, Signal, QVariantAnimation
from PySide6.QtGui import QFont, QColor, QTransform, QIcon, QPixmap
from PySide6.QtWidgets import QGraphicsDropShadowEffect


class FilterBase(QFrame):
    refreshClicked = Signal()
    def __init__(self, parent = None,):
        super().__init__(parent)
        
        self.isRefreshing = False
        
        self.setupUi()
        self.setFilterBaseStyleSheet()
        self.initAnimation()
        self.signalHandler()
        
    def setupUi(self):
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setSpacing(6)
        self.mainLayout.setAlignment(Qt.AlignTop)
        self.optionContainer = QFrame(self)
        self.optionLayout = QHBoxLayout(self.optionContainer)
        self.optionContainer.setContentsMargins(0, 0, 0, 0)
        self.optionLayout.setContentsMargins(0, 0, 0, 0)
        
        self.playButton = PrimaryPushButton(FluentIcon.PLAY_SOLID, "Play", self.optionContainer)
        self.playButton.setFixedWidth(90)
        
        self.spaceItem = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.searchButton = TransparentToolButton(FluentIcon.FILTER, self.optionContainer)
        self.sortByButton = TransparentDropDownPushButton("Sort by", self.optionContainer)
        self.refreshButton = PrimaryRotatingButton(FluentIcon.SYNC, "Refresh", self.optionContainer)
        
        self.optionLayout.addWidget(self.playButton)
        self.optionLayout.addItem(self.spaceItem)
        self.optionLayout.addWidget(self.searchButton)
        self.optionLayout.addWidget(self.sortByButton)
        self.optionLayout.addWidget(self.refreshButton)
        
        self.searchBar = SearchLineEdit(self)
        
        self.mainLayout.addWidget(self.optionContainer)
        self.mainLayout.addWidget(self.searchBar)
        
    def signalHandler(self):
        self.playButton.clicked.connect(self.playClicked)
        self.refreshButton.clicked.connect(self.refreshClicked)
        
    def playClicked(self):
        if self.playButton.text() == "Play":
            self.playButton.setText("Pause")
            self.playButtonClicked.emit(True)
            self.playButton.setIcon(FluentIcon.PAUSE_BOLD)
        else:
            self.playButton.setText("Play")
            self.playButtonClicked.emit(False)
            self.playButton.setIcon(FluentIcon.PLAY_SOLID)
            
    

    
        
    def initAnimation(self):
        self.animation = QPropertyAnimation(self.searchBar, b"maximumHeight")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        
    def setFilterBaseStyleSheet(self):
        qss = "PrimaryPushButton{border-radius: 16px}"
        setCustomStyleSheet(self.refreshButton, qss, qss)
        setCustomStyleSheet(self.playButton, qss, qss)

        qss = "SearchLineEdit{border-radius: 12px}"
        setCustomStyleSheet(self.searchBar, qss, qss)
        
    def searchButtonClicked(self):
        print("search button clicked")
        if self.searchBar.isHidden():
            self.searchBar.setHidden(False)
            self.searchShowAnimation()
        else:
            self.searchHideAnimation()
        
    def searchShowAnimation(self):
        if self.animation.state() == QPropertyAnimation.Running:
            return
        
        self.animation.setStartValue(0)
        self.animation.setEndValue(48)
        self.animation.finished.connect(self.searchBar.show)
        self.animation.start()
        
    def searchHideAnimation(self):
        self.animation.setStartValue(48)
        self.animation.setEndValue(0)
        self.animation.finished.connect(self.searchBar.hide)
        self.animation.start()
        
if(__name__ == '__main__'):
    app = QApplication(sys.argv)
    window = FilterBase()
    # window.setFixedSize(193, 270)
    window.show()
    print(window.size())
    app.exec()