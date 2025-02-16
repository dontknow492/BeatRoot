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
from PySide6.QtCore import QObject, QThread, Signal, QMutex, QWaitCondition, QMutexLocker
import yt_dlp as youtube_dlp
from loguru import logger


class DownloadWorker(QObject):
    progress_updated = Signal(str, float, float)  #  request_id, progress_percent, total size
    error_occurred = Signal(str, str)    # error_message, request_id
    download_finished = Signal(str)      # request_id
    removed = Signal(str)                # removed request_id

    def __init__(self, rate_limit=50000):
        super().__init__()
        self.download_queue = Queue()
        self.download_urls = set()
        self.removed_urls = set()
        self.lock = QMutex()  # Single lock to avoid deadlocks
        self.condition = QWaitCondition()
        self.current_request_id = None
        self.running = False
        self.cancel_current = False
        self.rate_limit = rate_limit  # Rate limit in bytes per second

    @Slot()
    def run(self):
        self.running = True
        while self.running:
            try:
                item = self.download_queue.get(timeout=0.5)
                request_id, video_url, download_dir = item
                
                with QMutexLocker(self.lock):
                    if video_url in self.removed_urls:
                        logger.info(f"Skipping removed download: {video_url} (ID: {request_id})")
                        self.download_queue.task_done()
                        continue
                
                self.current_request_id = request_id
                self.cancel_current = False  # Reset before each download
                logger.info(f"Starting download: {video_url} (ID: {request_id})")
                self.start_download(request_id, video_url, download_dir)
                self.download_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                self.error_occurred.emit(str(e), "unknown")
        
        logger.debug("Worker thread stopping")
        
    @logger.catch
    def start_download(self, request_id, video_url, download_dir):
        try:
            os.makedirs(download_dir, exist_ok=True)
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"{download_dir}/%(title)s.%(ext)s",
                "progress_hooks": [lambda d: self.progress_hook(d, request_id)],
                "retries": 3,
                "ratelimit": self.rate_limit,
            }

            with youtube_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            self.download_finished.emit(request_id)
            logger.info(f"Download completed: {video_url} (ID: {request_id})")
        except youtube_dlp.DownloadCancelled:
            logger.warning(f"Download cancelled: {video_url} (ID: {request_id})")
        except Exception as e:
            logger.error(f"Download failed: {str(e)} (ID: {request_id})")
            self.error_occurred.emit(str(e), request_id)
        finally:
            with QMutexLocker(self.lock):
                self.download_urls.discard(video_url)
                self.removed_urls.discard(video_url)
            self.current_request_id = None

    def progress_hook(self, data, request_id):
        if self.cancel_current:
            raise youtube_dlp.DownloadCancelled("Download cancelled by user")
        
        if data.get("status") == "downloading":
            downloaded = data.get("downloaded_bytes", 0)
            total = data.get("total_bytes") or data.get("total_bytes_estimate", 0)
            if total > 0:
                progress = (downloaded / total * 100)
                self.progress_updated.emit(request_id, progress, total)

    def add_request(self, video_url, download_dir="."):
        with QMutexLocker(self.lock):
            if video_url in self.download_urls:
                logger.warning(f"URL already in queue: {video_url}")
                return None

            request_id = str(uuid.uuid4())
            self.download_urls.add(video_url)
            self.download_queue.put((request_id, video_url, download_dir))
            self.condition.wakeAll()
            logger.info(f"Added to queue: {video_url} (ID: {request_id})")
            return request_id

    @Slot()
    def stop(self):
        self.running = False
        self.cancel_current = True
        self.condition.wakeAll()  # Wake up any waiting thread
        logger.debug("Stop signal received")

    @Slot()    
    def remove_download(self, video_url):
        with QMutexLocker(self.lock):
            if video_url in self.download_urls:
                self.removed_urls.add(video_url)
                logger.info(f"Marked for removal: {video_url}")
            else:
                logger.warning(f"Tried to remove non-queued URL: {video_url}")
        self.removed.emit(video_url)


class SongDownloader(QObject):
    download_progress_signal = Signal(str, float, float)  # progress_percent, request_id
    download_error_signal = Signal(str, str)    # error_message, request_id
    download_complete_signal = Signal(str)      # request_id
    def __init__(self, parent=None):
        super().__init__(parent = parent)
        self.thread = QThread()
        self.worker = DownloadWorker()
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.download_finished.connect(self._handle_finished)
        self.worker.error_occurred.connect(self._handle_error)
        self.worker.progress_updated.connect(self._handle_progress)

        # self.thread.start()
        
    def start(self):
        self.thread.start()

    def _handle_progress(self, request_id: str, progress: float, total_size: float ):
        # logger.debug(f"Progress for {request_id}: {progress}%")
        self.download_progress_signal.emit(request_id, progress, total_size)

    def _handle_error(self, message, request_id):
        # logger.error(f"Error for {request_id}: {message}")
        self.download_error_signal.emit(request_id, message)

    def _handle_finished(self, request_id):
        # logger.info(f"Download finished for {request_id}")
        self.download_complete_signal.emit(request_id)

    def add_request(self, video_url, download_dir="."):
        return self.worker.add_request(video_url, download_dir)

    def shutdown(self):
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()
        logger.info("Downloader shutdown complete")
        
        
        
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
        
    def update_progress(self, progress, request_id):
        if request_id == self.request_id:
            self.progress_bar.setValue(progress)
    def cancel_download(self):
        # Implement cancellation logic here
        logger.critical("clicked")
        self.canceled.emit(self.video_url)
    
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.downloader = SongDownloader()
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
        self.downloader.worker.progress_updated.connect(download_card.update_progress)
        download_card.canceled.connect(lambda url: self.downloader.worker.remove_download(url))
        download_card.request_id = self.downloader.add_request(video_url)
        # self.downloader.add_request(video_url)
        
        
if(__name__ == "__main__"):
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()