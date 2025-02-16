
from qfluentwidgets import ImageLabel, SubtitleLabel, BodyLabel, StrongBodyLabel, TransparentToolButton, TransparentPushButton
from qfluentwidgets import FluentIcon, setCustomStyleSheet, PrimaryPushButton
from qfluentwidgets import SearchLineEdit, Pivot, ComboBox, FlowLayout, SimpleCardWidget, isDarkTheme
from qfluentwidgets import RoundMenu, Action


import sys
sys.path.append(r'D:\Program\Musify')

from loguru import logger

from src.common.myScroll import SideScrollWidget, HorizontalScrollWidget, VerticalScrollWidget
from src.common.myFrame import VerticalFrame, HorizontalFrame, FlowFrame
from src.components.cards.audioCard import AudioCard
from src.utility.iconManager import ThemedIcon
from src.utility.database_utility import DatabaseManager
from src.utility.misc import is_online_song


from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QMenu
from PySide6.QtCore import Qt, QSize, Signal, QPoint, QTimer, QUrl
from PySide6.QtGui import QFont, QColor, QPainter, QDropEvent, QDragEnterEvent, QAction
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QGraphicsBlurEffect
import json

from typing import NamedTuple
import random
import asyncio

from qasync import QEventLoop, asyncSlot, asyncClose



