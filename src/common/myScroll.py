from qfluentwidgets import ImageLabel, BodyLabel, TitleLabel, TransparentToolButton, TransparentDropDownToolButton
from qfluentwidgets import FluentIcon, setCustomStyleSheet, setThemeColor, setTheme, Theme, ThemeColor, ScrollArea
from qfluentwidgets import SmoothScrollArea, FlowLayout

import sys
sys.path.append(r'D:\Program\Musify')
# print(sys.path)

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QSize, Signal, QPoint, QObject
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect


class MyScrollWidgetBase(QFrame):
    def __init__(self, title: str = None, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setObjectName("ScrollWidget")
        
        self.title = title
        
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(0)
        
        self.initScrollWidget()
        self.initScrollLayout()
        self.scrollContainer_layout.setSpacing(10)
        self.scrollContainer_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        
        self.dragging = False
        self.lastMousePos = QPoint()
        self.speedFactor = 1.0
        
        
    def initScrollLayout(self):
        self.scrollContainer_layout = QVBoxLayout(self.scrollContainer)
        self.scrollContainer.setLayout(self.scrollContainer_layout)
        
    def initScrollWidget(self):
        self.scrollArea = SmoothScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        # self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.scrollContainer = QFrame(self)
        self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.scrollArea.setStyleSheet("background-color: transparent; border: none;")
        
        if self.title:
            self.titleLabel = TitleLabel(self.title, self)
        else:
            self.titleLabel = TitleLabel("", self)
            self.titleLabel.hide()
        
        
        #setting widget
        self.scrollArea.setWidget(self.scrollContainer)
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.scrollArea)
        
    def addWidget(self, widget, stretch: int = 0, alignment: Qt.AlignmentFlag | None = None):
        if hasattr(self, "scrollContainer_layout"):
            try:
                if alignment is None:
                    self.scrollContainer_layout.addWidget(widget, stretch)
                else:
                    self.scrollContainer_layout.addWidget(widget, stretch, alignment)
            except TypeError:
                self.scrollContainer_layout.addWidget(widget)
        else:
            print("scrollWidget_layout not found")
            
    def insertWidget(self, index, widget, stretch = 0, alignment: Qt.AlignmentFlag | None = None):
        if isinstance(widget, QSpacerItem):
            self.scrollContainer_layout.insertSpacerItem(index, widget)
        elif alignment is not None:
            self.scrollContainer_layout.insertWidget(index, widget, stretch, alignment)
        else:
            if stretch != 0:
                self.scrollContainer_layout.insertWidget(index, widget, stretch)
            else:
                self.scrollContainer_layout.insertWidget(index, widget)
        
    def addWidgets(self, widgets):
        for widget in widgets:
            self.addWidget(widget)
            
    def setTitle(self, title):
        self.titleLabel.setText(title)
        
    def getTopLevelWidget(self, widget):
        """ Walks up the widget tree to find the first widget that is directly added to the layout. """
        while widget and widget.parent() != self.scrollContainer:
            widget = widget.parent()
        return widget
            
    def mousePressEvent(self, event):
        print('move')
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.lastMousePos = event.position().toPoint()
            # print(card)
            self.movedEnough = False  # Reset move flag
            event.accept()
            self.scrollArea.setCursor(Qt.ClosedHandCursor)
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event):
        # print('move')
        if self.dragging:
            current_pos = event.position().toPoint()
            delta = current_pos - self.lastMousePos
            # # Check if movement is significant
            
            # Apply scroll
            self.scrollArea.horizontalScrollBar().setValue(
                self.scrollArea.horizontalScrollBar().value() - delta.x()
            )
            self.scrollArea.verticalScrollBar().setValue(
                self.scrollArea.verticalScrollBar().value() - delta.y()
            )

            self.lastMousePos = current_pos
            event.accept()
        else:
            super().mouseMoveEvent(event)
            
    def clear(self, type_: QObject | None = None):
        for i in reversed(range(self.scrollContainer_layout.count())):  # Iterate in reverse
            item = self.scrollContainer_layout.itemAt(i)
            if not item:
                continue  # Skip if item is None
            
            widget = item.widget()
            if widget is None:
                continue  # Avoid calling delete_widget on None
            
            if type_ is None or isinstance(widget, type_):  # Remove if no type is specified or matches type_
                self.delete_widget(widget)
                
    def delete_widget(self, widget: QObject):
        if not widget or not hasattr(widget, "deleteLater"):
            return  # Safety check

        if widget.parent() is not None:
            widget.setParent(None)  # Detach from parent before deletion

        if self.scrollContainer_layout.indexOf(widget) != -1:  # Ensure widget is in layout before removing
            self.scrollContainer_layout.removeWidget(widget)

        widget.deleteLater()  # Schedule for deletion

            
    # def block_child_signal(self):
        # self.scr
    def setWidgetResizable(self, state: bool):
        self.scrollArea.setWidgetResizable(state)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False  # Start the glide effect (60 FPS)
            event.accept()
            self.scrollArea.setCursor(Qt.ArrowCursor)
            # self.smooth_scroll(self.scrollArea, 800)
        else:
            super().mouseReleaseEvent(event)
            
    def getLayout(self):
        return self.scrollContainer_layout
    
    def hideTitle(self):
        self.titleLabel.hide()
        
    def showTitle(self):
        self.titleLabel.show()
        
    def setMargins(self, left, right, top, bottom):
        self.setContentsMargins(left, top, right, bottom)
        
    def setLayoutMargins(self, left, right, top, bottom):
        self.scrollContainer_layout.setContentsMargins(left, top, right, bottom)
        
    def setSpacing(self, spacing):
        self.scrollContainer_layout.setSpacing(spacing)
    
    def setContentSpacing(self, spacing):
        self.setSpacing(spacing)
        
    def addSpacerItem(self, item: QSpacerItem):
        self.scrollContainer_layout.addSpacerItem(item)
        
    def removeWidget(self, widget):
        self.scrollContainer_layout.removeWidget(widget) 
        
    def itemAt(self, index):
        return self.scrollContainer_layout.itemAt(index)   
    
    def indexOf(self, widget):
        return self.scrollContainer_layout.indexOf(widget)
    
    def count(self):
        return self.scrollContainer_layout.count()
        
