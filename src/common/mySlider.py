from qfluentwidgets import Slider, StrongBodyLabel, themeColor, isDarkTheme, BodyLabel
from qfluentwidgets.components.widgets.slider import SliderHandle
from PySide6.QtWidgets import QApplication, QFrame, QVBoxLayout, QSlider, QGraphicsTransform, QWidget
from PySide6.QtCore import Qt, Signal, QRectF, QPoint
from PySide6.QtGui import QPainter, QColor, QMouseEvent
from PySide6.QtGui import QTransform


from PySide6.QtWidgets import QApplication, QSlider
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QPen
    



class VerticalSlider(QFrame):
    valueChanged = Signal(float)
    def __init__(self, text: str = None, parent=None):
        super().__init__(parent)
        # self.setFixedWidth(20)
        self.text = text
        self.initUi()
        
    def initUi(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setAlignment(Qt.AlignCenter)

        self.name_label = BodyLabel(self.text, self)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.name_label)

        self.slider = Slider(Qt.Orientation.Vertical, self)
        self.slider.valueChanged.connect(self.on_slider_value_changed)
        # self.slider.setTickInterval(10)
        self.main_layout.addWidget(self.slider, alignment=Qt.AlignHCenter, stretch=1)
        
        self.value_label = StrongBodyLabel("0.00", self)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.value_label)
        
    def on_slider_value_changed(self, value: int):
        # float_value = self.min + (value / 100) * (self.max - self.min)
        float_value = value / 100
        self.valueChanged.emit(float_value)
        self.value_label.setText(f"{float_value:.2f}")
        
    def set_range(self, minimum: int, maximum: int):
        minimum *= 100
        maximum *= 100
        self.slider.setRange(minimum, maximum)
        
    def setValue(self, value: int):
        self.slider.setValue(value * 100)
    
    def getValue(self):
        return self.slider.value() / 100
        
        
if(__name__ == "__main__"):
    app = QApplication([])
    w = VerticalSlider("he")
    w.set_range(-1, 1)
    w.show()
    app.exec()