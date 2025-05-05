from qfluentwidgets import ImageLabel, BodyLabel, TitleLabel, setCustomStyleSheet
from qfluentwidgets import FlowLayout, SimpleCardWidget

import sys
sys.path.append('src')
# print(sys.path)


from src.common.myLabel import ClickableBodyLabel, MyTitleLabel

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QPushButton, QSizePolicy, QLabel
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QColor, QFontMetrics
from PySide6.QtWidgets import QGraphicsDropShadowEffect

class InfoCardBase(QFrame):
    clicked = Signal()
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setObjectName("infoCard")
        self.setFixedSize(180, 120)
        self.setupUi()
        self.setCursor(Qt.PointingHandCursor)
        
    def setupUi(self):
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.mainLayout.setContentsMargins(20, 9, 9, 9)
        
        self.statsContainer = QFrame(self)
        # self.statsContainer.setStyleSheet("background: red;")
        self.statsContainer.setContentsMargins(0, 0, 0, 0)
        self.statsContainer_layout = QHBoxLayout(self.statsContainer)
        self.statsContainer_layout.setContentsMargins(0, 0, 0, 0)
        self.statsContainer_layout.setAlignment(Qt.AlignLeft)
        self.statsContainer_layout.setSpacing(3)
        # self.statsContainer.setStyleSheet("background: transparent;")
        self.mainStats = TitleLabel("0", self.statsContainer)
        self.mainStats.setAlignment(Qt.AlignBottom)
        self.statsUnit = BodyLabel("minutes", self.statsContainer)
        self.statsUnit.setFont(QFont("Segoe UI", 12))
        self.statsUnit.setAlignment(Qt.AlignBottom)
        
        self.statsContainer_layout.addWidget(self.mainStats)
        self.statsContainer_layout.addWidget(self.statsUnit)
        
        
        self.statsDescription = BodyLabel("Listned to Music  for this song ", self)
        self.statsDescription.setWordWrap(True)
        self.statsDescription.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        # self.statsDescription.setStyleSheet("background: transparent;")
        
        self.mainLayout.addWidget(self.statsContainer)
        self.mainLayout.addWidget(self.statsDescription)
        
    def setMainStats(self, text):
        try:
            text = str(text)
            self.mainStats.setText(text)
        except ValueError:
            text = "0"
            self.mainStats.setText(text)

        
    def getMainStats(self)->str:
        return self.mainStats.text()
        
    def setMainStatsUnit(self, text):
        self.statsUnit.setText(text)
        
    def setStatsDescription(self, text):
        self.statsDescription.setText(text)
        
    def setBackgroundColor(self, color):
        self.setStyleSheet(f"background-color: {color}; border-radius: 8px;")
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        return super().mousePressEvent(event)
        
class DurationInfoCard(InfoCardBase):
    def __init__(self, parent = None):
        super().__init__(parent)
        # self.setMainStats("160")
        self.setMainStatsUnit("minutes")
        self.setStatsDescription("Listened to music")
        self.setBackgroundColor("#FBF5DD")
        
        
class SongsInfoCard(InfoCardBase):
    def __init__(self, parent = None):
        super().__init__(parent)
        # self.setMainStats("160")
        self.setMainStatsUnit("songs")
        self.setStatsDescription("Streamed overall")
        self.setBackgroundColor("#A6CDC6")
        
class ArtistsInfoCard(InfoCardBase):
    def __init__(self, parent = None):
        super().__init__(parent)
        # self.setMainStats("160")
        self.setMainStatsUnit("artists")
        self.setStatsDescription("Music reached you")
        self.setBackgroundColor("#16404D")
        
class AlbumsInfoCard(InfoCardBase):
    def __init__(self, parent = None):
        super().__init__(parent)
        # self.setMainStats("160")
        self.setMainStatsUnit("full albums")
        self.setStatsDescription("Got your love")
        self.setBackgroundColor("#DDA853")
        
class PlaylistsInfoCard(InfoCardBase):
    def __init__(self, parent = None):
        super().__init__(parent)
        # self.setMainStats("160")
        self.setMainStatsUnit("playlists")
        self.setStatsDescription("You explored")
        self.setBackgroundColor("#a49db3")
        
class LikedSongsInfoCard(InfoCardBase):
    def __init__(self, parent = None):
        super().__init__(parent)
        # self.setMainStats("160")
        self.setMainStatsUnit("favorites")
        self.setStatsDescription("That stayed")
        self.setBackgroundColor("#7D5260")


class DisplayStats(QFrame):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setObjectName("display")
        # self.setFixedSize(180, 120)
        self.setupUi()

    def setupUi(self):
        self.mainLayout = FlowLayout(self)
        self.mainLayout.setAlignment(Qt.AlignCenter)
        self.mainLayout.setHorizontalSpacing(10)
        self.mainLayout.setContentsMargins(20, 0, 0, 0)
        self.durationCard = DurationInfoCard(self)
        self.songsCard = SongsInfoCard(self)
        self.artistsCard = ArtistsInfoCard(self)
        self.albumsCard = AlbumsInfoCard(self)
        self.playlistsCard = PlaylistsInfoCard(self)
        self.likedSongsCard = LikedSongsInfoCard(self)
        
        
        self.mainLayout.addWidget(self.durationCard)
        self.mainLayout.addWidget(self.songsCard)
        self.mainLayout.addWidget(self.artistsCard)
        self.mainLayout.addWidget(self.albumsCard)
        self.mainLayout.addWidget(self.playlistsCard)
        self.mainLayout.addWidget(self.likedSongsCard)
        
    def setStats(self, stats):
        self.set_play_duration(stats['duration'])
        self.set_songs_count(stats['songs'])
        self.set_artists_count(stats['artists'])
        self.set_albums_count(stats['albums'])
        self.set_playlists_count(stats['playlists'])
        self.set_liked_songs_count(stats['likedSongs'])
        
    def set_play_duration(self, min: str):
        self.durationCard.setMainStats(min)
    
        
    def set_songs_count(self, count: str|int):
        if isinstance(count, int):
            count = str(count)
        self.songsCard.setMainStats(count)

    def get_songs_count(self)->int:
        return self.durationCard.getMainStats()

    def set_artists_count(self, count: str|int):
        if isinstance(count, int):
            count = str(count)
        self.artistsCard.setMainStats(count)

    def get_artists_count(self)->int:
        return self.artistsCard.getMainStats()

    def set_albums_count(self, count: str|int):
        if isinstance(count, int):
            count = str(count)
        self.albumsCard.setMainStats(count)

    def get_albums_count(self)->int:
        return self.albumsCard.getMainStats()

    def set_playlists_count(self, count: str|int):
        if isinstance(count, int):
            count = str(count)
        self.playlistsCard.setMainStats(count)

    def get_playlists_count(self)->int:
        return self.playlistsCard.getMainStats()

    def set_liked_songs_count(self, count: str|int):
        if isinstance(count, int):
            count = str(count)
        self.likedSongsCard.setMainStats(count)

    def get_liked_songs_count(self)->int:
        return self.likedSongsCard.getMainStats()

        
        
if(__name__ == '__main__'):
    app = QApplication(sys.argv)
    window = DisplayStats()
    # window.setStats({
    #     'duration': '160',
    #     'songs': '23',
    #     'artists': '11',
    #     'albums': '3',
    #     'playlists': '7',
    #     'likedSongs': '35'
    # })
    window.show()
    window.resize(180*7, 300)
    app.exec()