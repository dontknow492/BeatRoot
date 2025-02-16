from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect



def blur_pixmap(pixmap: QPixmap, blur_radius: float) -> QPixmap:
        """Apply a blur effect to the given pixmap."""
        scene = QGraphicsScene()
        item = QGraphicsPixmapItem(pixmap)
        scene.addItem(item)

        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(blur_radius)
        item.setGraphicsEffect(blur_effect)

        blurred_pixmap = QPixmap(pixmap.size())
        blurred_pixmap.fill(Qt.transparent)
        painter = QPainter(blurred_pixmap)
        scene.render(painter)
        painter.end()

        return blurred_pixmap