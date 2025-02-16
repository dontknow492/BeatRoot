from qfluentwidgets import RoundMenu, Action
from qfluentwidgets import FluentIcon, setCustomStyleSheet, setThemeColor, setTheme, Theme, ThemeColor

import sys
sys.path.append('d:\\Program\\Musify')
# print(sys.path)
from src.components.filters.filterCardBase import FilterBase
from src.utility.enums import SortType

from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, QSize, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor




class FilterView(FilterBase):
    sortingChanged = Signal(SortType)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.searchBar.setHidden(True)
        
        # self.signalHandler()
        
    def set_menu(self, menu):
        pre_menu = self.sortByButton.menu()
        if pre_menu:
            pre_menu.deleteLater()
        self.sortByButton.setMenu(menu)
        

    
        
if(__name__ == "__main__"):
    app = QApplication(sys.argv)
    window = FilterView()
    window.resize(300, 96)
    window.show()
    window.initMenu()
    window.sortingChanged.connect(lambda st: print(st.description))
    window.searchClicked.connect(lambda text: print(text))
    app.exec()
        