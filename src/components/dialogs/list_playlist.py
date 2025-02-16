from PySide6.QtWidgets import QDialog, QVBoxLayout, QFrame, QPushButton, QApplication
from PySide6.QtCore import Qt
import sys

from qfluentwidgets import TitleLabel, PushButton, MessageDialog, BodyLabel, MessageBoxBase

from typing import List, Dict

class PlaylistDialog(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Playlists")
        # self.setFixedSize(300, 400)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.adjustSize()
        self.buttonGroup.setFixedHeight(30)
        self.buttonGroup.setContentsMargins(0, 0, 0, 0)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        
    def add_playlists(self, playlists: List[Dict]):
        for playlist in playlists:
            title = playlist.get("name", "Unknown")
            id_ = playlist.get("id", None)
            if id_ is None:
                continue
            button = self._create_button(title, id_)
            self.viewLayout.addWidget(button)
            
    def _create_button(self, title: str, id_: int):
        button = PushButton(title, self.buttonGroup)
        button.playlist_id = id_
        button.clicked.connect(lambda: self._playlist_selected(button))
        return button

    def _playlist_selected(self, playlist):
        print(playlist.playlist_id)  # Access the dynamically added attribute
        print(playlist.text())  # Print the text of the button
        self.close()       
    
    # def initViewLayout(self):
    #     self.viewLayout.deleteLater()
        
    #     self.viewLayout = QVBoxLayout()
        # self.v
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QFrame()
    playlists = [
        {"name": "Playlist 1", "id": 1},
        {"name": "Playlist 2", "id": 2},
        {"name": "Playlist 3", "id": 3},
    ]
    dialog = PlaylistDialog(window)
    dialog.add_playlists(playlists)
    window.show()
    window.resize(300, 400)
    dialog.exec()
    sys.exit(app.exec())