class MusicQueue(SimpleCardWidget):
    audioCardClicked = Signal(dict)
    selectionChanged = Signal(dict)
    def __init__(self, database_manager: DatabaseManager, parent=None):
        super().__init__(parent = parent)
        self.setObjectName("MusicQueue")
        
        self.setAcceptDrops(True)
        self.setContentsMargins(0, 0, 0, 0)
        
        self.database_manager = database_manager
        
        self.song_count = 1
        self.selected_card: AudioCard = None
        self.queue_id = None
        self.loaded_list = list()
        self.tracks = list()
        
        
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 9, 0, 0)
        self.initUi()
        
        self._setup_signal_handler()
        
        self.setObjectName("queue")
        # self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
    def _normalBackgroundColor(self):
        return QColor(25, 33, 42, 200) if isDarkTheme() else QColor(255, 255, 255, 230)
        
    def initUi(self):
        self.filters = HorizontalFrame(self)
        self.filters.setContentsMargins(15, 0, 0, 0)
        self.info_label = SubtitleLabel("0 Songs in Queue", self.filters)
        # self.info_label.setWordWrap(True)
        self.search_bar = SearchLineEdit(self.filters)
        self.search_bar.setFixedHeight(40)
        self.search_bar.setPlaceholderText("Search in Queue")
        self.clear_all_button = PrimaryPushButton(FluentIcon.DELETE, "Clear All", self.filters)
        
        self.filters.addWidgets([self.info_label, self.search_bar, self.clear_all_button])
        
        self.not_found_label = StrongBodyLabel(self)
        # self.not_found_label.setStyleSheet("background: red;")
        self.not_found_label.hide()
        
        self.scroll_area = VerticalScrollWidget()
        
        
        self.addWidget(self.filters, alignment= Qt.AlignmentFlag.AlignTop)
        self.addWidget(self.not_found_label, alignment= Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.addWidget(self.scroll_area)
        
    def addWidget(self, widget, stretch: int = 0, alignment: Qt.AlignmentFlag | None = None):
        try:
            if alignment is None:
                self.vBoxLayout.addWidget(widget, stretch)
            else:
                self.vBoxLayout.addWidget(widget, stretch, alignment)
        except TypeError:
            self.scroll_area.addWidget(widget)
        
    def _setup_signal_handler(self):
        self.clear_all_button.clicked.connect(self.clear_queue)
        self.search_bar.searchSignal.connect(self.search_queue)
        self.search_bar.clearSignal.connect(self.reset_search)
        self.search_bar.textChanged.connect(self.search_queue)
        self.scroll_area.scrollArea.verticalScrollBar().valueChanged.connect(self.on_scroll)
        
    def set_total(self, total):
        self.info_label.setText(f"{total} Songs in Queue")
        
    def setQueueData(self, queue_id: str, tracks: list, selected_idx: int = 0):
        if queue_id == self.queue_id:
            logger.info("Queue already loaded")
            if len(self.tracks)-1 < selected_idx:
                selected_idx = 0
            self.select_card_by_index(selected_idx)
            return
        self.song_count = 1
        self.loaded_list.clear()
        self.clear_queue()
        logger.info('Loading Queue')
        self.queue_id = queue_id
        self.tracks = tracks
        self.set_total(len(tracks))
        if len(self.tracks) < selected_idx:
            selected_idx = 0
        limit = self._calculate_limit(selected_idx)
        self._create_new_cards(self.tracks, 0, limit, selected_idx)
        
    def _calculate_limit(self, selected_idx: int):
        if selected_idx == 0:
            return 10
        return selected_idx + 5
        
    def _create_new_cards(self, tracks: list[dict], start = 0, limit: int = 10, selected_idx: int = 0):
        if self.song_count >= len(tracks):
            logger.debug(f"{self.song_count}>={len(tracks)}")
            return
        self.song_count = start + 1
        focus_card = None
        for index, track in enumerate(tracks[start:limit], start=start):
            card = self.createAudioCard(track)
            if card is not None:
                if selected_idx == index:
                    logger.info("Selected song found: ", selected_idx)
                    focus_card = card
                self.scroll_area.insertWidget(index, card)
            else:
                logger.debug(f"Song id is none: {track}-index{index}")
                
        logger.info(f"Loaded: {self.song_count - 1}")
        self.select_card(focus_card)
        
    def createAudioCard(self, audio, is_single: bool = False):
        # card.setSongId(songId)
        song_id = audio.get("videoId", None)
        if song_id is None or song_id in self.loaded_list:
            return None
        card = AudioCard(True)
        if card.setCardInfo(audio, is_single):
            self.loaded_list.append(song_id)
            card.setCount(self.song_count)
            self.song_count += 1
            card.clicked.connect(lambda: self.on_audio_clicked(card))
            menu = self._createMenuForAudioCard(card)
            card.setMenu(menu)
            return card

    def _createMenuForAudioCard(self, card):
        menu = RoundMenu(parent=card)
        menu.addAction(Action(FluentIcon.REMOVE, "Remove from Queue", parent = card, triggered= self.on_remove_song))
        menu.addAction(Action(FluentIcon.HEART, "Save to favorite", parent = card, triggered= self.on_save_to_fav))
        menu.addAction(Action(FluentIcon.ADD_TO, "Add to Playlist", parent = card, triggered= self.on_add_to_playlist))
        menu.addAction(Action(FluentIcon.ACCEPT_MEDIUM, "Send to top", parent = card, triggered= self.on_send_to_top))
        return menu
        
    def clear_queue(self):
        # self.shuffle_widgets()
        # logger.info(f"Next: {self.get_next_song().get('title')}")
        self.scroll_area.clear()
        self.song_count = 1
        self.set_total(0)
        self.queue_id = None
        self.selected_card = None
        
    def search_queue(self, text):
        # Step 1: Filter tracks based on search text
        matching_tracks = [track for track in self.tracks if text in track["title"].lower()]
        if len(matching_tracks) == 0:
            self.not_found_label.show()
            self.not_found_label.setText(f"No results found for '{text}' 😅")
            self.scroll_area.hide()
            return
        # print(matching_tracks)
        for i in range(self.scroll_area.count()):  # Get total number of items in layout
            item = self.scroll_area.itemAt(i)
            if item is not None:
                card = item.widget()
                if card and hasattr(card, "getTitle"):  # Ensure it's a widget and has getTitle method
                    if text.lower() in card.getTitle().lower():
                        card.show()
                    else:
                        card.hide()
        
        for track in matching_tracks:
            self.add_song(track)
            
    def reset_search(self):
        self.not_found_label.hide()
        self.scroll_area.show()
        for i in range(self.scroll_area.count()):
            self.scroll_area.itemAt(i).widget().show()
            
    def on_scroll(self, value):
        if self.song_count >= len(self.tracks):
            return
        if self.scroll_area.scrollArea.verticalScrollBar().maximum() - value < 100:
            limit = 5
            selected_idx = self.get_card_idx(self.selected_card)
            self._create_new_cards(self.tracks, self.song_count - 1, self.song_count + limit, selected_idx)
        
    def on_remove_song(self):
        logger.info("Remove song")
        card = self.sender().parent()
        self.scroll_area.removeWidget(card)
        self.update_count()
        card.deleteLater()    
        
    def on_add_to_playlist(self):
        logger.info("Add to playlist")
        
    def on_save_to_fav(self):
        logger.info("Save to favorite") 
    
    def on_send_to_top(self):
        card = self.sender().parent()
        # from layout
        self.scroll_area.removeWidget(card)
        self.scroll_area.insertWidget(0, card)
        
        #from queue elements
        logger.info("Send to top")
        self.update_count()
        
    def on_share(self):
        logger.info("Share")
        
    def on_song_link(self):
        logger.info("Song link")
        
    def on_audio_clicked(self, song_card: AudioCard):
        song_data = song_card.get_card_data()
        self.select_card(song_card)
        self.audioCardClicked.emit(song_data)
        
    def _generate_data_from_card(self, card: AudioCard):
        # print(card.getAuthor())
        return {
            'title': card.getTitle(),
            'artist': card.getAuthor(),
            'videoId': card.getAudioId(),
            'duration': card.getDuration(),
        }
                
    def get_card_idx(self, card):
        return self.scroll_area.indexOf(card)            
    
    def get_current_song(self):
        card = self.get_selected_card()
        return card.get_card_data()
    
    def get_next_song(self):
        current_idx = self.get_card_idx(self.selected_card)
        if current_idx + 1 < self.scroll_area.count():
            card: AudioCard = self.scroll_area.itemAt(current_idx + 1).widget()
            data = card.get_card_data()
            self.select_card(card)
            return data
        return None
    
    def get_previous_song(self)->dict|None:
        """_summary_

        Returns:
            
        """
        current_idx = self.get_card_idx(self.selected_card)
        logger.error(f"Current index: {current_idx}")
        if current_idx - 1 >= 0:
            card: AudioCard = self.scroll_area.itemAt(current_idx - 1).widget()
            data = card.get_card_data()
            self.select_card(card)
            return data
        return None
                
    def update_card(self, card: AudioCard, song_data):
        if card.setCardInfo(song_data, False):
            card.clicked.connect(lambda: self.on_audio_clicked(song_data))
            return True
        return False
    
    def add_song(self, song: dict, pos: int = -1, is_selected: bool = False):
        card = self.createAudioCard(song, True)
        if card is not None:
            if pos == -1 or pos >= self.scroll_area.count():
                pos = self.scroll_area.count()
            self.scroll_area.insertWidget(pos, card)
            self.update_count()
            self.tracks.append(song)
            if is_selected:
                self.select_card(card)
    
    def shuffle_widgets(self)->bool:
        widgets = [self.scroll_area.itemAt(i).widget() for i in range(self.scroll_area.count())]  # Exclude shuffle button
        if len(widgets) <= 1:
            return False
        #randomizing both seed and valid tracks so next song is based on shuffle.
        #seed to shuffle tracks also
        random.shuffle(widgets)

        # Remove all widgets from the layout
        for i in reversed(range(self.scroll_area.count())):
            widget = self.scroll_area.itemAt(i).widget()
            if widget:
                self.scroll_area.removeWidget(widget)
                # widget.hide()
                self.scroll_area.updateGeometry()   
            if widget.is_selected():
                selected_card = widget

        # Re-add widgets in new order
        for widget in widgets:
            self.scroll_area.addWidget(widget)
            
        self.update_count()
        return True
    
    def select_card(self, card: AudioCard):
        previous_card = self.get_selected_card()
        if card == previous_card  or card is None:
            return
        for index in range(self.scroll_area.count()):
            layout_card: AudioCard = self.scroll_area.itemAt(index).widget()
            if layout_card is card:
                # Avoid redundant state updates
                if  not card.is_selected():
                    card.set_selected(True)
                    self.selected_card = card
                # if previous_card < index:
                #     break
            else:
                if layout_card.is_selected():  # Only update if needed
                    layout_card.set_state(layout_card.AudioState.PAUSED)
                    layout_card.set_selected(False)
                    
        if card is not None:
            QTimer.singleShot(100, lambda: self.scroll_area.scrollArea.ensureWidgetVisible(card))
        
        if previous_card and previous_card != self.get_selected_card():
            logger.info(f"Selected card: {self.get_selected_card().getTitle()} - previos card: {previous_card.getTitle()}")
    
    def select_card_by_index(self, index: int):
        card = self.scroll_area.itemAt(index).widget()
        self.select_card(card)
                    
    def get_selected_card(self):
        return self.selected_card
            
    def update_count(self):
        for i in range(self.scroll_area.count()):
            card: AudioCard = self.scroll_area.itemAt(i).widget()
            card.setCount(i + 1)
            
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData() and event.source():
            logger.info("Drag enter event")
            event.accept()
        else:
            logger.info("Drag enter event not accepted")
            event.ignore()

    # Handle drop events
    def dropEvent(self, e):
        logger.info("Drop event")
        pos = e.position()  # Get the drop position
        widget = e.source()  # The dragged widget

        if not widget:
            logger.error("No valid widget source for drop event.")
            e.ignore()
            return

        widget_index = self.scroll_area.scrollContainer_layout.indexOf(widget)
        self.scroll_area.scrollContainer_layout.removeWidget(widget)

        n = 0
        for n in range(self.scroll_area.scrollContainer_layout.count()):
            # Get the widget at each index in turn.
            w = self.scroll_area.scrollContainer_layout.itemAt(n).widget()
            if pos.y() < w.y():
                # We didn't drag past this widget.
                logger.info(f"Dropping at the position: {n} - From: {widget_index}")
                break
        else:
            logger.info(f"Dropping widget at the bottom - From: {widget_index}")
            n += 1

        self.scroll_area.scrollContainer_layout.insertWidget(n, widget)

        
        e.accept()
        self.update_count()
        
    @asyncSlot()
    async def save_queue(self):
        if len(self.tracks) == 0:
            return
        await self.database_manager.clear_queue_songs()
        for position, track in enumerate(self.tracks, start=0):
            logger.debug(f"Saving Queue track: {track.get('title')}")
            song_id = track.get("videoId")
            path = track.get('path')
            if is_online_song(song_id):
                await self.database_manager.insert_song(track)
            else:
                await self.database_manager.insert_local_song(track)
            await self.database_manager.insert_queue_song(track.get("videoId"), position, path)
            # break
        
        logger.info("Queue saved")
            
    async def fetch_songs_queue(self, queue: asyncio.Queue):
        async def on_fetched(results):
            if not results:
                return
            self.set_total(len(results))
            
            for result in results:
                song_id = result["id"]
                path = result.get("path", "")
                if is_online_song(song_id):
                    song = await self.database_manager.get_song(result["id"])
                else:
                    song = await self.database_manager.get_local_song(result["id"])
                    song["path"] = path
                await queue.put(song)  # Push to queue

            await queue.put(None)  # Signal completion

        await self.database_manager.get_queue_songs(on_fetched)
        
    @asyncSlot()
    async def load_from_database(self):
        queue = asyncio.Queue()
        asyncio.create_task(self.fetch_songs_queue(queue))  # Run in background
        while True:
            song = await queue.get()
            if song is None:  # End of stream
                break
            await self.on_song_fetched(song)
            # break
        
    async def on_song_fetched(self, song):
        if song is not None:
            self.add_song(song)
            
    @asyncClose
    async def closeEvent(self, event):
        await self.save_queue()
        return super().closeEvent(event)
        
        
if(__name__ == "__main__"):
    app = QApplication(sys.argv)
    loop = QEventLoop()
    asyncio.set_event_loop(loop)
    
    app_exit_event = asyncio.Event()
    
    database_manager = DatabaseManager(r"data/user/database.db")
    window = MusicQueue(database_manager)
    # with open(r"D:\Program\Musify\data\app\playlist.json", "r") as f:
    #     data = json.load(f)
    
    # window.setQueueData("this(sid#", tracks=data.get("tracks", []), selected_idx=11)
    window.showMaximized()
    
    window.load_from_database()
    window.audioCardClicked.connect(print)
    app.aboutToQuit.connect(app_exit_event.set)
    app.aboutToQuit.connect(window.save_queue)
    
    with loop:
        loop.run_until_complete(app_exit_event.wait())
        
