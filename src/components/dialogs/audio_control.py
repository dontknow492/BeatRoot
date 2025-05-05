from qfluentwidgets import ComboBox, RoundMenu, TogglePushButton, FluentIcon, StrongBodyLabel, Slider, \
                Dialog, Flyout, FlyoutView, FlyoutViewBase, SwitchButton, BodyLabel, Action

import sys


from src.common.myFrame import VerticalFrame, HorizontalFrame
from src.common.mySlider import VerticalSlider
from src.common.toggled_switch import AnimatedToggle

from src.utility.misc import get_presets

from PySide6.QtCore import Qt, Signal, QObject, QStandardPaths
from PySide6.QtWidgets import QApplication, QVBoxLayout, QFrame
import sys

class MusicControlPanel(FlyoutViewBase):
    equalizeSignal = Signal(bool)
    normalizeSignal = Signal(bool)
    preset_changed = Signal(int)
    band_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.sliders = list()
        self.init_presets()
        self.initUi()
        self.set_preset()
        # Ensure default preset is applied
        if self.preset.count() > 0:
            self.preset.setCurrentText("Flat")  # Default to "Flat"
            self.on_preset_change("Flat")
        
    def initUi(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        option_container = VerticalFrame(self)
        option_container.setContentSpacing(0)
        option_container.setFrameStyle(QFrame.Box)
        
        self.equilizer_container = HorizontalFrame(self)
        self.equilizer_container.setLayoutMargins(0, 0, 0, 0)
        # self.equilizer_container.setContentSpacing(0)
        
        preset_container = VerticalFrame(self.equilizer_container)
        preset_container.setLayoutMargins(0, 0, 0, 0)
        
        self.normalize_button = self.create_switch("Normalize", self.normalizeSignal)
        self.equilize_button = self.create_switch("Equalizer", self.equalizeSignal)
        option_container.addWidget(self.normalize_button)
        option_container.addWidget(self.equilize_button)
        
        preset_label = BodyLabel("Preset", preset_container)
        preset_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.preset = ComboBox(preset_container)
        self.preset.currentTextChanged.connect(self.on_preset_change)
        
        self.create_freq_sliders()
        
        preset_container.addWidget(preset_label)
        preset_container.addWidget(self.preset)
        self.equilizer_container.addWidget(preset_container, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        self.addWidget(option_container, align=Qt.AlignmentFlag.AlignTop)
        self.addWidget(self.equilizer_container, stretch=1)
        
    def init_presets(self):
        self.presets = get_presets()
        
    def create_switch(self, text: str, slot: Signal = None):
        frame = HorizontalFrame()
        frame.setLayoutMargins(0, 0, 0, 0)
        switch = AnimatedToggle(frame)
        if slot:
            switch.toggled.connect(slot.emit)
        size = switch.sizeHint()
        frame.setFixedHeight(size.height())
        label = StrongBodyLabel(text, frame)
        frame.addWidget(label)
        frame.addWidget(switch, alignment=Qt.AlignmentFlag.AlignRight)
        frame.mousePressEvent  = lambda event: switch.setChecked(not switch.isChecked())
        return frame
        
    def create_freq_sliders(self):
        names = ["60", "170", "310", "600", "1k", "3k", "6k", "12k", "14k", "16k"]
        for name in names:
            slider = VerticalSlider(f"{name}hz", self.equilizer_container)
            slider.layout().setSpacing(0)
            slider.set_range(-20, 20)
            slider.valueChanged.connect(self.on_slider_change)  # Connect slider value change signal
            self.equilizer_container.addWidget(slider)
            self.sliders.append(slider)
            # slider.valueChanged.disconnect()/
        
    def addWidget(self, widget, stretch=0, align: Qt.AlignmentFlag = None):
        if align:
            self.main_layout.addWidget(widget, stretch, align)
        else:
            self.main_layout.addWidget(widget, stretch)

    def set_sliders_value(self, values: list):
        for value, slider in zip(values, self.sliders):
            slider.valueChanged.disconnect()
            slider.setValue(value)
            slider.valueChanged.connect(self.on_slider_change)
        
    def set_preset(self):
        for key in self.presets.keys():
            self.preset.addItem(key)
    
    def on_preset_change(self, name):
        if name in self.presets:
            bands = self.presets.get(name)
            self.set_sliders_value(bands)
            index = self.preset.currentIndex()
            self.preset_changed.emit(index)
        else:
            print(f"Preset '{name}' not found.")
        
    def get_current_bands_value(self):
        """Return a list with the value of each frequency band."""
        bands = list()
        for slider in self.sliders:
            value = slider.getValue()
            bands.append(value)
        return bands
        
    def on_slider_change(self, value):
        """Handle slider value changes."""
        bands = self.get_current_bands_value()
        if len(bands) != 10:
            return
        formatted_band = {band_index: bands[band_index] for band_index in range(10)}
        self.band_changed.emit(formatted_band)
    # def set_presets(self, presets: list[dict]):
        

if(__name__ == "__main__"):
    app = QApplication(sys.argv)
    w = MusicControlPanel()
    # w.preset_changed.connect(print)
    # w.normalizeSignal.connect(print)
    # w.equalizeSignal.connect(print)
    # w.set_sliders_value([0, 1, 2 , 3, 4, 5, 6, 7, 8, 9])
    # wi = FlyoutView("hell", "hello")
    # w = Flyout(wi)
    # w = Dialog('a', 'a')
    w.show()
    app.exec()