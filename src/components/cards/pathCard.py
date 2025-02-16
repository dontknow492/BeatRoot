from qfluentwidgets import ImageLabel, BodyLabel, TitleLabel, TransparentToolButton, TransparentDropDownToolButton, SubtitleLabel
from qfluentwidgets import FluentIcon, setCustomStyleSheet, setThemeColor, setTheme, Theme, ThemeColor

import sys
sys.path.append('src')
# print(sys.path)

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect

class PathCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("PathCard")
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        
        self.setupUi()
        
    def setupUi(self):
        # self.setStyleSheet("QFrame#PathCard{background-color: transparent;}")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignLeft)
        
        self.pathLabel = SubtitleLabel("D\\Program\\Musify", self)
        self.memoryLabel = BodyLabel("100MB", self)
        
        self.layout.addWidget(self.pathLabel)
        self.layout.addWidget(self.memoryLabel)
        
        
    def setPath(self, path):
        self.pathLabel.setText(path)
        
    def getPath(self):
        return self.pathLabel.text()
    
if(__name__ == "__main__"):
    app = QApplication(sys.argv)
    window = PathCard()
    window.resize(300, 32)
    window.show()
    # setThemeColor(QColor(34, 34, 34))
    app.exec()