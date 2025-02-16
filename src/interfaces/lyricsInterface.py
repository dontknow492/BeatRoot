from qfluentwidgets import ImageLabel, BodyLabel, LargeTitleLabel, TitleLabel, PrimaryPushButton
from qfluentwidgets import FluentIcon, setCustomStyleSheet, PrimaryPushButton, SearchLineEdit
from qfluentwidgets import SearchLineEdit, SimpleCardWidget, TransparentToolButton, TextBrowser
from qfluentwidgets import Theme, setTheme, setCustomStyleSheet


import sys
sys.path.append(r'D:\Program\Musify')

from src.common.myScroll import SideScrollWidget, HorizontalScrollWidget, VerticalScrollWidget
from src.common.myFrame import VerticalFrame, HorizontalFrame, FlowFrame
from src.utility.enums import PlaceHolder
from src.utility.image_utility import blur_pixmap


from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy, QStackedWidget
from PySide6.QtCore import Qt, QSize, Signal, QPoint, QTimer
from PySide6.QtGui import QFont, QColor, QImage, QIcon, QPainter, QPixmap, QTextCursor, QPalette, QBrush, QTextCharFormat
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QTextBrowser, QGraphicsOpacityEffect
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene, QGraphicsBlurEffect, QGraphicsPixmapItem
import json

