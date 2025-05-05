import sys


from src.interfaces.view.base.viewbase import ViewBase

class AlbumViewBase(ViewBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('AlbumViewBase')

    def loadData(self, data: dict)->bool:
        self.tracks = data.get("tracks", [])
        if len(self.tracks) == 0:
            self.errorOccurred.emit("No tracks found")
            return False
        self.title = data.get("name", None) or data.get('title', "Unknown")
        self.description = data.get("description", "Unknown")
        self.thumbnails = data.get("thumbnails", None)
        self.artist = data.get("artist", [])
        self.tracks = data.get("tracks", [])
        return True
        
        
    def create_media_cards(self):
        for track in self.tracks:
            card = self.createAudioCard(track)
            if card:
                self.addWidget(card)
        self.uiLoaded.emit()
    
    