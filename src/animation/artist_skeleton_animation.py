import sys

from src.animation.skeleton_screen_animation import RectSkeletonScreen, HorizontalRectSkeletonScreen, RoundedSkeletonScreen
from src.common.myFrame import VerticalFrame
# print(sys.path)
from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt

from loguru import logger

class ArtistSkeleton(VerticalFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFixedSize(173,  230)
        
        self.thumbnailSkeleton = RoundedSkeletonScreen(75, 0)
        # self.thumbnailSkeleton.setFixedSize(130, 130)
        self.thumbnailSkeleton.setFixedHeight(150)
        self.titleSkeleton = HorizontalRectSkeletonScreen(30)
        self.titleSkeleton.setFixedSize(130, 30)
        
        # self.vBoxLayout.setContentsMargins(11, 11, 10, 0)
        
        self.addWidget(self.thumbnailSkeleton)
        self.addWidget(self.titleSkeleton, alignment=Qt.AlignHCenter)
        
    def start_animation(self):
        self.thumbnailSkeleton.start_animation()
        self.titleSkeleton.start_animation()
        
    def stop_animation(self):
        self.thumbnailSkeleton.stop_animation()
        self.titleSkeleton.stop_animation() 
        
if(__name__ == "__main__"):
    app = QApplication(sys.argv)
    window = ArtistSkeleton()
    window.show()
    window.stop_animation()
    app.exec()