class LyricsInterface(VerticalFrame):
    def __init__(self, title: str = "Unknown", artist: str = "Unknown", parent = None):
        super().__init__(parent)
        self.title = title
        self.artist = artist
        self.zoomFactor = 0
        
        self.original_pixmap = None  # Cache the original image
        self.blurred_pixmap = None  # Cache the blurred image
        self.blur_radius = 10
        self.resize_timer = QTimer()  # Timer to debounce resize events
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.handle_resize)
        
        self.setBackgroundImage(PlaceHolder.LYRICS.path)
        
        self.overlayZoom()
        self.init_ui()
        self.noLyricsSetup()
        

    def init_ui(self):
        # Create a QTextBrowser
        self.text_browser = TextBrowser(self)
        self.text_browser.setFocusPolicy(Qt.NoFocus)
        self.text_browser.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_browser.setFrameShape(QTextBrowser.NoFrame)
        qss = """
            TextBrowser {
                background-color: transparent;
                border: none;
                }
            TextBrowser::hover {
                background: transparent;
            }
        """
        setCustomStyleSheet(self.text_browser, qss, qss)
        # self.text_browser.verticalScrollBar().hide()
        # self.text_browser.setZoomFactor(1.0)
        

        # Set the initial title, author, and lyrics (empty)
        # self.update_lyrics("Ajab Si", "Song Author", "")

        # Layout setup
        
        self.addWidget(self.text_browser)

        # Window settings
        self.setWindowTitle("Dynamic Song Lyrics")
        self.resize(400, 300)
        
    # def setBackgroundImage(self, image_path):
    #     """Set the background image of the widget."""
    #     # Load the image and cache it
    #     self.original_pixmap = QPixmap(image_path)
    #     self.update_background()

    def setBackgroundImage(self, image_path):
        """Set the background image of the widget."""
        # Load the image and cache it
        self.original_pixmap = QPixmap(image_path)

        # Apply blur effect to the original image and cache the result
        self.blurred_pixmap = blur_pixmap(self.original_pixmap, self.blur_radius)

        # Update the background with the blurred image
        self.update_background()

    def update_background(self):
        """Update the background image based on the current widget size."""
        if self.blurred_pixmap is None:
            return

        # Scale the cached blurred pixmap to the size of the widget
        scaled_pixmap = self.blurred_pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

        # Set the scaled pixmap as the background of the widget
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(scaled_pixmap))
        self.setPalette(palette)
        
    def setBackgroundImageCSS(self, url):
        """Set the background image of the widget using CSS."""
        # CSS to set the background image
        css = f"""
            QFrame {{
                background-image: url('{url}');
                background-repeat: no-repeat;
                background-position: center;
                background-attachment: fixed;
            }}
        """

        # Apply the CSS to the widget
        self.setStyleSheet(css)

    def update_lyrics(self, title, author, lyrics):
        """Update the title, author, and lyrics with proper formatting."""
        # Create a QTextCursor
        self.title = title
        self.artist = author
        self.lyrics = lyrics
            
        cursor = self.text_browser.textCursor()

        # Clear the text in QTextBrowser first
        cursor.select(QTextCursor.Document)
        cursor.removeSelectedText()

        # Set title format (bold, large font size)
        title_format = QTextCharFormat()
        title_font = QFont()
        title_font.setPointSize(40)
        title_font.setWeight(QFont.DemiBold)
        title_format.setFont(title_font)

        # Set author format (italic, slightly smaller font)
        author_format = QTextCharFormat()
        author_font = QFont()
        # author_font.setItalic(True)
        author_font.setPointSize(28)
        author_font.setWeight(QFont.DemiBold)
        author_format.setFont(author_font)

        # Set lyrics format (normal weight, regular font size)
        lyrics_format = QTextCharFormat()
        lyrics_font = QFont()
        lyrics_font.setLetterSpacing(QFont.PercentageSpacing, 120) 
        lyrics_point_size =  24 + int(20 * self.zoomFactor)
        lyrics_pixel_size = 32+  int(27 * self.zoomFactor)
        print(f"lyrics_point_size: {lyrics_point_size}, lyrics_pixel_size: {lyrics_pixel_size}, self.zoomFactor: {self.zoomFactor}")
        lyrics_font.setPointSize(lyrics_point_size)
        lyrics_font.setPixelSize(lyrics_pixel_size)
        lyrics_format.setFont(lyrics_font)
        

        # Insert title
        cursor.setCharFormat(title_format)
        cursor.insertText(title + "\n")

        # Insert author
        cursor.setCharFormat(author_format)
        cursor.insertText("By: " + author + "\n")

        # Insert lyrics
        cursor.setCharFormat(lyrics_format)
        cursor.insertText(lyrics)
        # Set the updated cursor back into QTextBrowser
        self.text_browser.setTextCursor(cursor)
        self.text_browser.verticalScrollBar().setValue(0)
        
        if hasattr(self, 'titleLabel'):
            self.titleLabel.setText(title)
            self.artistLabel.setText(author)
            self.titleLabel.hide()
            self.artistLabel.hide()
            self.noLyricsLabel.hide()
            self.text_browser.show()
            self.noLyricsImage.hide()
            self.zoomContainer.show()
            
        self.zoomContainer.raise_()
        self.zoomContainer.raise_()
        self.text_browser.verticalScrollBar().setValue(0)
        
    def set_lyrics(self,title, artist, lyrics):
        """Set the lyrics directly."""
        self.update_lyrics(title, artist, lyrics)
    
    def overlayZoom(self):
        self.zoomContainer = HorizontalFrame(self)
        # self.zoomContainer.raise_()
        self.zoomContainer.setFrameShape(QFrame.Shape.StyledPanel)
        # self.zoomContainer.setWindowFlags(Qt.WindowType.ToolTip)
        
        self.zoomInButton = TransparentToolButton(FluentIcon.ZOOM_IN, self.zoomContainer)
        self.zoomInButton.setCursor(Qt.PointingHandCursor)
        self.zoomInButton.clicked.connect(lambda: self.on_zoom(0.05))
        self.zoomLabel = BodyLabel("100%")
        self.zoomOutButton = TransparentToolButton(FluentIcon.ZOOM_OUT, self.zoomContainer)
        self.zoomOutButton.setCursor(Qt.PointingHandCursor)
        self.zoomOutButton.clicked.connect(lambda: self.on_zoom(-0.05))
        
        self.zoomContainer.addWidget(self.zoomInButton)
        self.zoomContainer.addWidget(self.zoomLabel)
        self.zoomContainer.addWidget(self.zoomOutButton)
        
        self.zoomContainer.adjustSize()
        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0.5)  # Set opacity (0.0 = fully transparent, 1.0 = fully opaque)
        self.zoomContainer.setGraphicsEffect(opacity_effect)
        
    def on_zoom(self, zoom_factor):
        self.zoomFactor = self.zoomFactor + zoom_factor
        percent = int(100 + self.zoomFactor * 100)
        if percent> 0:
            self.update_lyrics(self.title, self.artist, self.lyrics)
            self.zoomLabel.setText(f"{percent}%")
        else:
            self.zoomFactor = self.zoomFactor - zoom_factor
        
    def resizeEvent(self, event):
        self.zoomContainer.move(self.width() - self.zoomContainer.width() - 20, self.height() - self.zoomContainer.height() - 20)
        self.resize_timer.start(100)
        return super().resizeEvent(event)
    
    def handle_resize(self):
        """Update the background after the resize event is complete."""
        self.update_background()
    
    def noLyricsSetup(self):
        if hasattr(self, "text_browser"):
            self.text_browser.hide()
        if hasattr(self, "zoomContainer"):
            self.zoomContainer.hide()
        self.titleLabel = LargeTitleLabel(self.title, self)
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.artistLabel = TitleLabel(self.artist, self)
        self.artistLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.noLyricsLabel = BodyLabel("No Lyrics Found", self)
        self.noLyricsLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.noLyricsLabel.setFont(QFont("Segoe UI", 20))
        self.noLyricsLabel.setStyleSheet("color: gray")
        image = FluentIcon.MUSIC.icon(color=QColor("gray")).pixmap(64, 64)
        self.noLyricsImage = ImageLabel(image, self)
        
        self.addWidget(self.titleLabel, 0, alignment= Qt.AlignmentFlag.AlignTop)
        self.addWidget(self.artistLabel, 0,alignment= Qt.AlignmentFlag.AlignTop)
        self.addWidget(self.noLyricsImage, 1, alignment= Qt.AlignmentFlag.AlignCenter)
        self.addWidget(self.noLyricsLabel, 3, alignment= Qt.AlignmentFlag.AlignTop)
        

