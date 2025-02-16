from qfluentwidgets import ImageLabel, BodyLabel, LargeTitleLabel
from qfluentwidgets import FluentIcon, setCustomStyleSheet, PrimaryPushButton, SearchLineEdit
from qfluentwidgets import SearchLineEdit, SimpleCardWidget, TransparentPushButton
from qfluentwidgets import Theme, setTheme, setCustomStyleSheet


import sys
sys.path.append(r'D:\Program\Musify')

from src.common.myFrame import VerticalFrame
from src.utility.check_net_connectivity import is_connected_to_internet
from src.utility.enums import ImageFolder

from PySide6.QtWidgets import QFrame,  QSpacerItem, QSizePolicy, QStackedWidget
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QColor


class SearchInterface(VerticalFrame):
    searchSignal = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('SearchInterface')
        
        self.historyText = list()
        
        self.initUi()
        
    def initUi(self):
        self.searchBar = SearchLineEdit(self)
        self.searchBar.setPlaceholderText("Search")
        self.searchBar.setClearButtonEnabled(True)
        self.searchBar.setFixedHeight(50)
        self.searchBar.setClearButtonEnabled(True)
        self.searchBar.setClearButtonEnabled(True)
        self.searchBar.textChanged.connect(self.on_searchBar_text_changed)
        self.searchBar.searchButton.clicked.connect(lambda: self.searchSignal.emit(self.searchBar.text()))
        
        # self.searchDropDown.raise_()
        # self.searchDropDown.hide()
        # Add options
        
        
        self.frame = VerticalFrame(self)
        self.frame.setObjectName("frame")
        
        image = FluentIcon.GLOBE.icon(color= QColor("#757575")).pixmap(100, 100)
        self.placeholder_image = ImageLabel(image, self)
        self.placeholder_text = LargeTitleLabel("Search to get results", self)
        
        qss = """
            LargeTitleLabel {
                color: #B0B0B0;;
            }
        """
        qss_d = """LargeTitleLabel {color: #757575;}"""
        setCustomStyleSheet(self.placeholder_text, qss_d, qss_d)
        
        self.placeholder_image.setWordWrap(True)
        self.frame.addWidget(self.placeholder_image, 3, alignment= Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.frame.addWidget(self.placeholder_text, 2,alignment= Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        self.addWidget(self.searchBar)
        # self.addWidget(self.searchDropDown)
        self.addWidget(self.frame, 1)
        
        
        self.searchDropDown = VerticalFrame(self)
        self.searchDropDown.setObjectName("searchDropDown")
        self.searchDropDown.setFrameShape(QFrame.StyledPanel)
        self.searchDropDown.setFrameShadow(QFrame.Raised)
        spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.searchDropDown.addWidget(spacer)
        self.setMinimumHeight(100)
        self.searchDropDown.hide()
        
    def on_searchBar_text_changed(self, text):
        if text and len(self.historyText) != 0:
            self.searchDropDown.show()
        else:
            self.searchDropDown.hide()
    
    def resizeEvent(self, event):
        # if not self.searchDropDown.isHidden():
        pos = self.searchBar.pos()
        height = self.searchBar.height()
        self.searchDropDown.move(pos.x(), pos.y()+ 6 + height)
            
        self.searchDropDown.resize(self.searchBar.width(), self.searchBar.height()*4)
        super().resizeEvent(event)
    
    def addHistory(self, text):
        qss = "TransparentPushButton{text-align: left;}"
        self.historyText.append(text)
        button = TransparentPushButton(text)
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(lambda: self.historySelected(text))
        setCustomStyleSheet(button, qss, qss)
        self.searchDropDown.insertWidget(0, button)
        
    def historySelected(self, text):
        self.searchBar.setText(text)
        self.searchBar.setFocus()
        
        