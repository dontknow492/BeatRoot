import sys


from src.interfaces.view.base.viewbase import ViewBase

from qfluentwidgets import PrimaryPushButton

from PySide6.QtCore import Qt
from src.utility.enums import ImageFolder
from src.common.myScroll import SideScrollWidget
from src.components.cards.audioCard import AudioCard

from loguru import logger

from pathlib import Path


class ArtistViewBase(ViewBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setObjectName('ArtistViewBase')
        
        self.artist_count = 1
        
        self.artistAlbumsContainer = SideScrollWidget("Albums", self)
        self.artistAlbumsContainer.setMinimumHeight(340)
        self.artistAlbumsContainer.hide()
        
        self.artistRelatedContainer = SideScrollWidget("Related", self)
        self.artistRelatedContainer.setMinimumHeight(300)
        self.artistRelatedContainer.hide()
        
        self.is_album_empty = True
        self.is_related_empty = True
        
        
        
    def loadData(self, data: dict):
        self.title = data.get("name", "Unknown")
        self.description = data.get("description", "Unknown")
        thumbnail = Path(ImageFolder.ARTIST.path) / f"{self.view_card_id}.png"
        if thumbnail.exists():
            self.thumbnail = thumbnail
            self.viewCard.setImage(str(thumbnail))
        else:
            self.thumbnails = data.get("thumbnails", None)
            self.thumbnails_downloader.download_thumbnail(self.thumbnails[-1].get('url'), f"{self.view_card_id}.png", ImageFolder.ARTIST.path, self.view_card_id)
        self.songs = data.get("songs", {})
        self.albums = data.get("albums", {})
        self.related = data.get("related", {})
        self.singles = data.get("singles", {})
        return True
        
    def create_media_cards(self):
        for  song in self.songs.get("results", []):
            card = self.createAudioCard(song, False)
            if card:
                self.addWidget(card)
            
        for album in self.albums.get("results", []):
            card = self.createPortraitAlbumCard(album)
            if card:
                self.is_album_empty = False
                self.artistAlbumsContainer.addWidget(card)
            
        for artist in self.related.get("results", []):
            card = self.createArtistCard(artist)
            if card:
                self.is_related_empty = False
                self.artistRelatedContainer.addWidget(card)
            
        for single in self.singles.get("results", []):
            card = self.createSinglesCard(single)
            if card:
                self.addWidget(card)
                
        self._toggle_container_visibility()        
        self.addWidget(self.artistAlbumsContainer)
        self.addWidget(self.artistRelatedContainer)
        self.set_cover_from_queue()
        self.uiLoaded.emit()
        
    def createSinglesCard(self, single):
        song_id = single.get("browseId", None)
        if song_id is None:
            logger.warning(f"Song id is None: {single}")
            return None
        title = single.get("title", "Unknown")
        album = "Singles"
        artist_name = self.getCardTitle()
        artist_id = self.getViewId()
        artists = {
            'name': artist_name,
            'id': artist_id
        }
        
        data = {
            "videoId": song_id,
            "title": title,
            "artists": [artists],
            "album": {"name": album},
            "duration": single.get("duration", None),
            "thumbnails": single.get("thumbnails", None)
        }
        
        
        card = AudioCard()
        card.setCardInfo(data, True)
        thumbnails = single.get("thumbnails", None)
        path = Path(ImageFolder.SONG.path) / f"{song_id}.png"
        if not path.exists():
            if thumbnails:
                self.thumbnails_downloader.download_thumbnail(thumbnails[-1].get("url", None), f"{song_id}.png", ImageFolder.SONG.path, song_id)
            else:
                logger.warning(f"No Thumbnail found for the: {song_id}")

        card.clicked.connect(lambda: self.audioCardClicked.emit(data))
        return card
                
    def _toggle_container_visibility(self):
        if self.is_album_empty:
            self.artistAlbumsContainer.hide()
        else:
            self.artistAlbumsContainer.show()
        if self.is_related_empty:
            self.artistRelatedContainer.hide()  
        else:
            self.artistRelatedContainer.show()      
    
    def get_tracks(self):
        return self.songs.get("results", [])
    