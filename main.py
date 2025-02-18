from qfluentwidgets import FluentWindow, Theme, setTheme, setFont, SubtitleLabel, setThemeColor, ElevatedCardWidget, ScrollArea, SplashScreen
from qfluentwidgets import FluentIcon, NavigationItemPosition, setCustomStyleSheet
from qfluentwidgets import SimpleCardWidget, InfoBarPosition, MessageDialog, MessageBox, RoundMenu, Action

from PySide6.QtWidgets import QApplication, QFrame, QVBoxLayout, QGraphicsBlurEffect, QGraphicsPixmapItem, \
                            QWidget, QLabel, QGraphicsRectItem, QGraphicsScene, QGraphicsProxyWidget, QGraphicsView
from PySide6.QtCore import Qt, QObject, QTimer, QEventLoop as QtEventLoop, QCoreApplication, QPoint, Slot, QSize
from PySide6.QtGui import QColor, QMouseEvent, QCursor, QIcon
from PySide6.QtGui import QPainter, QPixmap, QBrush, QColor

from qasync import QEventLoop, asyncSlot, asyncClose

from src.utility.iconManager import ThemedIcon
from src.utility.check_net_connectivity import is_connected_to_internet
from src.utility.database_utility import DatabaseManager
from src.utility.misc import is_online_song
from src.common.infoBarMsg import InfoTime
from src.utility.enums import ImageFolder


from src.interfaces import (AlbumInterface, PlaylistInterface, ArtistInterface, DownloadInterface,
                            LocalInterface, StatsInterface)
from src.interfaces import HomeInterface
from src.interfaces import SearchInterface, SearchResultInterface, SearchResultSkeleton
from src.interfaces import LyricsInterface
from src.interfaces import GenrePlaylistsInterface, AllGenreInterface
from src.interfaces import PlaylistView, ArtistView, AudioView, AlbumView, ViewInterface
from src.interfaces import NoInternetWindow
from src.interfaces.view.localview import LocalView
from src.interfaces.music_queue import MusicQueue
from src.interfaces.playerInterface import PlayerInterface

from src.api import DataFetcherWorker, YTMusicMethod

import sys
import json
from loguru import logger
import json
import asyncio
from enum import Enum
import threading
import os

