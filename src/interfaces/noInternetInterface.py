from qfluentwidgets import PrimaryPushButton, SubtitleLabel, ImageLabel, FluentIcon

import sys
sys.path.append(r'D:\Program\Musify')
from src.common.myFrame import VerticalFrame
from src.utility.check_net_connectivity import is_connected_to_internet

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, Signal

class NoInternetWindow(VerticalFrame):
    refreshClicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('HomeNoWindow')
        self.initUI()

    def initUI(self):
        self.container = VerticalFrame(self)
        self.noInternetLabel = SubtitleLabel("No Internet Connection", self.container)
        self.noInternetLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.noInternetLabel.setObjectName('noInternetLabel')
        self.iconLabel = ImageLabel(r"D:\Downloads\General\no-wifi-svgrepo-com.svg", self.container)
        self.iconLabel.setFixedSize(50, 50)
        self.imageLabel = ImageLabel(r"D:\Downloads\General\no_internet_image.png", self.container)
        self.refreshButton = PrimaryPushButton(FluentIcon.SYNC, "Refresh", self.container)
        
        self.container.addWidget(self.iconLabel, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.container.addWidget(self.noInternetLabel, alignment=Qt.AlignmentFlag.AlignTop)
        self.container.addWidget(self.imageLabel, alignment=Qt.AlignmentFlag.AlignTop)
        self.container.addWidget(self.refreshButton, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.addWidget(self.container, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def refresh(self):
        if(is_connected_to_internet()):
            self.refreshClicked.emit()
        
        
if(__name__ == "__main__"):
    app = QApplication([])
    w = NoInternetWindow()
    w.show()
    app.exec()
        
        