class SideScrollWidget(MyScrollWidgetBase):
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        
        # Disabling the vertical scrollbar
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Spacer initialization to push widgets horizontally
        self.spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.current_spacer = None
        self.min_height = 0
        
    def initScrollLayout(self):
        """Initializes the scroll layout to hold widgets in a horizontal arrangement."""
        self.scrollContainer_layout = QHBoxLayout(self.scrollContainer)
        self.scrollContainer.setLayout(self.scrollContainer_layout)   
    
    def addWidget(self, widget: QObject, stretch=0, alignment=Qt.AlignmentFlag.AlignLeft):
        """
        Adds a widget to the scroll container and adjusts the scroll area height dynamically.
        
        :param widget: The widget to add to the scroll area.
        :param stretch: The stretch factor for the widget.
        :param alignment: The alignment of the widget within the scroll area.
        """
        # Remove any previous spacer
        if self.current_spacer:
            self.scrollContainer_layout.removeItem(self.current_spacer)
        
        self.current_spacer = self.spacer  # Set the current spacer
        
        
        # Adjust minimum height based on the widget height
        widget_height = widget.sizeHint().height()
        layout_margin = self.scrollContainer_layout.contentsMargins()
        widget_height += layout_margin.top() + layout_margin.bottom()
        if widget_height > self.min_height:
            self.scrollArea.setMinimumHeight(widget_height)
            self.min_height = widget_height

        # Add the widget and spacer to the layout
        super().addWidget(widget, stretch, alignment)
        super().addSpacerItem(self.current_spacer)
        
        # Update geometry after adding the widget
        self.updateGeometry()
    
    def insertWidget(self, index, widget, stretch=0, alignment=Qt.AlignmentFlag.AlignLeft):
        """Inserts a widget at the specified index."""
        return super().insertWidget(index, widget, stretch, alignment)
    
    def count(self):
        """
        Returns the number of widgets in the layout, accounting for the spacer item.
        """
        if self.current_spacer:
            return super().count() - 1  # Subtract 1 to account for the spacer
        return super().count()
        
class VerticalScrollWidget(MyScrollWidgetBase):
    def __init__(self, title: str = None, parent=None):
        super().__init__(title, parent)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def initScrollLayout(self):
        self.scrollContainer_layout = QVBoxLayout(self.scrollContainer)
        self.scrollContainer.setLayout(self.scrollContainer_layout)
        
    def addWidget(self, widget, stretch = 0, alignment = Qt.AlignmentFlag.AlignTop):
        return super().addWidget(widget, stretch, alignment)
    
    def insertWidget(self, index, widget, stretch=0, alignment = Qt.AlignmentFlag.AlignTop):
        return super().insertWidget(index, widget, stretch, alignment)
        
        
class HorizontalScrollWidget(MyScrollWidgetBase):
    def __init__(self, title: str = None, parent=None):
        super().__init__(title, parent)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def initScrollLayout(self):
        self.scrollContainer_layout = QHBoxLayout(self.scrollContainer)
        self.scrollContainer.setLayout(self.scrollContainer_layout)
        
        
class FlowScrollWidget(MyScrollWidgetBase):
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    
    def initScrollLayout(self):
        self.scrollContainer_layout = FlowLayout(self.scrollContainer)
        self.scrollContainer.setLayout(self.scrollContainer_layout)
        
    def setVerticalSpacing(self, spacing):
        self.scrollContainer_layout.setVerticalSpacing(spacing)
        
    def setHorizontalSpacing(self, spacing):
        self.scrollContainer_layout.setHorizontalSpacing(spacing)
        
if(__name__ == "__main__"):
    app = QApplication(sys.argv)
    # setTheme(Theme.DARK)
    # w = FlowScrollWidget("For You")
    w  = SideScrollWidget(None)
    for x in range(10):
        card = PlaylistCard()
        card.sizeHint().width()
        card.setTitle(f"playlist: {x}")
        card.clicked.connect(lambda: print("clicked"))
        w.addWidget(card)
    w.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
    w.show()
    app.exec()