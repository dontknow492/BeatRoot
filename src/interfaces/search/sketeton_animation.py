
import sys


from src.common.myScroll import VerticalScrollWidget
from src.animation.audio_skeleton_animation import LandscapeAudioSkeleton
from PySide6.QtCore import Qt, QSize, Signal, QPoint, QTimer

class SearchResultSkeleton(VerticalScrollWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('SearchResultSkeleton')
        self.ui_elements = list()
        self.initUi()
        
        self.setCursor(Qt.CursorShape.WaitCursor)
        
    def initUi(self):
        for _ in range(7):
            card = LandscapeAudioSkeleton()
            if card:
                self.ui_elements.append(card)
                card.setFixedHeight(90)
                self.addWidget(card, alignment=Qt.AlignmentFlag.AlignTop)
                
                
    def start_animation(self):
        # Synchronize animation start using a QTimer
        QTimer.singleShot(100, self._start_all_Animations)
        
    def _start_all_Animations(self):
        for element in self.ui_elements:
            element.start_animation()
            
    def stop_animation(self):
        for element in self.ui_elements:
            element.stop_animation()
        
        