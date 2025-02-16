from PySide6.QtWidgets import QWidget, QApplication, QLabel
from PySide6.QtGui import QPainter, QColor, QConicalGradient, QPen
from PySide6.QtCore import Qt, QTimer

from qfluentwidgets import themeColor


class LoadingCircle(QLabel):
    def __init__(self, parent = None):
        super().__init__(parent= parent)
        self.angle = 270  # Rotation angle
        self.tail_length = 360  # Length of the tail (arc span)
        self.tail_direction = 1  # 1 for increasing, -1 for decreasing
        
        self.point_size = 6  # Size of the arc points
        self.radius= 30  # Radius of the arc
        
        self.gradient = QConicalGradient(0, 0, 0)  # Start at the center with a 0 degree angle
        self.gradient.setColorAt(0, QColor(242, 240, 230))  # Start with blue at the beginning
        self.gradient.setColorAt(1, QColor(255, 255, 255))
        
        self.setAutoFillBackground(True)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.setInterval(16)
        # self.timer.start(16)  # ~60 FPS
        self.setFixedSize(120, 120)
        self.setWindowTitle("Loading Ring with Tail Effect")
    
    def setAttribute(self, radius, point_size, gradient: QConicalGradient | None = None):
        self.radius = radius
        self.point_size = point_size
        if gradient is not None:
            self.gradient = gradient
        
    def start_animation(self):
        """Start the animation."""
        self.timer.start(16)
        
    def stop_animation(self):
        """Stop the animation."""
        self.timer.stop()

    def update_animation(self):
        """Update the rotation angle and tail length dynamically for smooth animation."""
        # Modify angle speed for smoother rotation
        self.angle_speed_factor = 7 
        self.tail_speed_factor = 5
        if self.angle >= 360:
            self.angle = 0  # Reset angle to keep it within bounds
        # Smoothly adjust tail length
        if self.tail_direction == 1:
            self.angle += 6
            if self.angle < 60 or self.angle > 270:
                self.tail_length += 5
                self.angle += 2
            else:
                self.tail_length += 3
        else:
            self.angle+= 6
            if self.angle < 60 or self.angle > 270:
                self.tail_length -= 5
                self.angle += 2
            else:
                self.tail_length -= 3
        # Swap direction at tail length thresholds for smooth oscillation
        max_tail_length = 360  # Max tail length threshold
        if self.tail_length >= max_tail_length:
            self.tail_length = 359
            self.tail_direction = -1  # Start decreasing
        elif self.tail_length <= 5:
            self.tail_length = 5
            self.tail_direction = 1  # Start increasing

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)

        # Create a conical gradient for the arc (line) with gradient along the path
        gradient = QConicalGradient(0, 0, 0)  # Start at the center with a 0 degree angle
        gradient.setColorAt(0, QColor(242, 240, 230))  # Start with blue at the beginning
        gradient.setColorAt(1, QColor(255, 255, 255))  # Fade to light cyan at the end

        # Create a pen with the gradient
        pen = QPen(self.gradient, self.point_size, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)

        # Draw the continuous arc with a gradient color along the line
        span = -int(self.tail_length * 16)  # Convert degrees to 1/16th units, negative for clockwise
        painter.drawArc(-self.radius , -self.radius , self.radius * 2, self.radius * 2, 0, span)

if __name__ == "__main__":
    app = QApplication([])
    w = QWidget()
    window = LoadingCircle(w)
    
    # window.setFixedSize(38, 38)
    
    window.setAttribute(10, 3, window.gradient)
    color = themeColor()
    # window.setStyleSheet("border-radius: 5px;")
    window.setPalette(color)
    palette = window.palette()
    palette.setColor(window.backgroundRole(), color)  # Use themeColor()
    window.setPalette(palette)
    window.setAutoFillBackground(True)
    
    w.show()
    app.exec()