def get_resource_path(relative_path):
    """Get the absolute path to a resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Example: Load an icon
icon_path = get_resource_path("data/user/schema.sql")

class CardType(Enum):
    PLAYLIST = 1
    ARTIST = 2
    ALBUM = 3
    ONLINE_SONG = 4
    LOCAL_SONG = 5

class Widget(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QVBoxLayout(self)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))
        
        
class ViewManager:
    MAX_VIEW = 6

    def __init__(self, stacked_widget, data_fetcher, database_manager, parent=None):
        self.stacked_widget = stacked_widget
        self.data_fetcher = data_fetcher
        self.database_manager = database_manager
        self.view_stack = {}
        self.view_order = []  # Track order of views added
        self.parent = parent

    def add_view(self, view_class: ViewInterface, object_id, json_file_path, view_type, background: bool = False):
        """
        Generic method to add or switch to a view.

        :param view_class: The class of the view to create (e.g., PlaylistView, ArtistView).
        :param object_id: The unique ID for the view.
        :param json_file_path: Path to the JSON file containing data for the view.
        :param view_type: A string describing the type of view (e.g., "playlist", "artist").
        """
        logger.info(f"{view_type} time")

        # Check if view already exists
        view = self.view_stack.get(object_id)
        if view:
            logger.info(f"{view_type} view with ID {object_id} already exists")
            self.switch_to(view)
            return

        # Create the new view and add it
        view = self._create_view(view_class, object_id)
        
        if not view:
            logger.error(f"Failed to create view {object_id}")
            return

        self.view_stack[object_id] = view
        self.view_order.append(object_id)
        self.trim_view_stack()

    def _create_view(self, view_class: ViewInterface, object_id):
        """
        Creates and returns a new view.
        """
        logger.info(f"Creating view: {view_class.__name__} with ID: {object_id}")
        
        view = view_class(self.data_fetcher, self.database_manager, self.parent)
        view.setObjectName(object_id)

        view.fetch_data(object_id)
        
        self._add_view_signal(view, object_id)
        self.stacked_widget.addWidget(view)

    
        
        self.switch_to(view)

        return view  # ✅ Ensure the view is returned

    def trim_view_stack(self):
        """
        Removes the oldest view if the stack exceeds MAX_VIEW.
        """
        if len(self.view_order) > self.MAX_VIEW:
            oldest_view_id = self.view_order[0]  # Peek first item

            # ✅ Ensure we don’t remove the currently active view
            current_view = self.stacked_widget.currentWidget()
            if self.view_stack.get(oldest_view_id) == current_view:
                logger.info(f"Skipping removal of active view: {oldest_view_id}")
                return

            self.view_order.pop(0)
            view = self.view_stack.pop(oldest_view_id, None)

            if view:
                self.remove_view(view)
                
    def on_delete_view(self, view: ViewInterface):
        """
        Handle the deletion of a view.

        :param view: The view widget to be deleted.
        """
        for key, value in self.view_stack.items():
            if value is view:
                logger.info(f"Deleating view: {key}-{value}")
                self.view_order.remove(key)
                self.remove_view(view)
                self.view_stack.pop(key)
                break
            

    def remove_view(self, view: ViewInterface):
        """
        Remove a view from the stacked widget and the view stack.

        :param view: The view widget to remove.
        """
        if view in self.view_stack.values():
            self.stacked_widget.removeWidget(view)
            view.deleteLater()
            logger.info(f"View {view.objectName()} deleted successfully")  # ✅ Log message

    def _add_view_signal(self, view:ViewInterface, object_id):
        """
        Add signal handlers to the view.

        :param view: The view widget to add signal handlers to.
        """
        
        view.playlistCardClicked.connect(self.parent._add_playlist_view)
        view.artistClicked.connect(self.parent._add_artist_view)
        view.audioCardClicked.connect(self.parent.on_audioCardClicked)
        view.albumClicked.connect(self.parent._add_album_view)
        view.deleteSignal.connect(lambda: self.on_delete_view(view))

        if isinstance(view, PlaylistView):
            view.play.connect(lambda: self.parent.play_list(object_id, CardType.PLAYLIST))
            view.likeSignal.connect(self.parent.save_playlist)
            
        if isinstance(view, ArtistView):
            view.play.connect(lambda: self.parent.play_list(object_id, CardType.ARTIST))
            view.likeSignal.connect(self.parent.save_artist)
            
        if isinstance(view, AlbumView):
            view.play.connect(lambda: self.parent.play_list(object_id, CardType.ALBUM))
            view.likeSignal.connect(self.parent.save_album)
            
        # if isinstance(view, AudioView):
        #     view.play.connect(lambda: self.parent.play_track(object_id))

    def switch_to(self, view):
        """
        Switch to the specified view in the stacked widget.

        :param view: The view widget to switch to.
        """
        self.parent.switchTo(view)
        logger.info(f"Switched to view: {view.objectName()}")

    def get_view(self, view_id)->ViewInterface:
        """
        Retrieve a view by its ID.

        :param view_id: The ID of the view to retrieve.
        :return: The view widget if found, otherwise None.
        """
        return self.view_stack.get(view_id)
        
        
class LocalManager:
    def __init__(self, database_manager: DatabaseManager, parent=None):
        self.database_manager = database_manager
        self.parent = parent
        self.local_views = dict()

    def add_local_view(self, folder_id, folder_path):
        if folder_id in self.local_views.keys():
            self.parent.switchTo(self.local_views[folder_id])
            return
        local_view = LocalView(folder_id, folder_path, self.database_manager, self.parent)
        self.local_views[folder_id] = local_view
        self.parent.stackedWidget.addWidget(local_view)
        self.parent.switchTo(local_view)
        self.local_view_signal(local_view)
        
    def local_view_signal(self, local_view: LocalView):
        local_view.add_audio_to_queue.connect(self.parent.queue.add_song)
        local_view.play_dir.connect
        local_view.audioClicked.connect(self.parent.on_audioCardClicked)
        

class MainWindow(FluentWindow):
    def __init__(self, parent= None):
        super().__init__(parent)
        self.setWindowTitle("BeatRoot")
        self.setWindowIcon(QIcon("app.ico"))
        self.setWindowIcon
        
        self.datafetcher = DataFetcherWorker()
        self.datafetcher.error_occurred.connect(self.on_error_occurred)
        # starting 
        self.datafetcher.start()
        
        self.database_manager = DatabaseManager(r"data/user/database.db", self)
        
        self.info_msg_handler = InfoTime(self, pos=InfoBarPosition.BOTTOM, duration=2000)
        self.view_manager = ViewManager(self.stackedWidget, self.datafetcher, self.database_manager, self)
        self.local_view_manager = LocalManager(self.database_manager, self)
        # setup ui
        self.is_safe_to_close = False
        # to store task async
        # QTimer.singleShot(3000, self.initInterface)
        self.initInterface()
        # connecting signals
        self.signal_handler = SignalHandler(self)
        
        # self._load_last_played()
        # self._load_last_queue()
        
        
        
    def initInterface(self):
        
        self.homeInterface = HomeInterface(self.datafetcher, self)
        self.searchInterface = SearchInterface(self)
        self.searchResultInterface = SearchResultInterface(self.datafetcher, self)
        # self.searchResultInterface.setMaximumHeight(500)
        self.lyricsInterface = LyricsInterface(self.datafetcher, parent=self)
        
        #library interface and playlists
        self.libraryInterface = PlaylistInterface(self.database_manager, self)
        self.downloadsInterface = DownloadInterface(self)
        self.localInterface = LocalInterface(self.database_manager, self)
        self.artistInterface = ArtistInterface(self.database_manager, self)
        self.albumInterface = AlbumInterface(self.database_manager, self)
        
        #bottom interface
        self.statsInterface = StatsInterface(self.database_manager, self)
        self.settingsInterface = Widget("Settings", self)
        
        
        #interface which are extra, hidden on side bar, only visible when  option clicked
        self.genreViewInterface = AllGenreInterface(data_fetcher= self.datafetcher, parent= self)
        self.genrePLaylistViewInterface = GenrePlaylistsInterface(self.datafetcher, parent= None)
        self.noInternetInterface = NoInternetWindow(self)
        
        self.bottomPlayer = PlayerInterface(self.datafetcher, self.database_manager, self)
        self.bottomPlayer.setMaximumHeight(100)
        self.bottomPlayer.adjustSize()
        self.bottomPlayer.move(0, self.height())
        
        #queue
        self.queue = MusicQueue(self.database_manager, self)
        self.queue.setObjectName("queue")
        self.queue.hide()
        
        
        self.initNavigation()
        self.navigationSetup()
        # self.signalHandler()
        
        self.homeInterface._fetch_genres()
        self.homeInterface.load_home()
        
    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FluentIcon.HOME, "Browse")
        self.addSubInterface(self.searchInterface, FluentIcon.SEARCH, "Search")
        self.addSubInterface(self.lyricsInterface, FluentIcon.MUSIC, "Lyrics")
        self.navigationInterface.addSeparator()
        self.addSubInterface(self.libraryInterface, FluentIcon.BOOK_SHELF, "Library", NavigationItemPosition.SCROLL)
        self.addSubInterface(self.localInterface, FluentIcon.FOLDER, 'Local', parent=self.libraryInterface)
        self.addSubInterface(self.downloadsInterface, FluentIcon.DOWNLOAD, 'Downloads', parent=self.libraryInterface)
        self.addSubInterface(self.artistInterface, FluentIcon.PEOPLE, 'Artist', parent=self.libraryInterface)
        self.addSubInterface(self.albumInterface, FluentIcon.ALBUM, 'Album', parent=self.libraryInterface)
        
        self.navigationInterface.addSeparator(position= NavigationItemPosition.SCROLL)
        self.addSubInterface(self.statsInterface, ThemedIcon.STATS, "Stats", position=NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.settingsInterface, FluentIcon.SETTING, "Settings", position=NavigationItemPosition.BOTTOM)
        
        #extra interfaces
        
        
        # self.
        # self.stackedWidget.addWidget(self.playlistViewInterface)
        # self.stackedWidget.addWidget(self.albumViewInterface)
        # self.stackedWidget.addWidget(self.artistViewInterface)
        # self.stackedWidget.addWidget(self.audioViewInterface)
        self.stackedWidget.addWidget(self.genreViewInterface)
        self.stackedWidget.addWidget(self.genrePLaylistViewInterface)
        self.stackedWidget.addWidget(self.searchResultInterface)
        
        #adding no internet screen
        self.stackedWidget.addWidget(self.noInternetInterface)
        
    def navigationSetup(self):
        self.navigationInterface.setExpandWidth(275)
        self.navigationInterface.setCollapsible(False)
        self.navigationInterface.expand(useAni=False)
        self.navigationInterface.setAcrylicEnabled(True)
        self.navigationInterface.setMenuButtonVisible(False)
        
    def on_moreGenreClicked(self):
        logger.info("All genre button clicked")
        self.genreViewInterface._fetch_genres()
        self.switchTo(self.genreViewInterface)
        
        
    def _add_playlist_view(self, playlist_id):
        self.view_manager.add_view(
            PlaylistView, playlist_id, "data/app/playlist.json", "playlist"
        )

    def _add_artist_view(self, artist_id):
        logger.debug(f"Artist id: {artist_id}")
        self.view_manager.add_view(
            ArtistView, artist_id, "data/app/artist.json", "artist"
        )

    def _add_album_view(self, album_id):
        self.view_manager.add_view(
            AlbumView, album_id, "data/app/album.json", "album"
        )

    def _add_audio_view(self, audio_id):
        self.view_manager.add_view(
            AudioView, audio_id, "data/app/watch_playlist.json", "audio"
        )  
        
    def _add_folder_view(self, folder_id, folder_path):
        self.local_view_manager.add_local_view(folder_id, folder_path)
    
    
    def on_queue_clicked(self):
        
        if self.queue.isHidden():
            self.queue.setFocus()
            self.queue.show()
            # self.queue.setFocus()
        else:
            self.queue.hide()
        
    def on_genreSelected(self, genre_id):
        logger.info(genre_id)
        self.switchTo(self.genrePLaylistViewInterface)
        self.genrePLaylistViewInterface.load_genre(genre_id)
        # self.genrePLaylistViewInterface.load_genre_playlists(genre_id)
        # self.genrePLaylistViewInterface.loaded.connect(self.on_genre_playlist_loaded)
        
    def on_search(self, query):
        logger.info("Search Query is: ", query)
        if query == "":
            self.info_msg_handler.warning_msg("Empty search query", "Please enter a search query")
            logger.warning("Empty search query")
            return
        if not is_connected_to_internet:
            logger.warning("No internet connection")
            self.on_no_internet()
            return
        
        
        # with open("data/app/search.json", "r") as file:
        #     data = json.load(file)
        
        self.switchTo(self.searchResultInterface)
        self.searchResultInterface.load_search(query)
        # self.searchResultInterface._on_search_data_ready(data)
        # self.navigationInterface.expand(useAni=False)
        # self.update()
        
        # self.playlistViewInterface.load_data(playlist_id)
        
    @asyncSlot()
    async def _load_last_played(self):
        logger.info("Loading last played song")
        result = await self.database_manager.get_recent_songs()
        self.set_player_track(result)
        logger.info(f"Result: {result}")
        
    def _load_last_queue(self):
        logger.info("Loading last played Queue")
        self.queue.load_from_database()
        
    def set_player_track(self, track_data):
        title = track_data.get("title")
        artist = track_data.get("artists")
        if isinstance(artist, list):
            str_artist = ", ".join([artist.get("name") for artist in artist])
        elif isinstance(artist, str):
            str_artist = artist
        self.lyricsInterface.set_title(title)
        self.lyricsInterface.set_author(str_artist)
        
        cover = f"{ImageFolder.SONG.path}\\{track_data.get('videoId')}.png"
        # self.lyricsInterface.setBackgroundImage()
        QTimer.singleShot(1000, lambda: self.lyricsInterface.setBackgroundImage(cover))
        self.lyricsInterface.start_animation()
        self.bottomPlayer.set_song(track_data)
        
    def set_queue_data(self, id_: str, tracks: dict, selected_idx: int = 0):
        self.queue.setQueueData(id_, tracks, selected_idx)
        
    def on_queue_song_change(self, song_data):
        logger.info("queue song change")
        self.set_player_track(song_data)
        
    def on_audioCardClicked(self, track_data, index: int = 0):
        track_id  =  track_data.get('videoId')
        logger.info(f"Track id: {track_id}")
        from_playlist = (AudioView, PlaylistView, AlbumView)
        
        sender_widget = self.sender()
        logger.debug(f"Sender: {sender_widget}")
        if  isinstance(sender_widget, from_playlist):
            id_ = sender_widget.get_id()
            logger.info("Playing playlist")
            self.info_msg_handler.success_msg("Loading playlist", "Loading playlist to queue")
            logger.debug(f"id: {id_}")
            self.set_queue_data(id_, sender_widget.get_tracks())
        if isinstance(sender_widget, LocalView):
            id_ = sender_widget.get_id()
            logger.info("Playling playlist")
            self.info_msg_handler.success_msg("Loading playlist", "Loading playlist to queue")
            self.set_queue_data(id_, sender_widget.get_tracks(), index)
            self.set_player_track(track_data)
    
    
    @asyncSlot()
    async def play_track(self, audio_data: dict, fetch_watch_playlist: bool = True):
        logger.info("play track")
        self.set_player_track(audio_data)
        track_id = audio_data.get('videoId')
        is_local = not is_online_song(track_id)
        def watch_playlist_fetched(data, uid):
            if uid != request_id:
                return
            if data is None:
                self.info_msg_handler.warning_msg("Song", "Song not found")
                return
            qid = data.get("playlistId")
            tracks = data.get("tracks", [])
            selected = 0
            self.queue.clear_queue()
            QTimer.singleShot(2000, lambda: self.set_queue(qid, tracks, selected))
            
        if fetch_watch_playlist and not is_local:
            self.datafetcher.data_fetched.connect(watch_playlist_fetched)
            request_id = self.datafetcher.add_request(YTMusicMethod.GET_WATCH_PLAYLIST, audio_data.get("videoId"))
        asyncio.create_task(self.database_manager.insert_song(audio_data))
    
    @asyncSlot()
    async def save_track(self, audio_data: dict, is_local: bool = False, path: str = 'ytmusic'):
        logger.info("Save Track")
        if is_local:
            pass
            # await self.database_manager.insert_local_directory(path, audio_data.get("path"))
        else:
            logger.debug(f'Audio: {audio_data}')
            await self.database_manager.insert_song(audio_data)
        
    @asyncSlot()
    async def track_liked(self, audio_data, is_local: bool = False, path: str = 'ytmusic'):
        logger.info("add to liked")
        await self.save_track(self, audio_data)
        asyncio.create_task(self.database_manager.insert_liked_song(audio_data.get("videoId")))
        self.info_msg_handler.success_msg("Liked", "Song added to liked")
    
    @asyncSlot()
    async def track_liked_id(self, song_id):
        logger.info("add to liked")
        await self.database_manager.insert_liked_song(song_id)
        self.info_msg_handler.success_msg("Liked", "Song added to liked")
    
    @asyncSlot()
    async def track_unliked_id(self, song_id):
        logger.info("remove from liked")
    
    @Slot()        
    def play_list(self, fetch_id, type_: CardType):
        logger.info("play list")
        def list_fetched(data, uid):
            if uid != request_id:
                return
            if data is None:
                self.info_msg_handler.warning_msg("Playlist", "Playlist not found")
                return
            tracks = data.get("tracks", [])
            selected = 0
            track = tracks[selected]
            self.play_track(track, False)
            self.set_queue(fetch_id, tracks, selected)
            
        self.datafetcher.data_fetched.connect(list_fetched)
        if type_ == CardType.PLAYLIST:
            request_id = self.datafetcher.add_request(YTMusicMethod.GET_PLAYLIST, fetch_id)
        elif type_ == CardType.ALBUM:
            request_id = self.datafetcher.add_request(YTMusicMethod.GET_ALBUM, fetch_id)
        elif type_ == CardType.ARTIST:
            request_id = self.datafetcher.add_request(YTMusicMethod.GET_ARTIST, fetch_id)
        
    @asyncSlot()    
    async def save_playlist(self, playlist_data):
        @asyncSlot()
        async def playlist_fetched(data, uid):
            if uid != request_id:
                return
            if data is None:
                self.info_msg_handler.warning_msg("Playlist", "Playlist not found")
                return
            tracks = data.get("tracks", [])
            for index, track in enumerate(tracks, start= 0):
                await self.database_manager.insert_song(track)
                asyncio.create_task(self.database_manager.insert_playlist_song(playlist_data.get("id"), track.get("videoId"), index))
        
        # cover_art = 
        await self.database_manager.insert_playlist(playlist_data)
        self.datafetcher.data_fetched.connect(playlist_fetched)
        request_id = self.datafetcher.add_request(YTMusicMethod.GET_PLAYLIST, playlist_data.get('id'))
        
    @asyncSlot()
    async def save_artist(self, artist_data: dict):
        await self.database_manager.insert_artist(artist_data)
        asyncio.create_task(self.database_manager.insert_liked_artist(artist_data.get("id")))
        
    @asyncSlot()
    async def save_album(self, album_data: dict):
        await self.database_manager.insert_album(album_data)
        asyncio.create_task(self.database_manager.insert_liked_album(album_data.get("id")))
        
    def set_queue(self, qid: str, tracks: list, selected: int):
        self.set_queue_data(qid, tracks, selected)
        
    def add_to_playlist(self, audio_id):
        logger.info("add to playlist")
        self.info_msg_handler.success_msg("Playlist", "Song added to playlist")
        # asyncio.create_task(self.database_manager.insert_playlist_song(playlist_id, audio_id, 0))
        
    @asyncSlot()    
    async def show_playlist_dialog(self, playlists):
        dialog = MessageBox("Add to playlist", "Select a playlist to add to", self)
        future = asyncio.Future()

        def on_finished():
            if not future.done():
                future.set_result(None)

        dialog.finished.connect(on_finished)
        dialog.open()  # Open the dialog non-blocking
        await future
        # dialog.open()  # Open non-blocking dialog

    def on_next_clicked(self):
        logger.info("next clicked")
        song_data = self.queue.get_next_song()
        if song_data is None:
            self.info_msg_handler.warning_msg("No song", "No next song in queue")
            logger.warning("No next song in queue")
            return
        self.set_player_track(song_data)  
        
    def on_prev_clicked(self):
        logger.info("prev clicked")
        song_data = self.queue.get_previous_song()
        if song_data is None:
            self.info_msg_handler.warning_msg("No song", "No previous song in queue")
            logger.warning("No previous song in queue")
            return
        self.set_player_track(song_data)  
        
    def on_like_clicked(self):
        logger.info("like clicked")
        
    def on_shuffle_clicked(self):
        logger.info("shuffle clicked")
        if self.queue.shuffle_widgets():
            self.info_msg_handler.success_msg("Shuffled", "Queue shuffled")
            logger.success("Queue shuffled")
        else:
            self.bottomPlayer.shuffleButton.blockSignals(True)
            self.bottomPlayer.set_shuffle(False)
            self.bottomPlayer.shuffleButton.blockSignals(False)
            self.info_msg_handler.warning_msg("No songs", "No songs in queue")
            logger.warning("No songs in queue")
        
    def on_download_clicked(self):
        logger.info("download clicked") 
        
    def on_error_occurred(self, error):
        logger.error(error)
        self.info_msg_handler.error_msg("Error", error)
        dialog = MessageBox("Error", error, self)
        dialog.exec()
        self._return_to_previous()    
    
    def _return_to_previous(self):
        # self.switchTo(self.navigationInterface.panel.history[-2].widget
        self.navigationInterface.panel.history.pop()
        
    def on_no_internet(self):
        self.switchTo(self.noInternetInterface)
        self.info_msg_handler.warning_msg("No internet", "No internet connection")
        
    def resizeEvent(self, e):
        
        
        # if hasattr(self, 'bottomPlayer'):
        self.bottomPlayer.move(0, self.height() - self.bottomPlayer.height())
        self.bottomPlayer.resize(self.width(), self.bottomPlayer.height())   
        
        
        width = int(self.stackedWidget.width()/100 * 70)
        height = self.titleBar.height()
        self.queue.setFixedSize(width, self.stackedWidget.height() + 2)
        self.queue.move(self.width() - self.queue.width(), height)
        super().resizeEvent(e)
        
    @asyncClose
    async def closeEvent(self, event):
        await self.queue.save_queue()
        await self.database_manager.close()
        self.datafetcher.stop()
        self.datafetcher.exit(0)
        self.bottomPlayer.stop()
        self.bottomPlayer.deleteLater()
        self.datafetcher.deleteLater()
        self.info_msg_handler.deleteLater()
        self.thread().deleteLater()
        self.deleteLater()
        super().closeEvent(event)
        # self.stop_threads()
        
    

class SignalHandler(QObject):
    def __init__(self, ui: MainWindow):
        super().__init__()
        self.ui = ui  # Pass the main UI reference
        self.connect_signals()
    
    def connect_signals(self):
        self._home_signals()
        self._search_signals()
        self._genre_view_signals()
        self._player_signals()
        self._queue_signals()
        self._library_signals()
        self._stats_signals()
        # self._db_signals()
    
    def _home_signals(self):
        home = self.ui.homeInterface
        home.moreGenreClicked.connect(self.ui.on_moreGenreClicked)
        home.noInternet.connect(self.ui.on_no_internet)
        home.genreSelected.connect(self.ui.on_genreSelected)
        home.audioCardClicked.connect(self.ui._add_audio_view)
        home.artistCardClicked.connect(self.ui._add_artist_view)
        home.albumCardClicked.connect(self.ui._add_artist_view)
        home.playlistCardClicked.connect(self.ui._add_playlist_view)
        home.audioPlayClicked.connect(lambda audio_data: self.ui.play_track(audio_data, True))
        home.playlistPlayClicked.connect(lambda playlist_id: self.ui.play_list(playlist_id, CardType.PLAYLIST))
        home.albumPlayClicked.connect(lambda album_id: self.ui.play_list(album_id, CardType.ALBUM))
        home.audioAddToPlaylistClicked.connect(self.ui.save_track)
        home.playlistAddtoClicked.connect(self.ui.save_playlist)
        home.albumAddtoClicked.connect(self.ui.save_album)

    def _search_signals(self):
        search = self.ui.searchInterface
        search.searchSignal.connect(self.ui.on_search)
        self.ui.searchResultInterface.noInternet.connect(self.ui.on_no_internet)
        self.ui.searchResultInterface.audioCardClicked.connect(lambda audio_data: self.ui.play_track(audio_data, True))
        self.ui.searchResultInterface.artistCardClicked.connect(self.ui._add_artist_view)
        self.ui.searchResultInterface.albumCardClicked.connect(self.ui._add_album_view)
        self.ui.searchResultInterface.playlistCardClicked.connect(self.ui._add_playlist_view)
        self.ui.searchResultInterface.playlistPlayClicked.connect(lambda playlist_id: self.ui.play_list(playlist_id, CardType.PLAYLIST))
        self.ui.searchResultInterface.albumPlayClicked.connect(lambda album_id: self.ui.play_list(album_id, CardType.ALBUM))
        self.ui.searchResultInterface.playlistAddtoClicked.connect(self.ui.save_playlist)
        self.ui.searchResultInterface.albumAddtoClicked.connect(self.ui.save_album)

    def _genre_view_signals(self):
        ui = self.ui  # Short alias
        ui.genreViewInterface.noInternet.connect(ui.on_no_internet)
        ui.genreViewInterface.genreSelected.connect(ui.on_genreSelected)
        ui.genrePLaylistViewInterface.noInternet.connect(ui.on_no_internet)
        ui.genrePLaylistViewInterface.playlistCardClicked.connect(ui._add_playlist_view)

    def _player_signals(self):
        player:PlayerInterface = self.ui.bottomPlayer
        player.nextClicked.connect(self.ui.on_next_clicked)
        player.prevClicked.connect(self.ui.on_prev_clicked)
        player.shuffleClicked.connect(self.ui.on_shuffle_clicked)
        player.queuesClicked.connect(self.ui.on_queue_clicked)
        player.likedSignal.connect(self.ui.track_liked_id)
        player.unlikeSignal.connect(self.ui.track_unliked_id)
        player.downloadClicked.connect(self.ui.on_download_clicked)

    def _queue_signals(self):
        self.ui.queue.audioCardClicked.connect(lambda song_data: self.ui.bottomPlayer.set_song(song_data))

    def _dynamic_view_signal(self, view):
        view.audioCardClicked.connect(self.ui.on_audioPlayClicked)
        view.artistCardClicked.connect(self.ui.on_artistCardClicked)
        view.albumCardClicked.connect(self.ui.on_albumCardClicked)
        view.playlistCardClicked.connect(self.ui.on_playlistCardClicked)
        
    def _library_signals(self):
        
        artist = self.ui.artistInterface
        artist.artistClicked.connect(self.ui._add_artist_view) 
        
        album = self.ui.albumInterface
        album.albumClicked.connect(self.ui._add_album_view)
        album.albumPlayClicked.connect(lambda album_id: self.ui.play_list(album_id, CardType.ALBUM))
        
        local = self.ui.localInterface
        local.directoryClicked.connect(self.ui._add_folder_view)
    
    def _stats_signals(self):
        stats = self.ui.statsInterface
        stats.albumClicked.connect(self.ui._add_album_view)
        stats.artistClicked.connect(self.ui._add_artist_view)
        stats.audioClicked.connect(self.ui._add_audio_view)



def main():
    # setTheme(Theme.DARK)
    # Configure logging
    logger.add("logs/app.log", rotation="1 week", level="DEBUG", encoding="utf-8", backtrace=True, diagnose=True)
    logger.info("App started")

    # Create the Qt application
    app = QApplication(sys.argv)
    # app icon
    app.setWindowIcon(QIcon("app.ico"))
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)  # Set the event loop for asyncio

    # Create the main window
    splash_screen = SplashScreen(FluentIcon.FULL_SCREEN)
    splash_screen.setWindowFlag(Qt.WindowType.FramelessWindowHint)
    splash_screen.setWindowState(Qt.WindowState.WindowMaximized)
    # splash_screen.show()
    
    window = MainWindow()
    # window.setWindowState(Qt.WindowState.WindowFullScreen)
    window.setContentsMargins(0, 0, 0, 98)
    window.move(100, 100)
    window.showMaximized()
    # window.showFullScreen()

    
    # Create an event to signal app closure
    app_close_event = asyncio.Event()

    app.aboutToQuit.connect(app_close_event.set)

    logger.critical(f"Size: {window.geometry()}")
    # Run the Qt event loop
    with loop:
        try:
            # Wait for the app_close_event to be set
            loop.run_until_complete(app_close_event.wait())
        except asyncio.CancelledError:
            logger.info("Application shutdown requested.")

    
    logger.debug("loop ends")
    # loop.close()
    print("this is real end")
    # Explicitly quit the QApplication
    # app.quit()
    



if __name__ == "__main__":
    main()