if(__name__ == "__main__"):
    app = QApplication(sys.argv)
    setTheme(Theme.DARK)
    w = LyricsInterface()
    w.show()
    # w.setBackgroundImage(r"D:\Downloads\Images\Desktop-blurry-wallpaper.jpg")
    title = "Ajab Si"
    author = "Vishal-Skehar, KK"
    lyrics = (
        """
Aankhon mein teri
Ajab si ajab si adayein hai
hoo Aankhon mein teri
Ajab si ajab si adayein hai

Dil ko banade jo patang saans se
Yeh teri woh haawaien hai

Aankhon mein teri
Ajab si ajab si adayein hai
hoo Aankhon mein teri
Ajab si ajab si adayein hai

Dil ko banade jo patang saans se
Yeh teri woh haawaien hai

Aai aise raat hai jo
Bahut khush naseeb hai

Chahe jise door se duniya
Woh mere kareeb hai

Kitna kuch kehna hai
Phir bhi hai dil mein
Saawal hai kahin

Sapno mein jo roj kaha hai
Woh phir se kahun ya nahi

Aankhon mein teri
Ajab si ajab si adayein hai
hoo Aankhon mein teri
Ajab si ajab si adayein hai

Dil ko banade jo patang saans se
Yeh teri woh haawaien hai

Tere saath saath aisa
        """
    )
    # print(lyrics)  
    # w.zoomContainer.show()
    # w.zoomContainer.raise_()
    # w.zoomContainer.raise_()
    w.set_lyrics("Dil Lga Liya", "John Doe", lyrics)  
    # w.update_lyrics(title, author, lyrics)
    app.exec()
    