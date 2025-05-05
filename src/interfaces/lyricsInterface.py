from qfluentwidgets import ImageLabel, BodyLabel, LargeTitleLabel, TitleLabel, PrimaryPushButton
from qfluentwidgets import FluentIcon, setCustomStyleSheet, PrimaryPushButton, SearchLineEdit
from qfluentwidgets import SearchLineEdit, SimpleCardWidget, TransparentToolButton, TextBrowser
from qfluentwidgets import Theme, setTheme, setCustomStyleSheet


import sys


import random

from src.common.myScroll import SideScrollWidget, HorizontalScrollWidget, VerticalScrollWidget
from src.common.myFrame import VerticalFrame, HorizontalFrame, FlowFrame
from src.utility.enums import PlaceHolder
from src.utility.image_utility import blur_pixmap
from src.api.data_fetcher import YTMusicMethod, DataFetcherWorker
from src.animation.skeleton_screen_animation import RectSkeletonScreen
from src.utility.misc import is_online_song


from PySide6.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout, QSpacerItem, QSizePolicy, QStackedWidget
from PySide6.QtCore import Qt, QSize, Signal, QPoint, QTimer
from PySide6.QtGui import QFont, QColor, QImage, QIcon, QPainter, QPixmap, QTextCursor, QPalette, QBrush, QTextCharFormat
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QTextBrowser, QGraphicsOpacityEffect
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene, QGraphicsBlurEffect, QGraphicsPixmapItem
import json

from loguru import logger
from pathlib import Path

