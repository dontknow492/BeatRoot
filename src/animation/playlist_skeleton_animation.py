import sys
sys.path.append(r'D:\Program\Musify')
from src.animation.skeleton_screen_animation import RectSkeletonScreen, HorizontalRectSkeletonScreen
from src.common.myFrame import VerticalFrame
# print(sys.path)
from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy

from loguru import logger

class PlaylistSkeleton(VerticalFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFixedSize(173, 280)
        
        self.thumbnailSkeleton = RectSkeletonScreen(150, 150)
        self.thumbnailSkeleton.setFixedSize(150, 150)
        self.titleSkeleton = HorizontalRectSkeletonScreen(30)
        self.titleSkeleton.setFixedSize(150, 30)
        self.infoSkeleton = RectSkeletonScreen(95, 20)
        
        # self.vBoxLayout.setContentsMargins(11, 11, 10, 0)
        
        self.addWidget(self.thumbnailSkeleton)
        self.addWidget(self.titleSkeleton)
        self.addWidget(self.infoSkeleton)
        
        
    def start_animation(self):
        self.thumbnailSkeleton.start_animation()
        self.titleSkeleton.start_animation()
        self.infoSkeleton.start_animation()
        
    def stop_animation(self):
        self.thumbnailSkeleton.stop_animation()
        self.titleSkeleton.stop_animation()  
        self.infoSkeleton.stop_animation()
        
        
if(__name__ == "__main__"):
    app = QApplication(sys.argv)
    window = PlaylistSkeleton()
    window.show()
    app.exec()