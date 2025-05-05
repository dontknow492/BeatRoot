import sys


from src.interfaces.view.base.viewbase import ViewBase

from qfluentwidgets import PrimaryPushButton

from PySide6.QtCore import Qt
from src.utility.enums import ImageFolder

from loguru import logger

from pathlib import Path

class PlaylistViewBase(ViewBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('PlaylistViewBase')
        
        self.loadMoreButton = PrimaryPushButton("Load More", self)
        self.loadMoreButton.setCursor(Qt.CursorShape.PointingHandCursor)
        self.loadMoreButton.clicked.connect(self.loadMore)
        self.loadMoreButton.hide()
        
        
    
    
    def loadData(self, data: dict):
        self.tracks = data.get("tracks", [])
        if len(self.tracks) == 0:
            self.errorOccurred.emit("No tracks found")
            return False
        self.title = data.get("title", "Unknown")
        self.description = data.get("description", "Unknown")
        self.artist = data.get("artist", [])
        
        self.thumbnail = Path(ImageFolder.PLAYLIST.path) / f"{self.view_id}.png"
        return True
        # self.update_view_card()
        
    def create_media_cards(self):
        logger.info(f"total trackss: {len(self.tracks)}")
        for index, track in enumerate(self.tracks, start=0):
            if(index >= 20) and len(self.tracks) >= 20:
                self.addWidget(self.loadMoreButton, alignment=Qt.AlignmentFlag.AlignCenter)
                self.loadMoreButton.show()
                break
            card = self.createAudioCard(track)
            if card:
                self.addWidget(card)
        logger.info(f"loaded tracks: {self.song_count}/{len(self.tracks)}")
        self.uiLoaded.emit()
        
    def loadMore(self):
        logger.info("load more clicked")
        self.loadMoreButton.setEnabled(False)
        self.loadMoreButton.setText("Loading...")
        for x in range(self.song_count - 1, self.song_count + 20 -1):
            if x >= len(self.tracks) - 1:
                logger.info("All songs are loaded")
                self.loadMoreButton.setEnabled(False)
                self.loadMoreButton.setText("No more songs")
                self.layout().removeWidget(self.loadMoreButton)
                self.addWidget(self.loadMoreButton, alignment=Qt.AlignmentFlag.AlignCenter)
                return
            card = self.createAudioCard(self.tracks[x])
            if card:
                self.addWidget(card)
                
        self.loadMoreButton.setEnabled(True)
        self.loadMoreButton.setText("Load More")
        self.layout().removeWidget(self.loadMoreButton)
        self.addWidget(self.loadMoreButton, alignment=Qt.AlignmentFlag.AlignCenter)
    
    