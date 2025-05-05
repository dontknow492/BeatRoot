import os
import sys

from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentIconBase, Theme, Enum, getIconColor


def resource_path(relative_path):
    """Return absolute path to resource. Compatible with dev and bundled modes."""
    if hasattr(sys, "_MEIPASS"):  # PyInstaller
        base_path = sys._MEIPASS
    elif getattr(sys, 'frozen', False):  # Nuitka
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

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
        # def path(self, theme=Theme.AUTO):
        icon_color = getIconColor(theme)
        relative_path = f'resources/icons/{icon_color}/{self.value}-svgrepo-com.svg'
        return resource_path(relative_path)
    
if(__name__ == "__main__"):
    app = QApplication([])
    print(resource_path())
    # setTheme(Theme.DARK)
    # button = ToggleToolButton(ThemedIcon.PLAYLIST_MUSIC.path())
    # button.show()
    app.exec()

