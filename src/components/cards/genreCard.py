import random
import sys
# print(sys.path)
from pathlib import Path

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QPainter
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QApplication, QVBoxLayout
from qfluentwidgets import SimpleCardWidget
from qfluentwidgets import TitleLabel


class SimpleGenreCard(SimpleCardWidget):
    def __init__(self, image_path: str | None, text: str, parent=None):
        super().__init__(parent)
        
        self.setCursor(Qt.PointingHandCursor)
        
        self.setLayout(QVBoxLayout())
        self.genreLabel = TitleLabel(text, self)
        
        self.layout().addWidget(self.genreLabel, alignment=Qt.AlignVCenter)
        
        if image_path and Path(image_path).exists():
            self.image = QPixmap(image_path)
            
        self.color = self.generate_random_color()
        # self.color.setAlpha(180)
        
        self.setFixedSize(220, 50)
            
    def setGenreId(self, id_: str):
        self.genreID = id_
        
    def getGenreId(self):
        return self.genreID
        
    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QPainter(self)
        if hasattr(self, 'image'):
            painter.drawPixmap(self.rect(), self.image)
        else:
            rect = QRect(0, 0, 10, self.height())
            painter.fillRect(rect, self.color)
            self.setContentsMargins(11, 0, 0, 0)
    
    @staticmethod        
    def generate_random_color():
        """Generates a random QColor."""
        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)
        return QColor(red, green, blue)
        
        
if(__name__ == "__main__"):
    # setTheme(Theme.DARK)
    app = QApplication(sys.argv)
    w = QFrame()
    w_layout = QVBoxLayout(w)
    w.setLayout(w_layout)
    w_layout.addWidget(SimpleGenreCard(r"/resources\images\image_.png", "hello"))
    # w = SimpleGenreCard(r"D:\Program\Musify\src\resources\images\image_.png", "hello")
    # w.
    w.show()
    app.exec()