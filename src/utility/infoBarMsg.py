from qfluentwidgets import InfoBar, InfoBarPosition
from PySide6.QtCore import Qt, QObject
from PySide6.QtGui import QIcon

class InfoTime(QObject):
    def __init__(self, parent: QObject, pos: InfoBarPosition = InfoBarPosition.BOTTOM, duration: int = 2000):
        super().__init__(parent)
        self.pos = pos
        self.duration = duration
        self.parent = parent
        self.orient = Qt.Horizontal
        self.isClosable = True
        
    def success_msg(self, title, msg):
        InfoBar.success(
            title=title,
            content=msg,
            orient=self.orient,
            isClosable=self.isClosable,
            position=self.pos,
            duration=self.duration,
            parent=self.parent
        )
        
    def error_msg(self, title, msg):
        InfoBar.error(
            title=title,
            content=msg,
            orient=self.orient,
            isClosable=self.isClosable,
            position=self.pos,
            duration=self.duration,
            parent=self.parent
        )
        
    def warning_msg(self, title, msg):
        InfoBar.warning(
            title=title,
            content=msg,
            orient=self.orient,
            isClosable=self.isClosable,
            position=self.pos,
            duration=self.duration,
            parent=self.parent
        )
        
    def info_msg(self, title, msg):
        InfoBar.info(
            title=title,
            content=msg,
            orient=self.orient,
            isClosable=self.isClosable,
            position=self.pos,
            duration=self.duration,
            parent=self.parent
        )
        
    def failure_msg(self, title, msg):
        InfoBar.failure(
            title=title,
            content=msg,
            orient=self.orient,
            isClosable=self.isClosable,
            position=self.pos,
            duration=self.duration,
            parent=self.parent
        )
        
    def custom_msg(self, title, msg, icon: QIcon, background_col: str, background_hex: str):
        w = InfoBar.new(
            icon=icon,
            title=title,
            content=msg,
            orient=self.orient,
            isClosable=self.isClosable,
            position=self.pos,
            duration=self.duration,
            parent=self.parent
        )
        w.setCustomBackgroundColor(background_col, background_hex)
        w.show()
    
    def setDuration(self, duration: int):
        self.duration = duration
        
    def setPos(self, pos: InfoBarPosition):
        self.pos = pos
        
    def setClosable(self, closable: bool):
        self.isClosable = closable
        
    def setOrient(self, orient: Qt.AlignmentFlag):
        self.orient = orient
        
