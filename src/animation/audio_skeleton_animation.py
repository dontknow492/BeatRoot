
import sys
sys.path.append(r'D:\Program\Musify')
from src.animation.skeleton_screen_animation import RectSkeletonScreen, HorizontalRectSkeletonScreen
from src.common.myFrame import HorizontalFrame, VerticalFrame
# print(sys.path)

from PySide6.QtWidgets import QApplication

from loguru import logger

class PortraitAudioSkeleton(VerticalFrame):
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
        logger.info("Animation Started")
        
    def stop_animation(self):
        self.thumbnailSkeleton.stop_animation()
        self.titleSkeleton.stop_animation()  
        self.infoSkeleton.stop_animation()
        logger.info("Animation Stopped")
        
class LandscapeAudioSkeleton(HorizontalFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        # self.setFixedSize(280, 173)
        self.setFixedHeight(90)
        self.setContentsMargins(0, 0, 0, 0)
        self.thumbnailSkeleton = RectSkeletonScreen(60, 60)
        self.thumbnailSkeleton.setFixedSize(60, 60)
        
        self.container = VerticalFrame(self)
        self.container.setContentSpacing(0)
        self.titleSkeleton = HorizontalRectSkeletonScreen(20)
        self.titleSkeleton.setParent(self.container)
        self.titleSkeleton.setFixedHeight(30)
        self.infoSkeleton = RectSkeletonScreen(155, 15)
        self.infoSkeleton.setParent(self.container)
        
        self.container.addWidget(self.titleSkeleton)
        self.container.addWidget(self.infoSkeleton)

        
        # self.hBoxLayout.setContentsMargins(11, 11, 10, 0)

        self.addWidget(self.thumbnailSkeleton)
        self.addWidget(self.container)
        
        self.adjustSize()
        
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
    # window = PortraitAudioSkeleton()
    window = LandscapeAudioSkeleton()
    window.start_animation()
    window.show()
    app.exec()