from qfluentwidgets import ImageLabel, BodyLabel, TitleLabel, TransparentToolButton, TransparentDropDownToolButton
from qfluentwidgets import FluentIcon, setCustomStyleSheet, CardWidget, ElevatedCardWidget, SimpleCardWidget
from qfluentwidgets import SearchLineEdit, PrimaryPushButton

import sys
sys.path.append('d:\\Program\\Musify')

from src.common.myScroll import FlowScrollWidget, MyScrollWidgetBase, VerticalScrollWidget
from src.components.cards.portraitCard import PlaylistCard
from src.components.cards.downloadCard import DownloadCard, DownloadStatus
from src.interfaces.library.base import LibraryInterfaceBase
from src.utility.misc import is_online_song, get_audio_url, is_valid_youtube_url
from src.utility.downloader.song_downloader import SongDownloader
from src.utility.enums import ImageFolder

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect

from loguru import logger
from queue import Queue

class DownloadInterface(LibraryInterfaceBase):
    def __init__(self, parent = None):
        super().__init__(parent=parent)
        self.setObjectName("downloadInterface")
        
        self.song_downloader = SongDownloader(self)
        # self.song_downloader.start()
        self.download_dict = dict() #consist of request id, card
        #overideing
        self.scrollArea.deleteLater()
        self.scrollArea = VerticalScrollWidget(parent= self)
        self.scrollArea.setObjectName("scrollArea")
        self.addWidget(self.scrollArea)
        # self.setContentLayout(vBoxLayout)
        
        self.cancelAllButton = PrimaryPushButton(FluentIcon.CLOSE, 'Cancel All')
        self.addOption(self.cancelAllButton, alignment=Qt.AlignmentFlag.AlignRight)
        # self.optionContainer.setStyleSheet('background: red;')
        # self.scrollArea.setStyleSheet('background: green;')
        
        self._init_signal_handler()
        

    def _init_signal_handler(self):
        # Connect song downloader signals to handle download progress and completion
        self.song_downloader.download_progress_signal.connect(self._on_download_progress)
        self.song_downloader.download_complete_signal.connect(self._on_download_complete)
        self.song_downloader.download_error_signal.connect(self._on_download_error)
        self.cancelAllButton.clicked.connect(self._on_cancel_all)

    def _on_download_progress(self,   request_id: str, progress: float, total_size: float):
        # Update download progress on card
        logger.info(f"Download progress: {request_id}-{progress}")
        if request_id in self.download_dict.keys():
            card: DownloadCard = self.download_dict[request_id]
            card.set_download_percentages(progress)
            card.set_status(DownloadStatus.DOWNLOADING)
            card.set_total_download(self._byte_to_mb(total_size), "MB")

    def _on_download_complete(self, request_id: str):
        # Remove completed download card
        logger.info(f"Download complete: {request_id}")
        if request_id in self.download_dict.keys():
            card = self.download_dict[request_id]
            # self.removeCard(card)
            self.download_dict.pop(request_id)
            card.set_status(DownloadStatus.FINISHED)

    def _on_download_error(self, request_id: str, error: str):
        # Handle download error
        logger.error(f"Download error: {error}")
        if request_id in self.download_dict.keys():
            card = self.download_dict[request_id]
            card.set_error(error)
            self.download_dict.pop(request_id)
            card.set_status(DownloadStatus.ERROR)

    def _on_cancel_all(self):
        # Cancel all active downloads
        for request_id, card in self.download_dict.items():
            self.song_downloader.cancel_request(request_id)
            self.removeCard(card)
        self.download_dict.clear()   

    def add_download(self, video_id: str, title: str):
        download_url = get_audio_url(video_id)
        if not is_valid_youtube_url(download_url):
            logger.error(f"Invalid download url: {download_url}")
            return
        
        card = self._create_download_card(video_id, title)
        if card is None:
            return
        self.addCard(card)
        download_url = get_audio_url(video_id)
        request = self.song_downloader.add_request(download_url, r"D:\Program\Musify\data\downloads")
        self.download_dict[request] = card
        logger.info(f"Download added for {video_id}")
        
        
    def _create_download_card(self, video_id: str, title: str)->DownloadCard | None:
        if self.findChild(DownloadCard, f"{video_id}_card"):
            logger.error("Card already exists")
            return
        if video_id is None:
            logger.error("videoId is None")
            return
        cover_path = f"{ImageFolder.PLACEHOLDER.path}/{video_id}.png"
        card = DownloadCard()
        card.setObjectName(f"{video_id}_card")
        card.set_title(title)
        card.set_download_percentages(0)
        card.set_cover(cover_path)
        card.deleteSignal.connect(lambda: self.cancel_download(video_id))
        return card
    
    def cancel_download(self, video_id: str):
        card = self.findChild(DownloadCard, f"{video_id}_card")
        if card:
            self.removeCard(card)
        else:
            logger.error("Card not found")
            
    def _byte_to_mb(self, byte: float)->float:
        if not byte:
            return 0
        return byte / 1024 / 1024
            
    def closeEvent(self, event):
        # self.song_downloader.stop()
        self.song_downloader.shutdown()
        self.song_downloader.deleteLater()
        return super().closeEvent(event)
        
if(__name__ == '__main__'):
    app = QApplication(sys.argv)
    window = DownloadInterface()
    # for x in range(5):
    video_id = "YALvuUpY_b0"
    title = "Apna bane le piya"
    window.add_download(video_id, title)
    window.show()
    window.resize(800, 600)
    app.exec()
