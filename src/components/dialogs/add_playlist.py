from qfluentwidgets import ImageLabel, BodyLabel, TitleLabel, TransparentToolButton, TransparentPushButton, PushButton
from qfluentwidgets import SubtitleLabel, PrimaryPushButton, FluentIcon, Dialog, LineEdit, TextEdit
from qfluentwidgets import SearchLineEdit, Pivot, ComboBox, FlowLayout, OpacityAniStackedWidget
from qframelesswindow import FramelessDialog


import sys
sys.path.append(r'D:\Program\Musify')
from pathlib import Path

from src.common.myScroll import SideScrollWidget, HorizontalScrollWidget, VerticalScrollWidget
from src.common.myFrame import VerticalFrame, HorizontalFrame, FlowFrame


from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy, QStackedWidget, QFileDialog
from PySide6.QtCore import Qt, QSize, Signal, QTimer, QParallelAnimationGroup
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect
import json


class AddPlaylistDialog(FramelessDialog):
    confirmed = Signal(str, str, str)
    cancelled = Signal()
    def __init__(self, parent=None):
        super().__init__(parent = parent)
        
        
        self.cover_path = None
        # self.titleBar.hide()
        
        self.vBoxLayout = QVBoxLayout(self)
        
        self.initUi()
        self._signal_connect()
        self._setup_cursor()
        # self.setShadowEffect()
        
    def initUi(self):
        self.titleLabel = TitleLabel("Create playlist", self)
        
        self.coverImage = ImageLabel(r"D:\Program\Musify\src\resources\images\image_2.png", self)
        self.coverImage.setFixedSize(180, 180)
        self.coverImage.setBorderRadius(10, 10, 10, 10)
        
        self.optionContainer = HorizontalFrame(self)
        self.addCoverButton = PrimaryPushButton(FluentIcon.ADD, "Add cover", self.optionContainer)
        self.removeCoverButton = TransparentToolButton(FluentIcon.DELETE, self.optionContainer)
        self.removeCoverButton.setToolTip("Remove Cover")
        self.optionContainer.addWidget(self.addCoverButton)
        self.optionContainer.addWidget(self.removeCoverButton)
        
        self.playlistName = LineEdit(self)
        self.playlistName.setPlaceholderText("Name of the playlist")
        self.playlistName.setMinimumHeight(40)
        
        self.description = TextEdit(self)
        self.description.setPlaceholderText("Description")
        
        self.dialogOptionContainer = HorizontalFrame(self)
        self.cancelButton = PushButton("Cancel", self.dialogOptionContainer)
        self.confirmButton = PrimaryPushButton("Create", self.dialogOptionContainer)
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.dialogOptionContainer.addSpacerItem(spacer)
        self.dialogOptionContainer.addWidget(self.cancelButton, alignment=Qt.AlignRight)
        self.dialogOptionContainer.addWidget(self.confirmButton, alignment=Qt.AlignRight)
        
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.coverImage, alignment=Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.optionContainer, alignment=Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.playlistName)
        self.vBoxLayout.addWidget(self.description)
        self.vBoxLayout.addWidget(self.dialogOptionContainer)
        
    def _signal_connect(self):
        self.addCoverButton.clicked.connect(self.on_add_cover)
        self.removeCoverButton.clicked.connect(self.remove_cover_image)
        self.cancelButton.clicked.connect(self.on_cancel)
        self.confirmButton.clicked.connect(self.on_confirm) 
        
    def _setup_cursor(self):
        self.addCoverButton.setCursor(Qt.PointingHandCursor)
        self.removeCoverButton.setCursor(Qt.PointingHandCursor)
        self.cancelButton.setCursor(Qt.PointingHandCursor)
        self.confirmButton.setCursor(Qt.PointingHandCursor)
        
    def on_add_cover(self):
        self.filepicker = QFileDialog(self)
        self.filepicker.setWindowTitle("Select an Image File")
        self.filepicker.setNameFilter("Images (*.png *.jpg *.jpeg)")
        self.filepicker.setFileMode(QFileDialog.ExistingFile)
        self.filepicker.fileSelected.connect(self.set_cover_image)
        self.filepicker.exec()
        
    def set_cover_image(self, file_path):
        self.cover_path = file_path
        self.coverImage.setImage(file_path)
        self.coverImage.setFixedSize(175, 175)
        
    def remove_cover_image(self):
        self.cover_path = None
        self.coverImage.setImage(r"D:\Program\Musify\src\resources\images\image_2.png")
        self.coverImage.setFixedSize(180, 180)
        
    def setShadowEffect(self, blurRadius=60, offset=(0, 10), color=QColor(0, 0, 0, 100)):
        """ add shadow to dialog """
        shadowEffect = QGraphicsDropShadowEffect(self)
        shadowEffect.setBlurRadius(blurRadius)
        shadowEffect.setOffset(*offset)
        shadowEffect.setColor(color)
        self.setGraphicsEffect(None)
        self.setGraphicsEffect(shadowEffect)
        
    def on_cancel(self):
        self.close()
        
    def on_confirm(self):
        self.confirmed.emit(self.playlistName.text(), self.description.toPlainText(), self.cover_path)
        self.close()
        
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = AddPlaylistDialog()
    w.show()
    app.exec()
