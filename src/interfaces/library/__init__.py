__all__ = [
    'AlbumInterface',
    'PlaylistInterface',
    'ArtistInterface',
    'LocalInterface',
    'DownloadInterface',
]


# Interfaces for library components
# from .librarybase import LibraryInterfaceBase
from .albumInterface import AlbumInterface
from .playlistInterface import PlaylistInterface
from .artistInterface import ArtistInterface
from .localInterface import LocalInterface
from .downloadInterface import DownloadInterface
