from PySide6.QtCore import QObject, QUrl, Signal, QTimer
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from typing import List
from pathlib import Path
from PySide6.QtWidgets import QApplication

import sys
sys.path.append(r"D:\Program\Musify")
from src.utility.crop_image_border import remove_borders
from src.utility.validator import is_youtube_thumbnail_url

from loguru import logger
from PIL import Image

# Configure logger
# logger.basicConfig(level=logger.INFO, format="%(message)s")

class ThumbnailDownloader(QObject):
    # Define custom signals
    download_finished = Signal(str, str)  # Emits the file path when download is successful
    download_error = Signal(str, str)  # Emits the file path and error message when download fails # Emits when all requests are completed

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_network()

    def init_network(self):
        """Initialize the network manager."""
        self.network_manager = QNetworkAccessManager(self)
        # self.network_manager.finished.connect(self.on_download_finished)

    def download_thumbnail(self, url: str, output_name: str, output_dir: str, uid: str | None = None):
        """
        Download a thumbnail from the specified URL.

        Args:
            url (str): URL of the thumbnail to download.
            output_name (str): Name of the output file.
            output_dir (str): Directory to save the downloaded thumbnail.
        """
        if url is None:
            logger.error("URL is None")
            return
        path = Path(output_dir) / output_name
        if path.exists():
            # logger.info(f"Thumbnail already exists: {path}")
            self.download_finished.emit(str(path), uid)  # Emit signal for existing file
            return
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Create a QNetworkRequest with the URL
        request = QNetworkRequest(QUrl(url))

        # Send the request and get the reply
        reply = self.network_manager.get(request)

        # Store the output path in the reply object for later use
        reply.output_path = str(Path(output_dir) / output_name)
        reply.uid = uid
        reply.crop = is_youtube_thumbnail_url(url)
        # if reply.crop:
            # logger.info(f"Need to Crop the image: {url}")
        # Connect the finished signal to a slot
        reply.finished.connect(lambda: self.handle_thumbnail_download_finished(reply))
        

    def handle_thumbnail_download_finished(self, reply: QNetworkReply):
        """
        Handle the finished signal for a thumbnail download.

        Args:
            reply (QNetworkReply): The reply object containing the downloaded data.
        """
        # self._increment_request_count()
        try:
            if reply.error() == QNetworkReply.NoError:
                # Read the downloaded data
                thumbnail_data = reply.readAll()

                if reply.crop:
                    cropped_image = remove_borders(thumbnail_data.data())
                    if cropped_image and isinstance(cropped_image, Image.Image):
                    # Save the processed image
                        cropped_image.save(reply.output_path)
                        logger.info(f"Coverd thumbnail saved to {reply.output_path}")
                        self.download_finished.emit(reply.output_path, reply.uid)
                    else:
                        logger.error(f"Failed to process thumbnail: {reply.output_path}")
                        self.download_error.emit(reply.output_path, "Border removal failed")
                else:
                # Save the thumbnail to the specified output path
                    with open(reply.output_path, "wb") as file:
                        file.write(thumbnail_data.data())

                    # Emit the download_finished signal with the file path
                    self.download_finished.emit(reply.output_path, reply.uid)
                    logger.info(f"Thumbnail saved to {reply.output_path}")
            else:
                # Emit the download_error signal with the file path and error message
                self.download_error.emit(reply.output_path, reply.errorString())
                logger.error(f"Failed to download thumbnail: {reply.errorString()}")
        finally:
            # Clean up the reply object
            reply.deleteLater()
    # Reset the request count


if __name__ == "__main__":
    app = QApplication(sys.argv)
    urls = [
        "https://i.ytimg.com/vi/YALvuUpY_b0/maxresdefault.jpg",
        "https://lh3.googleusercontent.com/9yW8MLF3RtzJdf0W1kCi6azo4Sc3UpfPcK9-1akb9VAtvJrfHqY2XVHIW07hGECkkFtYMcB1E7o9U0nu=w120-h120-l90-rj",
    ]
    output_names = ["thumbnail1.png", "thumbnail2.jpg"]
    output_dir = r"D:\Downloads"
    downloader = ThumbnailDownloader()
    downloader.download_thumbnail(urls[0], output_names[0], output_dir)
    sys.exit(app.exec())