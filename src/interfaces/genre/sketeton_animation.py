import sys


from src.common.myFrame import FlowFrame
from src.animation.playlist_skeleton_animation import PlaylistSkeleton

from PySide6.QtCore import QTimer, Qt
import sys

class GenrePlaylistsSkeleton(FlowFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.WaitCursor)
        self.setObjectName('GenrePlaylistsSkeleton')
        self.ui_elements = list()
        for _ in range(20):
            skeleton = PlaylistSkeleton()
            if skeleton:
                self.ui_elements.append(skeleton)
                self.addWidget(skeleton)
            
    def start_animation(self):
        # Synchronize animation start using a QTimer
        QTimer.singleShot(100, self._start_all_Animations)
        
    def _start_all_Animations(self):
        for element in self.ui_elements:
            element.start_animation()
            
    def stop_animation(self):
        for element in self.ui_elements:
            element.stop_animation()

