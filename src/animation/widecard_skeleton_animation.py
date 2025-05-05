from qfluentwidgets import ImageLabel, SimpleCardWidget

import sys

from src.animation.skeleton_screen_animation import RectSkeletonScreen, HorizontalRectSkeletonScreen
from src.common.myFrame import HorizontalFrame, VerticalFrame
# print(sys.path)

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect


class WideCardSkeleton(HorizontalFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('WideCardSkeleton')
        self.initUI()
        self.setFixedSize(547, 222)
        
    def initUI(self):
        # PySide6.QtCore.QSize
        self.setContentsMargins(0, 0, 0, 0)
        self.thumbnailSkeleton = RectSkeletonScreen(200, 200)
        self.thumbnailSkeleton.setFixedSize(200, 200)
        
        self.container = VerticalFrame(self)
        self.titleSkeleton = HorizontalRectSkeletonScreen(40)
        self.titleSkeleton.setParent(self.container)
        self.titleSkeleton.setFixedHeight(40)
        self.infoSkeleton = RectSkeletonScreen(155, 25)
        self.infoSkeleton.setFixedHeight(25)
        self.infoSkeleton.setParent(self.container)
        self.optionSkeleton = RectSkeletonScreen(180, 30)
        self.optionSkeleton.setFixedHeight(30)
        
        self.buttonContainer = HorizontalFrame(self.container)
        self.skeleton1 = RectSkeletonScreen(100, 30)
        self.skeleton2 = RectSkeletonScreen(100, 30)
        self.buttonContainer.setFixedHeight(60)
        
        self.buttonContainer.addWidget(self.skeleton1)
        self.buttonContainer.addWidget(self.skeleton2)
        
        self.container.addWidget(self.titleSkeleton)
        self.container.addWidget(self.infoSkeleton)
        self.container.addWidget(self.optionSkeleton)
        self.container.addWidget(self.buttonContainer)
        
        # self.hBoxLayout.setContentsMargins(11, 11, 10, 0)

        self.addWidget(self.thumbnailSkeleton)
        self.addWidget(self.container, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.adjustSize()
        
    def start_animation(self):
        self.thumbnailSkeleton.start_animation()
        self.titleSkeleton.start_animation()
        self.infoSkeleton.start_animation()
        self.skeleton1.start_animation()
        self.skeleton2.start_animation()
        self.optionSkeleton.start_animation()
        
    def stop_animation(self):
        self.thumbnailSkeleton.stop_animation()
        self.titleSkeleton.stop_animation()  
        self.infoSkeleton.stop_animation()
        self.skeleton1.stop_animation()
        self.skeleton2.stop_animation()
        self.optionSkeleton.stop_animation()
        
if(__name__ == "__main__"):
    app = QApplication(sys.argv)
    window = WideCardSkeleton()
    window.start_animation()
    window.show()
    app.exec()