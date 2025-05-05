from qfluentwidgets import ImageLabel, BodyLabel, TitleLabel, TransparentToolButton, TransparentDropDownToolButton
from qfluentwidgets import FluentIcon, setCustomStyleSheet, PrimaryPushButton
from qfluentwidgets import SearchLineEdit


import sys

from src.common.myScroll import MyScrollWidgetBase, FlowScrollWidget, VerticalScrollWidget
from src.common.myFrame import HorizontalFrame, VerticalFrame
from src.common.myButton import PrimaryRotatingButton
from src.components.cards.artistCard import ArtistCard
from src.utility.downloader.thumbnail_downloader import ThumbnailDownloader

# from utility.default_value import MusifyDefault
# from pathlib import Path

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy, QStackedWidget
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect


class LibraryInterfaceBase(VerticalFrame):
    error = Signal(str)
    def __init__(self, parent = None):
        super().__init__(parent=parent)
        self.setObjectName("LibraryInterface")
        self.setupUi()
        # self.add_refresh()
        self.setContentsMargins(0, 0, 0, 0)
        self.setContentSpacing(0)
        
        
    def setupUi(self):
        # self.homeWidget.setContentsMargins(0, 0, 0, 0)
        
        self.searchBar = SearchLineEdit(self)
        self.searchBar.setFixedHeight(50)
        self.searchBar.setPlaceholderText("Search")
        self.scrollArea = FlowScrollWidget(None, self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalSpacing(20)
        self.scrollArea.setVerticalSpacing(10)
        self.scrollArea.setContentsMargins(0, 0, 0, 0)
        # self.scrollArea.setLayoutMargins(0, 0, 0, 0)
        
        self.optionContainer = HorizontalFrame(self)
        self.optionContainer.setContentsMargins(0, 6, 0, 0)
        self.optionContainer.setLayoutMargins(0, 0, 0, 0)
        self.addWidget(self.searchBar, alignment=Qt.AlignmentFlag.AlignTop)
        self.addWidget(self.optionContainer, alignment=Qt.AlignmentFlag.AlignTop)
        self.addWidget(self.scrollArea, stretch= 1)
        
    def add_refresh(self):
        self.refresh_button = PrimaryRotatingButton(FluentIcon.SYNC, "Refresh", self.optionContainer)
        self.refresh_button.clicked.connect(self.on_refresh)
        
        self.addOption(self.refresh_button, alignment= Qt.AlignmentFlag.AlignTrailing)
        
    def on_refresh(self):
        QTimer.singleShot(1000, self.fetch_data)    
        
        
    def hideSearchBar(self):
        self.searchBar.hide()
        
    def showSearchBar(self):
        self.searchBar.show()
        
    def addCard(self, card):
        self.scrollArea.addWidget(card)
        
    def removeCard(self, card):
        self.scrollArea.removeWidget(card)
        card.deleteLater()
        self.scrollArea.update()
            
    def addOptions(self, options):
        for option in options:
            self.addOption(option)
    
    def addOption(self, option, stretch = 0, alignment: Qt.AlignmentFlag | None = None):
        if hasattr(option, "setCursor"):
            option.setCursor(Qt.CursorShape.PointingHandCursor)
        self.optionContainer.addWidget(option, stretch, alignment)
        
    
    def hideOptions(self):
        self.optionContainer.hide()
        
    def showOptions(self):
        self.optionContainer.show()
        
    def setContentLayout(self, layout):
        self.homeWidget_layout.deleteLater()
        self.homeWidget_layout = layout
        self.homeWidget.setLayout(self.homeWidget_layout)
        
        
        
        
if(__name__ == '__main__'):
    app = QApplication(sys.argv)
    window = LibraryInterfaceBase()
    window.show()
    # window.tempMedia(2)
    # window.tempOption(2)
    print("hello")
    app.exec()