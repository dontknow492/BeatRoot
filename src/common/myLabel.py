from qfluentwidgets import setCustomStyleSheet
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import setTheme, Theme, ToggleToolButton, BodyLabel, ImageLabel, TitleLabel, FluentLabelBase, FluentIconBase
from qfluentwidgets import Slider, TransparentToolButton, PrimaryToolButton, TransparentPushButton, TransparentDropDownToolButton
from qfluentwidgets import PillToolButton, getFont, FluentIcon


import sys
sys.path.append('src')

from typing import Union
# print(sys.path)
from src.utility.iconManager import ThemedIcon

from PySide6.QtWidgets import QFrame, QApplication
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QPixmap, QImage
from PySide6.QtGui import QFontMetrics, QMovie


class MyLabelBase(FluentLabelBase):
    
    def __init__(self, text: str, is_elided: bool = True, is_underline: bool = True, parent=None):
        super().__init__(parent)
        super().setText("str")
        self.setText(text)
        self.is_elided = is_elided
        if self.is_elided:
            self.setWordWrap(True)
        self.is_underline = is_underline
        if self.is_underline:
            self.setCursor(Qt.PointingHandCursor)
        self.font_metrics = QFontMetrics(self.font())
        
    def getFont(self):
        return getFont(14)
        
    def enterEvent(self, event):
        if self.is_underline:
            self.set_underline(state=True)
        return super().enterEvent(event)
    
    def leaveEvent(self, event):
        if self.is_underline:
            self.set_underline(state=False)
        return super().leaveEvent(event)
    
    def resizeEvent(self, event):
        if self.is_elided:
            self.set_elided_text(self.original_text)
        super().resizeEvent(event)
    
    def setText(self, arg__1):
        self.original_text = arg__1
        return super().setText(arg__1)
    
    def text(self):
        return self.original_text
    
    def set_elided_text(self, text: str):
        """
        Set the elided text for the label based on the available width.
        """
        font_metrics = QFontMetrics(self.font())
        elided_text = font_metrics.elidedText(text, Qt.TextElideMode.ElideRight, self.width())
        super().setText(elided_text)
        
    def set_underline(self, state: bool):
        font = self.font()
        font.setUnderline(state)
        self.setFont(font)

class MyBodyLabel(MyLabelBase):
    def __init__(self, text, is_elided: bool = True, is_underline: bool = True, parent=None):
        super().__init__(text, is_elided, is_underline, parent)
        
        
            
class MyTitleLabel(MyLabelBase):
    def __init__(self, text, is_elided: bool = True, is_underline: bool = True, parent=None):
        super().__init__(text, is_elided, is_underline, parent)
        
    def getFont(self):
        return getFont(28, QFont.DemiBold)
    
    
class ClickableLabel(MyLabelBase):
    clicked = Signal()
    def __init__(self, text, is_elided: bool = True, parent=None):
        super().__init__(text, is_elided, True, parent)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        # return super().mousePressEvent(event)
    
class ClickableBodyLabel(ClickableLabel):
    def __init__(self, text, is_elided: bool = True, parent=None):
        super().__init__(text, is_elided, parent)
    
class ClickableTitleLabel(MyTitleLabel):
    clicked = Signal()
    def __init__(self, text, is_elided: bool = True, parent=None):
        super().__init__(text, is_elided, parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        # return super().mousePressEvent(event)
            

class HoverOverlayImageLabel(ImageLabel):
    def __init__(self, image: Union[str, QPixmap, QImage] = None, icon: FluentIconBase = None, parent=None):
        super().__init__(parent = parent)
        if image:
            self.setImage(image)
        self.icon_label = ImageLabel(self)
        self.icon_label.setStyleSheet('background: none;')
        if icon:
            self.icon_label.setImage(icon.path())
        self.icon_label.setWindowFlag(Qt.WindowType.WindowDoesNotAcceptFocus | Qt.WindowType.WindowStaysOnTopHint)
        self.icon_label.setFixedSize(20, 20)
        self.icon_label.move(150, 150)
        self.icon_label.raise_()
        self.icon_label.hide()
        # self.overlay = QFrame(self)
        # self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.4);")
        # self.
        
    def setBorderRadius(self, topLeft: int, topRight: int, bottomLeft: int, bottomRight: int):
        if not hasattr(self, 'overlay'):
            self.overlay = QFrame(self)
            self.overlay.hide()
        self.overlay.setStyleSheet(f"""
            background-color: rgba(0, 0, 0, 0.4); 
            border-radius: {topLeft}px {topRight}px {bottomRight}px {bottomLeft}px;
        """)
        super().setBorderRadius(topLeft, topRight, bottomLeft, bottomRight)
        
    def enterEvent(self, event):
        self.icon_label.show()
        self.overlay.setGeometry(self.rect())
        self.overlay.setVisible(True)
        return super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.icon_label.hide()
        self.overlay.setVisible(False)
        return super().leaveEvent(event)
    
    def resizeEvent(self, event):
        self.icon_label.move(*self.find_center())
        return super().resizeEvent(event)
    
    def find_center(self):
        "find x, y where icon will be displayed"
        return (self.width() - self.icon_label.width()) // 2, (self.height() - self.icon_label.height()) // 2
    
    def set_overlay_icon(self, icon: FluentIconBase):
        size = self.icon_label.size()
        self.icon_label.setImage(icon.path())
        self.icon_label.setFixedSize(size)
        
    def set_icon_size(self, size: QSize):
        self.icon_label.setFixedSize(size)
        self.icon_label.move(*self.find_center())
        
    def set_movie(self, movie: QMovie):
        self.movie = movie
        self.icon_label.set_movie(movie)
        
    def start_movie(self):
        if hasattr(self, 'movie'):
            self.movie.start()
            # self.icon_label.show()
            
    def stop_movie(self):
        if hasattr(self, 'movie'):
            self.movie.stop()
            # self.icon_label.hide()
            
if(__name__ == "__main__"):
    app = QApplication([])
    w = HoverOverlayImageLabel(r"src\resources\images\image_2.png", FluentIcon.PLAY_SOLID)
    # w.setImage()
    w.setFixedSize(64, 64)
    w.show()
    app.exec()