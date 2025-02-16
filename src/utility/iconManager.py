from qfluentwidgets import FluentIconBase, Theme, Enum, getIconColor, setTheme
from qfluentwidgets import ToggleToolButton
from PySide6.QtWidgets import QApplication

class ThemedIcon(FluentIconBase, Enum):
    PLAYLIST =  "playlist" 
    QUEUE =  "queue" 
    FAV =  "favourite-star" 
    SHUFFLE =  "shuffle" 
    NEXT =  "next" 
    NEXT_ARROW =  "next-arrow" 
    NEXT_SOLID =  "next-solid"
    PREV_BK =  "previous-back" 
    PREV_ARROW =  "previous-arrow" 
    PREV_SOLID =  "previous-solid"
    PLAYBACK_SPEED =  "playback-speed"
    HEART_SOLID =  "heart"
    REPEAT =  "repeat" 
    LIKE =  "like" 
    DOWN_CHEVRON =  "down-chevron" 
    UP_CHEVRON =  "chevron-up" 
    PLAYLIST_MUSIC =  "playlist-2" 
    STATS =  "stats"
    MUSIC =  "music"
    PLAY_CIRCLE =  "play-circle"
    PAUSE_CIRCLE =  "pause-circle"
    CHECK_BADGE =  "check-badge"

    def path(self, theme=Theme.AUTO):
        # getIconColor() return "white" or "black" according to current theme
        return f'src/resources/icons/{getIconColor(theme)}/{self.value}-svgrepo-com.svg'
    
if(__name__ == "__main__"):
    app = QApplication([])
    setTheme(Theme.DARK)
    button = ToggleToolButton(ThemedIcon.PLAYLIST_MUSIC)
    button.show()
    app.exec()

