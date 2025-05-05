import os
import sys
from enum import Enum
from pathlib import Path


def resource_path(relative_path):
    """Return absolute path to resource. Compatible with dev and bundled modes."""
    if hasattr(sys, "_MEIPASS"):  # PyInstaller
        base_path = sys._MEIPASS
    elif getattr(sys, 'frozen', False):  # Nuitka
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class DataPath(Enum):
    DATA_DIR = "data"
    APP_DATA_DIR = "app"
    HOMEPAGE = "home.json"
    RECENT = "recent.json"
    GENRE_CATEGORY = "genres.json"
    
    @property
    def getAbsPath(self):
        return f"{self.DATA_DIR.value}/{self.APP_DATA_DIR.value}/{self.value}"
    
    @property
    def getFullPath(self):
        return Path(__file__).parent.parent / self.getAbsPath
    

class SortType(Enum):
    A2Z = 1
    Z2A = 2
    NEWEST = 3
    OLDEST = 4
    DURATION = 5
    ARTIST = 6
    ALBUM = 7
    
    @property
    def description(self):
        # Direct mapping to a human-readable string
        descriptions = {
            SortType.A2Z: "Sort by A - Z",
            SortType.Z2A: "Sort by Z - A",
            SortType.NEWEST: "Sort by Newest",
            SortType.OLDEST: "Sort by Oldest",
            SortType.DURATION: "Sort by Duration",
            SortType.ARTIST: "Sort by Artist",
            SortType.ALBUM: "Sort by Album",
        }
        return descriptions[self]
    
    @classmethod
    def all_descriptions(cls):
        return {sort_type: sort_type.description for sort_type in cls}
    
    
from enum import Enum




#imagefolder
class ImageFolder(Enum):
    """
    An enumeration representing the path for the image of categories.
    """
    
    # Folder names inside the IMAGE_FOLDER
    IMAGE_DIR = r'.cache\thumbnail'
    ARTIST = "artist"
    ALBUM = "album"
    PLAYLIST = "playlist"
    SONG = "song"
    PLACEHOLDER = "placeholder"

    @property
    def path(self):
        # Join the base IMAGE_FOLDER path with the enum value (folder name)
        return f"{self.IMAGE_DIR.value}\\{self.value}"
    
class PlaceHolder(Enum):
    """Enum representing placeholder image paths."""
    ARTIST = "artist.jpg"
    ALBUM = "album.png"
    PLAYLIST = "playlist.png"
    SONG = "song.png"
    LYRICS = "lyrics.jpg"

    BASE_FOLDER = "resources/images/placeholder"

    @property
    def path(self):
        return resource_path(f"{self.BASE_FOLDER.value}/{self.value}")


#
class MusifyDefault(Enum):
    """
    An enumeration representing the default values for the Musify application.
    """
    # Default values for the Musify application
    DEFAULT_PORT = 5000
    DEFAULT_HOST = '127.0.0.1'
    DEFAULT_DEBUG = False
    DEFAULT_SECRET_KEY = 'musify_secret_key'
    DEFAULT_DATABASE_URI = 'sqlite:///musify.db'
    DEFAULT_DATABASE_TRACK_MODIFICATIONS = False
    
    DEFAULT_MEDIA_CARD_THUMBNAIL_PATH = Path(r'resources\images\image_2.png')
    
    @property
    def absolute_path(self):
        return self.value.absolute().__str__()
    
    
if(__name__ == "__main__"):
    print(ImageFolder.ALBUM.path)
    print(DataPath.HOMEPAGE.getFullPath)
    for sort_type in SortType:
        print(sort_type.description)
    