from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from PySide6.QtGui import QMovie, QIcon, QTransform, QPixmap
from PySide6.QtCore import QSize, Qt, QVariantAnimation
import sys

from qfluentwidgets import PrimaryPushButton, PrimaryToolButton, FluentIconBase, FluentIcon, Theme, isDarkTheme

from typing import overload, override

class GifPrimaryPushButton(PrimaryPushButton):
    def __init__(self, gif: str| QMovie, text: str|None = None, parent = None):
        super().__init__(parent)
        if isinstance(gif, str):
            self.movie = QMovie(gif)
        elif isinstance(gif, QMovie):
            self.movie = gif 
            
        self.text = text
        if text is not None:
            self.setText(text)    
        
        self.clicked.connect(self.toggle_gif)    
        
        self.movie.frameChanged.connect(self.update_icon)
        self.is_loading = False
        self.setIconSize(QSize(50, 50))

    def toggle_gif(self):
        if self.is_loading:
            self.stop_gif()
            self.is_loading = False
        else:
            self.start_gif()
            self.is_loading = True
    
    def start_gif(self, text: str| None = None):
        if text is not None:
            self.setText(text)
        else:
            self.setText("")
        # Set icon size
        self.movie.start()
        self.is_loading = True
        
    def stop_gif(self, text: str| None = None):
        self.movie.stop()
        if hasattr(self, 'stop_icon'):
            self.setIcon(self.stop_icon)
        else:
            self.setIcon(QIcon())  # Clear the icon
            
        if text is not None:
            self.setText(text)
        else:
            self.setText(self.text if self.text is not None else "")
        
        self.is_loading = False

    def update_icon(self):
        # Update the button's icon with the current frame of the GIF
        current_frame = self.movie.currentPixmap()
        self.setIcon(QIcon(current_frame))
    
    def setStopIcon(self, icon: QIcon):
        self.stop_icon = icon
        
        
class GifPrimaryToolButton(PrimaryToolButton):
    def __init__(self, icon: QIcon|str|FluentIconBase, gif: str| QMovie, parent = None):
        super().__init__(parent)
        self.setIcon(icon)
        self.primary_icon = icon
        
        if isinstance(gif, str):
            self.movie = QMovie(gif)
        elif isinstance(gif, QMovie):
            self.movie = gif 
        
        
        self.movie.frameChanged.connect(self.update_icon)
        self.is_loading = False
    
    def setGifSize(self, size: QSize):
        self.movie.setScaledSize(size)
    
    def start_gif(self):
        self.movie.start()
        self.is_loading = True
        
    def stop_gif(self):
        self.movie.stop()
        if hasattr(self, 'stop_icon'):
            self.setIcon(self.stop_icon)
        else:
            self.setIcon(self.primary_icon)
        
        self.is_loading = False

    def update_icon(self):
        # Update the button's icon with the current frame of the GIF
        current_frame = self.movie.currentPixmap()
        self.setIcon(QIcon(current_frame))
    
    def setStopIcon(self, icon: QIcon| str| FluentIconBase):
        self.stop_icon = icon
        
        
class PrimaryRotatingButton(PrimaryPushButton):
    def __init__(self, icon: QIcon | FluentIconBase, text: str, parent=None):
        super().__init__(parent=parent)
        
        
        if isinstance(icon, FluentIconBase):
            if isDarkTheme():
                print("yes")
                icon = icon.icon(Theme.LIGHT)
            else:
                print("no")
                icon = icon.icon(Theme.DARK)
        self.setIcon(icon)
        self.setText(text)
        
        self.animation = QVariantAnimation()
        self.animation.setDuration(1000)  # 1 second per full rotation
        self.animation.setStartValue(0)
        self.animation.setEndValue(360)
        self.animation.valueChanged.connect(self.update_icon)
        self.animation.setLoopCount(1)
        
        self.clicked.connect(self.start_rotation)
        
        # Store the original icon
        # if isinstance(icon, FluentIconBase):
        #     icon = icon.icon()
        self.original_icon = icon
        
    def set_animation(self, duration, loop_count):
        """Sets the animation duration and loop count."""
        self.animation.setDuration(duration)
        self.animation.setLoopCount(loop_count)

    def update_icon(self, angle):
        """Applies rotation to the icon."""
        transform = QTransform().rotate(angle)
        rotated_icon = self.original_icon.pixmap(32, 32).transformed(transform, Qt.SmoothTransformation)
        self.setIcon(QIcon(rotated_icon))

    def start_rotation(self):
        """Starts the rotation animation."""
        if self.animation.state() == QVariantAnimation.Stopped:
            self.animation.start()

    def stop_rotation(self):
        """Stops the rotation animation."""
        self.animation.stop()
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PrimaryRotatingButton(FluentIcon.HOME, "Home")
    window.setFixedSize(100, 100)
    # window = GifPrimaryToolButton(FluentIcon.HOME, gif = r"D:\Downloads\Images\loading-loading-forever.gif")
    # window.start_gif()
    # window.setStopIcon(FluentIcon.HOME_FILL)
    window.show()
    sys.exit(app.exec())
