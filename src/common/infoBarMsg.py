from qfluentwidgets import InfoBar, InfoBarPosition
from PySide6.QtCore import Qt, QObject, QSize
from PySide6.QtGui import QIcon

class InfoTime(QObject):
    def __init__(self, parent: QObject, pos: InfoBarPosition = InfoBarPosition.BOTTOM, duration: int = 20000):
        super().__init__(parent)
        self.pos = pos
        self.duration = duration
        self.parent = parent
        self.orient = Qt.Horizontal
        self.isClosable = True
        # self.info_bar = InfoBar(parent=self.parent)
        
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
        InfoBar.error(
            title=title,
            content=msg,
            orient=Qt.Vertical,  # Use vertical layout when the content is too long
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,
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
        
if(__name__ == "__main__"):
    from PySide6.QtWidgets import QApplication
    app = QApplication([])
    info = InfoTime(None)
    info.success_msg("Success", "This is a success message")
    info.error_msg("Error", "This is an error message")
    info.warning_msg("Warning", "This is a warning message")
    info.info_msg("Info", "This is an info message")
    info.failure_msg("Failure", "This is a failure message")
    app.exec()
        
