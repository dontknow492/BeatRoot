

import sys

from src.common.myFrame import VerticalFrame, HorizontalFrame, FlowFrame
from src.common.myScroll import SideScrollWidget, VerticalScrollWidget
from src.animation import RectSkeletonScreen, PlaylistSkeleton
from PySide6.QtCore import Qt, QTimer




class HomeAnimationSkeleton(VerticalScrollWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('HomeAnimationSkeleton')
        self.ui_elements = list()
        self.setContentSpacing(20)
        self.initUI()
        self.setCursor(Qt.CursorShape.WaitCursor)
        # self.addWidget(self.genreContainer)
        # self.addWidget(self.playlistContainer)
        # self.addWidget(self.albumContainer)
        
        
    def initUI(self):
        title_skeleton = RectSkeletonScreen(200, 40)
        title_skeleton.setFixedSize(200, 40)
        self.ui_elements.append(title_skeleton)
        self.genreContainer = FlowFrame(self)
        for _ in range(10):
            card = RectSkeletonScreen(220, 50)
            card.setFixedSize(220, 50)
            if card:
                self.ui_elements.append(card)
                self.genreContainer.addWidget(card)
                
        self.addWidget(title_skeleton)
        self.addWidget(self.genreContainer)
                
        title_skeleton = RectSkeletonScreen(200, 40)
        title_skeleton.setFixedSize(200, 40)
        self.ui_elements.append(title_skeleton)
        self.playlistContainer = SideScrollWidget(None, self)
        self.playlistContainer.setFixedHeight(300)
        for _ in range(6):
            card = PlaylistSkeleton()
            if card:
                self.ui_elements.append(card)
                self.playlistContainer.addWidget(card)
                
        self.addWidget(title_skeleton)
        self.addWidget(self.playlistContainer)
                
        title_skeleton = RectSkeletonScreen(200, 40)
        title_skeleton.setFixedSize(200, 40)
        self.ui_elements.append(title_skeleton)
        self.albumContainer = SideScrollWidget(None, self)
        for _ in range(6):
            card = RectSkeletonScreen(170, 100)
            card.setParent(self.albumContainer)
            card.setFixedSize(170, 50)
            if card:
                self.ui_elements.append(card)
                self.albumContainer.addWidget(card)
            
        self.addWidget(title_skeleton)
        self.addWidget(self.albumContainer)
        
    def start_animation(self):
        # Synchronize animation start using a QTimer
        QTimer.singleShot(1000, self._start_all_animations)
        
    def _start_all_animations(self):
        for element in self.ui_elements:
            QTimer.singleShot(0, element.start_animation)
            
    def stop_animation(self):
        for element in self.ui_elements:
            element.stop_animation()
    
