from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QWidget, QFrame
from PySide6.QtCore import QTimer, Qt, QRect
from PySide6.QtGui import QBrush, QLinearGradient, QPainter



class BaseSkeletonScreen(QFrame):
    def __init__(self, shimmer_speed=5, animation_interval=30, logical_width=200):
        super().__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.setInterval(animation_interval)

        self.shimmer_offset = 0
        self.shimmer_speed = shimmer_speed
        self.logical_width = logical_width  # Standard width for shimmer calculation

        self.setContentsMargins(0, 0, 0, 0)

    def update_animation(self):
        self.shimmer_offset += self.shimmer_speed
        if self.shimmer_offset > self.logical_width * 2:
            self.shimmer_offset = -self.logical_width
        self.update()

    def create_gradient(self):
        # Scale the shimmer_offset proportionally to the widget's width
        normalized_offset = (self.shimmer_offset / self.logical_width) * self.width()
        
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0.0, Qt.lightGray)
        gradient.setColorAt(0.5, Qt.white)
        gradient.setColorAt(1.0, Qt.lightGray)
        gradient.setStart(normalized_offset, 0)
        gradient.setFinalStop(normalized_offset + self.width() / 2, 0)
        return QBrush(gradient)

    def stop_animation(self):
        self.timer.stop()

    def start_animation(self):
        self.timer.start()


class RoundedSkeletonScreen(BaseSkeletonScreen):
    def __init__(self, radius, x=0, y=0):
        super().__init__()
        self.radius = radius
        self.x = x
        self.y = y

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.create_gradient())
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRect(self.x, self.y, self.radius * 2, self.radius * 2), self.radius, self.radius)
        
class RectSkeletonScreen(BaseSkeletonScreen):
    def __init__(self, width, height, x=0, y=0):
        super().__init__()
        self.rect_width = width
        self.rect_height = height
        self.pos_x = x
        self.pos_y = y

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.create_gradient())
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRect(self.pos_x, self.pos_y, self.rect_width, self.rect_height), 5, 5)
        # self.stop_animation()
    
        
    


class ExpandableRectSkeletonScreen(BaseSkeletonScreen):
    def __init__(self, x=0, y=0):
        super().__init__()
        self.pos_x = x
        self.pos_y = y

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.create_gradient())
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(
            QRect(self.pos_x, self.pos_y, self.width() - 20, self.height() - 20), 5, 5
        )


class HorizontalRectSkeletonScreen(BaseSkeletonScreen):
    def __init__(self, height, x=0, y=0):
        super().__init__()
        self.rect_height = height
        self.pos_x = x
        self.pos_y = y
        
        

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.create_gradient())
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(
            QRect(self.pos_x, self.pos_y, self.width(), self.rect_height), 5, 5)
        

class VerticalRectSkeletonScreen(BaseSkeletonScreen):
    def __init__(self, width, x=0, y=0):
        super().__init__()
        self.rect_width = width
        self.pos_x = x
        self.pos_y = y

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.create_gradient())
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(
            QRect(self.pos_x, self.pos_y, self.rect_width, self.height()), 5, 5
        )

        
if(__name__ == "__main__"):
    app = QApplication([])
    window = RectSkeletonScreen(224, 224)
    window.start_animation()
    window.show()
    app.exec()
