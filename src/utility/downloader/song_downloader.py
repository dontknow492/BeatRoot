from loguru import logger
import os
import uuid
from queue import Queue, Empty

from PySide6.QtCore import QObject, QThread, Signal, Slot, QMutex, QWaitCondition, QMutexLocker
import yt_dlp
from PySide6.QtWidgets import QPushButton


from PySide6.QtWidgets import QApplication, QProgressBar, QLabel, QHBoxLayout, QVBoxLayout, QWidget

import os
import uuid
import logging
from queue import Queue, Empty
from PySide6.QtCore import QObject, QThread, Signal, QMutex, QWaitCondition, QMutexLocker, QTimer
import yt_dlp as youtube_dlp
from loguru import logger


import os
import yt_dlp
import logging
from PySide6.QtCore import QObject, Signal, Slot

import uuid
import xxhash
from PySide6.QtCore import QObject, Signal, QThread, QTimer

logger = logging.getLogger(__name__)

class DownloadWorker(QObject):
    progress_updated = Signal(str, float, float)  # request_id, progress_percent, total size
    error_occurred = Signal(str, str)  # error_message, request_id
    download_finished = Signal(str)  # request_id

    def __init__(self, rate_limit=50000):
        super().__init__()
        self.download_url = None
        self.request_id = None
        self.download_dir = None
        self.is_downloading = False
        self.rate_limit = rate_limit
        self.cancel_current = False  # Initialize properly

    @Slot()
    def run(self):
        try:
            if not self.download_url:
                return
            logger.info(f"Starting download: {self.download_url} (ID: {self.request_id})")
            self.start_download()
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            self.error_occurred.emit(str(e), self.request_id or "unknown")
        
        logger.debug("Worker thread stopping")

    def start_download(self):
        try:
            os.makedirs(self.download_dir, exist_ok=True)
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"{self.download_dir}/%(title)s.%(ext)s",
                "progress_hooks": [self.progress_hook],
                "retries": 3,
                "ratelimit": self.rate_limit,
            }

            with youtube_dlp.YoutubeDL(ydl_opts) as ydl:
                self.is_downloading = True
                ydl.download([self.download_url])

            self.is_downloading = False
            self.download_finished.emit(self.request_id)
            logger.info(f"Download completed: {self.download_url} (ID: {self.request_id})")
        except youtube_dlp.utils.DownloadCancelled:
            logger.warning(f"Download cancelled: {self.download_url} (ID: {self.request_id})")
        except Exception as e:
            logger.error(f"Download failed: {str(e)} (ID: {self.request_id})")
            self.error_occurred.emit(str(e), self.request_id)
        finally:
            self.is_downloading = False

    def progress_hook(self, data):
        if self.cancel_current:
            self.is_downloading = False
            raise youtube_dlp.utils.DownloadCancelled("Download cancelled by user")

        if data.get("status") == "downloading":
            downloaded = data.get("downloaded_bytes", 0)
            total = data.get("total_bytes") or data.get("total_bytes_estimate", 0)
            if total > 0:
                progress = (downloaded / total * 100)
                self.progress_updated.emit(self.request_id, progress, total)

    def add_download(self, video_url, request_id: str, download_dir="."):
        """Initialize and start a new download."""
        self.download_url = video_url  # Fixed variable reference
        self.request_id = request_id
        self.download_dir = download_dir
        self.cancel_current = False
        # self.run()

    @Slot()
    def stop_download(self):
        """Stop the current download."""
        self.cancel_current = True
        logger.debug("Stop signal received")

    def get_current_request_id(self):
        """Return the current request ID."""
        return self.request_id
    
    def isDownloading(self):
        """Check if a download is currently in progress."""
        return self.is_downloading