class LyricsInterface(VerticalFrame):
    def __init__(self, datafetcher: DataFetcherWorker, parent = None):
        super().__init__(parent)
        self.datafetcher = datafetcher
        self.title = "Unknown"
        self.artist = "Unknown"
        
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
        # Create ui
        self.titleLabel = LargeTitleLabel(self.title, self)
        title_font = QFont()
        title_font.setPointSize(40)
        title_font.setWeight(QFont.DemiBold)
        self.titleLabel.setFont(title_font)
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        
        self.artistLabel = TitleLabel(self.artist, self)
        author_font = QFont()
        # author_font.setItalic(True)
        author_font.setPointSize(28)
        author_font.setWeight(QFont.DemiBold)
        self.artistLabel.setFont(author_font)
        self.artistLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.noLyricsLabel = BodyLabel("No Lyrics Found", self)
        self.noLyricsLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.noLyricsLabel.setFont(QFont("Segoe UI", 20))
        self.noLyricsLabel.setStyleSheet("color: gray")
        image = FluentIcon.MUSIC.icon(color=QColor("gray")).pixmap(64, 64)
        self.noLyricsImage = ImageLabel(image, self)
        
        
        self.text_browser = TextBrowser(self)
        self.text_browser.setFocusPolicy(Qt.NoFocus)
        self.text_browser.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_browser.setFrameShape(QTextBrowser.NoFrame)
        text_font = QFont()
        text_font.setPointSize(32)
        self.text_browser.setFont(text_font)
        qss = """
            TextBrowser {
                background-color: transparent;
                border: none;
                }
            TextBrowser::hover {
                background: transparent;
                border: none;
            }
        """
        setCustomStyleSheet(self.text_browser, qss, qss)
        
        self._init_loading_frame()
        spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        
        
        self.addWidget(self.titleLabel, 0, alignment= Qt.AlignmentFlag.AlignTop)
        self.addWidget(self.artistLabel, 0,alignment= Qt.AlignmentFlag.AlignTop)
        
        self.addWidget(self.loading_animation, alignment= Qt.AlignmentFlag.AlignHCenter)
        
        self.addWidget(self.noLyricsImage, 1, alignment= Qt.AlignmentFlag.AlignCenter)
        self.addWidget(self.noLyricsLabel, 3, alignment= Qt.AlignmentFlag.AlignTop)
        
        self.addWidget(self.text_browser, stretch=10)
        self.addSpacerItem(spacer)

        # Window settings
        self.setWindowTitle("Dynamic Song Lyrics")
        # self.resize(400, 300)
        
    def _init_loading_frame(self):
        self.loading_animation = VerticalFrame()
        self.loading_animation.setContentSpacing(0)
        for _ in range(4):
            line = HorizontalFrame(self.loading_animation)
            line.setContentSpacing(6)
            for _ in range(4):
                width = random.randint(50, 100)
                animation = RectSkeletonScreen(width, 20)
                # animation.setFixedSize(width, 20)
                line.addWidget(animation)
            self.loading_animation.addWidget(line)
            
    def start_animation(self):
        for child in self.loading_animation.children():
            if isinstance(child, HorizontalFrame):
                for animation in child.children():
                    if isinstance(animation, RectSkeletonScreen):
                        animation.start_animation()

    def stop_animation(self):
        for child in self.loading_animation.children():
            if isinstance(child, HorizontalFrame):
                for animation in child.children():
                    if isinstance(animation, RectSkeletonScreen):
                        animation.stop_animation()

    def set_blur_radius(self, radius):
        self.blur_radius = radius
        
    def setBackgroundImage(self, image_path: str):
        """Set the background image of the widget."""
        # Load the image and cache it
        if image_path is None or  not Path(image_path).exists():
            image_path = PlaceHolder.LYRICS.path
        self.original_pixmap = QPixmap(image_path)

        # Apply blur effect to the original image and cache the result
        self.blurred_pixmap = blur_pixmap(self.original_pixmap, self.blur_radius)

        # Update the background with the blurred image
        self.update_background()
        self.update()
        self.repaint()

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

    def fetch_song_lyrics(self, video_id: str):
        if not is_online_song(video_id):
            self.noLyricsSetup()
            return None  # No lyrics available
        self.set_loading(True)
        self.clear_lyrics()
        logger.info(f"Fetching lyrics for video id: {video_id}")
        self.datafetcher.data_fetched.connect(self._on_watch_fetched)
        self.watch_request_id = self.datafetcher.add_request(YTMusicMethod.GET_WATCH_PLAYLIST, video_id)
    
    def _on_watch_fetched(self,  watch_list, request_id):
        if request_id != self.watch_request_id:
            return
        if watch_list is None:
            return
        logger.info("Watch list fetched")
        lyrics_id = watch_list.get("lyrics")
        track_1 = watch_list.get("tracks")[0]
        logger.debug(track_1)
        title = track_1.get("title")
        artist = track_1.get("artists")[0].get("name")
        self.set_title(title)
        self.set_author(artist)
        if not lyrics_id:
            self.noLyricsSetup()
            logger.warning("No lyrics", "No lyrics available")
            return None  # No lyrics available
        self.lyrics_request_id = self.datafetcher.add_request(YTMusicMethod.GET_LYRICS, lyrics_id)
        self.datafetcher.data_fetched.connect(self._on_lyrics_fetched)
        
    def _on_lyrics_fetched(self, lyrics_data, request_id):
        if request_id != self.lyrics_request_id:
            return
        if lyrics_data is None:
            logger.warning("No lyrics available")
            return None  # No lyrics available
        logger.success("Lyrics fetched")
        
        self.update_lyrics(lyrics_data.get("lyrics"))
    
    def update_lyrics(self, lyrics):
        """Update the title, author, and lyrics with proper formatting."""
        # Create a QTextCursor
        self.lyrics = lyrics
        """Update the QTextBrowser text and align it to the center."""
        centered_lyrics = f'<div align="center">{self.lyrics.replace("\n", "<br>")}</div>'
        self.text_browser.setText(centered_lyrics)
        self.text_browser.verticalScrollBar().setValue(0)
        
        if hasattr(self, 'titleLabel'):
            self.noLyricsLabel.hide()
            self.text_browser.show()
            self.noLyricsImage.hide()
            self.zoomContainer.show()
            self.stop_animation()
            self.loading_animation.hide()
            
        self.zoomContainer.raise_()
        self.zoomContainer.raise_()
        self.text_browser.verticalScrollBar().setValue(0)
        
    def set_lyrics(self,title, artist, lyrics):
        """Set the lyrics directly."""
        self.update_lyrics(lyrics)
        self.set_title(title)
        self.set_author(artist)
        
    def set_title(self, title: str):
        if not title and title != "":
            title = "Unknown"
        self.title = title
        self.titleLabel.setText(title)
    
    def set_author(self, author):
        if not author and author != "":
            author = "Unknown"
        self.artist = author
        self.artistLabel.setText(f"By: {author}")
        
    def increase_font_size(self, increment=2):
        """Increase the font size of the QTextBrowser dynamically."""
        current_font = self.text_browser.font()
        new_size = current_font.pointSize() + increment  # Increase font size
        current_font.setPointSize(new_size)
        self.text_browser.setFont(current_font)  # Apply new font size

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
        """Adjust the font size dynamically based on zoom_factor."""
        logger.info(f"Zoom factor: {zoom_factor}")
        
        text = self.zoomLabel.text()
        text = text.replace("%", "")
        value = int(text)
        value = value + int(100 * zoom_factor)
        
        if value < 10 and zoom_factor < 0:
            return
        self.adjust_font_size(zoom_factor)
        self.zoomLabel.setText(f"{value}%")
            
    def adjust_font_size(self, zoom_factor):
        change = 1 if zoom_factor>0 else -1
        logger.info(f"Adjusting font size by {zoom_factor}")
        current_font = self.text_browser.font()
        new_size = current_font.pointSize() + change  # Prevent too small fonts
        logger.info(f"Previous font Size: {current_font.pointSize()}")
        logger.info(f"New font size: {new_size}")
        current_font.setPointSize(new_size)
        self.text_browser.setFont(current_font)

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
        
        if hasattr(self, "loading_animation"):
            self.stop_animation() 
            self.loading_animation.hide()  
        self.noLyricsImage.show()
        self.noLyricsLabel.show() 
        
    def set_loading(self, state: bool):
        if state:
            self.start_animation()
            self.loading_animation.show()
            # self.text_browser.hide()
            self.noLyricsImage.hide()
            self.noLyricsLabel.hide()
        else:
            self.stop_animation()
            self.loading_animation.hide()
            self.text_browser.show()
        
    def clear_lyrics(self):
        self.text_browser.setText("")
    
    def reset_lyrics_interface(self):
        self.set_title("")
        self.set_author("")
        self.clear_lyrics()
        self.noLyricsSetup()  
        
if(__name__ == "__main__"):
    app = QApplication(sys.argv)
    setTheme(Theme.DARK)
    datafetcher = DataFetcherWorker()
    datafetcher.start()
    w = LyricsInterface(datafetcher)
    w.show()
    # w.setBackgroundImage(r"D:\Downloads\Images\Desktop-blurry-wallpaper.jpg")
    title = "Ajab Si"
    author = "Vishal-Skehar, KK"
    lyrics = (
        """Aankhon mein teri
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
    # w.set_lyrics("Dil Lga Liya", "Sameer", lyrics)  
    w.fetch_song_lyrics("tfvwos6d-qw12")
    w.setBackgroundImage(r"D:\Program\Musify\.cache\thumbnail\song\_eZnQzneuKs.png")
    app.exec()
    