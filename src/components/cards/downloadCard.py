from qfluentwidgets import ImageLabel, BodyLabel, StrongBodyLabel, TitleLabel, TransparentToolButton, TransparentDropDownToolButton
from qfluentwidgets import FluentIcon, setCustomStyleSheet, setThemeColor, setTheme, Theme, ThemeColor
from qfluentwidgets import ProgressRing, CardWidget, SimpleCardWidget

import sys
sys.path.append(r'D:\Program\Musify')
from src.components.cards.audioCard import AudioCardBase
from src.common.myFrame import HorizontalFrame, VerticalFrame
from src.common.myButton import PrimaryRotatingButton
from src.common.myLabel import MyTitleLabel, MyBodyLabel
from src.utility.enums import PlaceHolder
from src.utility.iconManager import ThemedIcon

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QSize, Signal, QMimeData
from PySide6.QtGui import QFont, QColor, QDrag, QPixmap, QFontMetrics
from PySide6.QtWidgets import QGraphicsDropShadowEffect

from enum import Enum
from pathlib import Path

class DownloadStatus(Enum):
    DOWNLOADING = 0
    PAUSED = 1
    FINISHED = 2
    ERROR = 3
    READY = 4
    QUEUE = 5

class DownloadCard(SimpleCardWidget):
    deleteSignal = Signal()
    startSignal = Signal()
    pauseSignal = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("downloadCard")
        # self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cover_art = PlaceHolder.SONG.path
        self.download_status = DownloadStatus.READY
        self.request_id = None
        self.initUi()
        
        
    def initUi(self):
        self.setContentsMargins(6, 9, 9, 9)
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.cancel_button = TransparentToolButton(FluentIcon.CANCEL_MEDIUM, self)
        self.cancel_button.clicked.connect(self.deleteSignal.emit)
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cover_label = ImageLabel(self.cover_art, self)
        self.cover_label.setFixedSize(QSize(64, 64))
        self.cover_label.setBorderRadius(4, 4, 4, 4)
        self.cover_label.setStyleSheet('background: gray; border-radius: 4px;')
        
        self.info_container = VerticalFrame(self)
        self.info_container.setContentSpacing(0)
        self.info_container.setContentsMargins(10, 0, 0, 0)
        self.info_container.setLayoutMargins(0, 0, 0, 0)
        self.title_label = MyTitleLabel("Bitle", is_underline= False, parent= self.info_container)
        # self.title_label.setStyleSheet("background: red;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.download_info_container = HorizontalFrame(self.info_container)
        # self.download_info_container.setStyleSheet("background: red;")
        self.download_info_container.setContentsMargins(2, 0, 0, 0)
        self.download_info_container.setLayoutMargins(0, 0, 0, 0)
        self.download_info_container.setContentSpacing(0)
        self.current_download_label = BodyLabel("0%", parent= self.download_info_container)
        seperator = BodyLabel(" / ", parent= self.download_info_container)
        self.total_download_label = BodyLabel("0MB", parent= self.download_info_container)
        
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        self.download_info_container.addWidget(self.current_download_label)
        self.download_info_container.addWidget(seperator)
        self.download_info_container.addWidget(self.total_download_label)
        self.download_info_container.addSpacerItem(spacer)
        
        self.info_container.addWidget(self.title_label)
        self.info_container.addWidget(self.download_info_container)
        
        self.status_label = StrongBodyLabel("Ready", parent= self)
        
        self.play_pause_button = TransparentToolButton(ThemedIcon.PLAY_CIRCLE, self)
        self.play_pause_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_pause_button.setIconSize(QSize(32, 32))
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        
        self.progress_ring = ProgressRing(self)
        self.progress_ring.setRange(0, 100)
        self.progress_ring.setValue(0)
        self.progress_ring.setStrokeWidth(6)
        self.progress_ring.setFixedSize(QSize(30, 30))
        
        self.addWidget(self.cancel_button, alignment= Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.addWidget(self.cover_label, alignment= Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.addWidget(self.info_container, stretch= 1, alignment= Qt.AlignmentFlag.AlignVCenter)
        self.addWidget(self.status_label, alignment= Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.addWidget(self.play_pause_button, alignment= Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.addWidget(self.progress_ring, alignment= Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        
    def addWidget(self, widget, stretch: int = 0, alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft) -> None:
        self.main_layout.addWidget(widget, stretch, alignment)

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_download_percentages(self, percentage: float) -> None:
        percentage = min(percentage, 100)
        self.current_download_label.setText(f"{percentage:.0f}%")
        self.progress_ring.setValue(int(percentage))
        if percentage == 100:
            self.on_download_complete()

    def set_total_download(self, total: int, unit: str) -> None:
        self.total_download_label.setText(f"{total:.3f}{unit}")

    def toggle_play_pause(self) -> None:
        if self.download_status == DownloadStatus.DOWNLOADING:
            self.set_status(DownloadStatus.PAUSED)
            self.pauseSignal.emit()
        else:
            self.set_status(DownloadStatus.DOWNLOADING)
            self.startSignal.emit()

    def on_download_complete(self) -> None:
        self.set_status(DownloadStatus.FINISHED)

    def set_status(self, status: DownloadStatus) -> None:
        self.download_status = status
        status_map = {
            DownloadStatus.DOWNLOADING: ("Downloading...", ThemedIcon.PAUSE_CIRCLE, True, True),
            DownloadStatus.PAUSED: ("Paused", ThemedIcon.PLAY_CIRCLE, True, True),
            DownloadStatus.FINISHED: ("Completed", ThemedIcon.CHECK_BADGE, False, False),
            DownloadStatus.ERROR: ("Error", ThemedIcon.CHECK_BADGE, False, False),
            DownloadStatus.READY: ("Ready", ThemedIcon.PLAY_CIRCLE, True, True),
            DownloadStatus.QUEUE: ("Queued", ThemedIcon.PLAY_CIRCLE, False, False),
        }
        label, icon, enable_button, show_progress = status_map[status]
        self.status_label.setText(label)
        self.play_pause_button.setIcon(icon)
        self.play_pause_button.setEnabled(enable_button)
        self.progress_ring.setVisible(show_progress)
        if status == DownloadStatus.FINISHED:
            self.current_download_label.setText("100%")
                
    def set_cover(self, cover_path: str):
        if cover_path is None or not Path(cover_path).exists():
            return
        size = self.cover_label.size()
        self.cover_label.setImage(cover_path)
        self.cover_label.setFixedSize(size)
        
    def set_request_id(self, request_id: str):
        self.request_id = request_id
        
    def get_request_id(self):
        return self.request_id  
                
if(__name__ == "__main__"):
    app = QApplication(sys.argv)
    color = ThemeColor.DARK_1.color()
    print(color.name())
    # setTheme(Theme.DARK)
    # setThemeColor(ThemeColor.LIGHT_1)
    w = DownloadCard()
    w.set_title("This is the song title.")
    w.set_download_percentages(10)
    # w.set_total_download(100, "MB")
    w.show()
    app.exec()