class SongDownloader(QObject):
    download_progress_signal = Signal(str, float, float)  # request_id, progress, total size
    download_error_signal = Signal(str, str)  # request_id, error message
    download_complete_signal = Signal(str)  # request_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread = QThread()
        self.worker = DownloadWorker()
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.download_finished.connect(self._handle_finished)
        self.worker.error_occurred.connect(self._handle_error)
        self.worker.progress_updated.connect(self._handle_progress)

        self.requests = {}  # Dictionary to hold queued downloads

    def start(self):
        """Start the downloader thread."""
        self.thread.start()

    def _handle_progress(self, request_id: str, progress: float, total_size: float):
        """Emit progress update signal."""
        self.download_progress_signal.emit(request_id, progress, total_size)

    def _handle_error(self, message, request_id):
        """Emit error signal."""
        self.download_error_signal.emit(request_id, message)

    def _handle_finished(self, request_id):
        """Handle completion of a download."""
        self.requests.pop(request_id, None)
        self.download_complete_signal.emit(request_id)

        if not self.worker.isDownloading():
            self._start_next_download()

    def _start_next_download(self):
        """Start the next download in the queue."""
        if self.requests:
            request_id, (video_url, download_dir) = next(iter(self.requests.items()))
            self.worker.add_download(video_url, request_id, download_dir)
            QTimer.singleShot(1000, self.worker.run)

    def add_request(self, video_url, download_dir="."):
        """Add a new download request."""
        request_id = self.generate_request_id(video_url)
        self.requests[request_id] = (video_url, download_dir)

        if not self.worker.isDownloading():
            self.worker.add_download(video_url, request_id, download_dir)
            QTimer.singleShot(1000, self.worker.run)
            # self.worker.run()

        return request_id
    
    def generate_request_id(self, video_url):
        """Generate a unique request ID based on the video URL."""
        return xxhash.xxh128_hexdigest(video_url)

    def pause_request(self, request_id):
        """Pause a specific request and move it to the end of the queue."""
        if request_id == self.worker.request_id:
            self.worker.stop_download()
            data = self.requests.pop(request_id, None)
            if data:
                self.requests[request_id] = data  # Move to the end of the queue
            self._start_next_download()

    def cancel_request(self, request_id):
        """Cancel a specific request."""
        if request_id == self.worker.request_id:
            self.worker.stop_download()
        self.requests.pop(request_id, None)

    def shutdown(self):
        """Shutdown the downloader gracefully."""
        self.worker.stop_download()
        self.thread.quit()
        self.thread.wait()

        
        
        
class DownloadCard(QWidget):
    canceled = Signal(str)
    def __init__(self, video_url, download_dir="."):
        super().__init__()
        self.request_id = None
        self.video_url = video_url
        self.download_dir = download_dir
        label = QLabel("song_1", self)
        self.progress_bar = QProgressBar(self)
        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.cancel_download)
        
        layout = QHBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.progress_bar, stretch=1)
        layout.addWidget(cancel_button)
        
    def update_progress(self, request_id, progress, total: str = None):
        logger.debug(f"Updating progress: {progress} for {request_id}")
        if request_id == self.request_id:
            self.progress_bar.setValue(int(progress))
            
    def cancel_download(self):
        # Implement cancellation logic here
        logger.critical("clicked")
        self.canceled.emit(self.request_id)
    
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.downloader = SongDownloader()
        self.downloader.start()
        self.download_cards = []

        self.layout = QVBoxLayout(self)
        
        urls =  [
            "https://www.youtube.com/watch?v=xTpv9lc_qMw",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        ]
        # UI setup...
        for url in urls:
            self.add_download(url)

    def add_download(self, video_url):
        download_card = DownloadCard(video_url)
        self.layout.addWidget(download_card)
        self.downloader.download_progress_signal.connect(download_card.update_progress)
        download_card.canceled.connect(lambda request: self.downloader.pause_request(request))
        download_card.request_id = self.downloader.add_request(video_url)
        # self.downloader.add_request(video_url)
        
        
if(__name__ == "__main__"):

    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    uid = xxhash.xxh128_hexdigest(video_url)
    print(uid)
    # app = QApplication([])
    # window = MainWindow()
    # window.show()
    # app.exec()