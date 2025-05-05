from qfluentwidgets import setTheme, Theme
import sys

from qfluentwidgets import FlowLayout, PrimaryPushButton
from qfluentwidgets import setTheme, Theme

sys.path.append('src')
# print(sys.path)

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem
from PySide6.QtCore import Qt, QTimer, QObject
from PySide6.QtGui import QPixmap, QPalette, QBrush

from typing import override
class MyFrameBase(QFrame):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFrameShape(QFrame.NoFrame)
        self.setFrameStyle(QFrame.Box)
        # self.setFrameShape(QFrame.StyledPanel)
        self.original_pixmap = None
        self.resize_timer = QTimer()  # Timer to debounce resize events
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.handle_resize)
        self.setLineWidth(0)
        self.setObjectName("MyFrameBase")
        self.setGraphicsEffect(None)
        self.initLayout()
        
    def initLayout(self):
        self.mainLayout = QVBoxLayout(self)
        self.setLayout(self.mainLayout)
        
    def addWidget(self, widget, stretch = 0, alignment: Qt.AlignmentFlag | None = None):
        if isinstance(widget, QSpacerItem):
            self.mainLayout.addSpacerItem(widget)
        elif alignment is not None:
            self.mainLayout.addWidget(widget, stretch, alignment)
        else:
            if stretch != 0:
                self.mainLayout.addWidget(widget, stretch)
            else:
                self.mainLayout.addWidget(widget)
                
                
    def addSpacerItem(self, item: QSpacerItem):
        self.mainLayout.addSpacerItem(item)
    
    def insertWidget(self, index, widget, stretch = 0, alignment: Qt.AlignmentFlag | None = None):
        if isinstance(widget, QSpacerItem):
            self.mainLayout.insertSpacerItem(index, widget)
        elif alignment is not None:
            self.mainLayout.insertWidget(index, widget, stretch, alignment)
        else:
            if stretch != 0:
                self.mainLayout.insertWidget(index, widget, stretch)
            else:
                self.mainLayout.insertWidget(index, widget)
        
    def addWidgets(self, widgets):
        for widget in widgets:
            self.addWidget(widget)
            
    def setAlignment(self, alignment: Qt.AlignmentFlag):
        self.mainLayout.setAlignment(alignment)
            
    def setLayoutMargins(self, left: int, top: int, right: int, bottom: int):
        self.mainLayout.setContentsMargins(left, top, right, bottom)
        
    def setContentSpacing(self, spacing):
        self.mainLayout.setSpacing(spacing)
        
    def setBackgroundImage(self, image_path):
        """Set the background image of the widget."""
        # Load the image
        pixmap = QPixmap(image_path)

        # Set the pixmap as the background of the widget
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setBrush(self.backgroundRole(), pixmap)
        self.setPalette(palette)
        
    def setBackgroundImageCSS(self, url):
        """Set the background image of the widget using CSS."""
        # CSS to set the background image
        css = f"""
            QFrame#MyFrameBase {{
                background-image: url('{url}');
                background-position: center;
                background-attachment: fixed;
            }}
        """

        # Apply the CSS to the widget
        self.setStyleSheet(css)
    
    def setBackgroundImage(self, pixmap: QPixmap):
        """Set the background image of the widget."""
        # Load the image and cache it
        self.original_pixmap = pixmap

        # Apply blur effect to the original image and cache the result

        # Update the background with the blurred image
        self.update_background()
    
    def update_background(self):
        """Update the background image based on the current widget size."""
        if self.original_pixmap is None:
            return

        # Scale the cached blurred pixmap to the size of the widget
        scaled_pixmap = self.original_pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

        # Set the scaled pixmap as the background of the widget
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(scaled_pixmap))
        self.setPalette(palette)
    
    def resizeEvent(self, event):
        self.resize_timer.start(100)
        return super().resizeEvent(event)
    
    def handle_resize(self):
        """Update the background after the resize event is complete."""
        self.update_background()

    def clear(self, type_: QObject | None = None):
        print('clear', type_)
        
        for i in reversed(range(self.mainLayout.count())):  # Iterate in reverse to avoid index shifting
            item = self.mainLayout.itemAt(i)
            if item is None:
                continue  # Don't exit early, just skip this item
            
            widget = item.widget()
            if widget is None:
                continue  # Ensure widget exists before attempting to remove

            if type_ is None or isinstance(widget, type_):  # Remove all or only matching type
                self.delete_widget(widget)

        self.mainLayout.update()  # Ensure layout updates properly

    def count(self):
        return self.mainLayout.count()

    def itemAt(self, index):
        return self.mainLayout.itemAt(index)
        
    def delete_widget(self, widget: QObject):
        if not widget or not hasattr(widget, "deleteLater"):
            return  # Safety check

        if widget.parent() is not None:
            widget.setParent(None)  # Detach from parent before deletion

        if self.mainLayout.indexOf(widget) != -1:  # Ensure widget is in layout before removing
            self.mainLayout.removeWidget(widget)

        widget.deleteLater()  # Schedule for deletion

        
class FlowFrame(MyFrameBase):
    def __init__(self, parent = None):
        super().__init__(parent)
        
        
    def initLayout(self):
        self.mainLayout = FlowLayout(self)
        # self.setLayout(self.mainLayout)
        
    def setHorizantalSpacing(self, spacing):
        self.mainLayout.setHorizontalSpacing(spacing)
        
    def setVerticalSpacing(self, spacing):
        self.mainLayout.setVerticalSpacing(spacing)
    
    @override    
    def addWidget(self, widget):
        self.mainLayout.addWidget(widget)
        
class HorizontalFrame(MyFrameBase):
    def __init__(self, parent = None):
        super().__init__(parent)

    def initLayout(self):
        self.mainLayout = QHBoxLayout(self)
        # self.setLayout(self.mainLayout)
        
class VerticalFrame(MyFrameBase):
    def __init__(self, parent = None):
        super().__init__(parent)

    def initLayout(self):
        # self.mainLayout.deleteLater()
        self.mainLayout = QVBoxLayout(self)
        # self.setLayout(self.mainLayout)

        
        
if(__name__ == "__main__"):
    app = QApplication(sys.argv)
    setTheme(Theme.DARK)
    w = VerticalFrame()
    pixmap = QPixmap(r"/resources\images\image_2.png")
    w.setBackgroundImage(pixmap)
    
    for x in range(10):
        card = PrimaryPushButton(f"playlist: {x}", w)
        # card.setTitle(f"playlist: {x}")
        card.clicked.connect(w.clear)
        w.addWidget(card)
    # w.addWidget(ToolButton(FluentIcon.MORE), alignment=Qt.AlignmentFlag.AlignAbsolute)
    # w.addWidget(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum), alignment=Qt.AlignmentFlag.AlignLeft)
    # w.addWidget(ToolButton(FluentIcon.MORE), alignment=Qt.AlignmentFlag.AlignRight)
    # w.setStyleSheet("background-color: red;")
    w.show()
    sys.exit(app.exec())