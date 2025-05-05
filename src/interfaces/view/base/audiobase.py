import sys


from src.interfaces.view.base.playlistbase import PlaylistViewBase

from qfluentwidgets import TitleLabel

from src.utility.enums import ImageFolder

from pathlib import Path


class AudioViewBase(PlaylistViewBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('AudioViewBase')
        
        self.addWidget(TitleLabel("Up Next", self))
        
        self.uiLoaded.emit()
    
    def loadData(self, data: dict):
        self.tracks = data.get("tracks", [])
        if len(self.tracks) == 0:
            self.errorOccurred.emit("No tracks found")
            return False
        first_track = self.tracks[0]
        self.title = first_track.get("title", "Unknown")
        self.view_card_id = first_track.get("videoId", None)
        self.artist = first_track.get("artist", [{}])
        self.description = ' ,'.join([artist.get("name", "Unknown") for artist in self.artist])
        self.thumbnail = Path(ImageFolder.SONG.path) / f"{self.view_card_id}.png"
        return True