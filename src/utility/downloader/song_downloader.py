from loguru import logger
import os
import uuid
from collections import OrderedDict
from queue import Queue, Empty

import yt_dlp as youtube_dlp
from PySide6.QtWidgets import QApplication, QProgressBar, QLabel, QHBoxLayout, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import QObject, QThread, Signal, Slot, QMutex, QWaitCondition, QMutexLocker, Qt, Q_ARG, QMetaObject

class DownloadWorker(QObject):
    progress_updated = Signal(str, float, float)  # request_id, progress_percent, total size
    error_occurred = Signal(str, str)            # request_id, error_message
    download_finished = Signal(str)              # request_id
    download_cancelled = Signal(str)             # request_id

    def __init__(self, rate_limit=50000):
        super().__init__()
        self._mutex = QMutex()
        self.current_request = None
        self.rate_limit = rate_limit
        self._cancel_requested = False

    @Slot(str, str, str)
    def start_download(self, request_id, url, download_dir):
        with QMutexLocker(self._mutex):
            self._cancel_requested = False
            self.current_request = request_id

        try:
            os.makedirs(download_dir, exist_ok=True)
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"{download_dir}/%(title)s.%(ext)s",
                "progress_hooks": [lambda d: self._progress_hook(d, request_id)],
                "retries": 3,
                "ratelimit": self.rate_limit,
            }

            logger.info(f"Starting download {request_id}: {url}")
            with youtube_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            if self._cancel_requested:
                logger.info(f"Download cancelled {request_id}")
                self.download_cancelled.emit(request_id)
            else:
                logger.info(f"Download completed {request_id}")
                self.download_finished.emit(request_id)

        except youtube_dlp.utils.DownloadCancelled:
            logger.info(f"Download cancelled by user {request_id}")
            self.download_cancelled.emit(request_id)
        except Exception as e:
            logger.error(f"Download failed {request_id}: {str(e)}")
            self.error_occurred.emit(request_id, str(e))
        finally:
            with QMutexLocker(self._mutex):
                self.current_request = None
                self._cancel_requested = False

    def _progress_hook(self, data, request_id):
        if self._cancel_requested:
            raise youtube_dlp.utils.DownloadCancelled("Download cancelled by user")

        if data.get("status") == "downloading":
            downloaded = data.get("downloaded_bytes", 0)
            total = data.get("total_bytes") or data.get("total_bytes_estimate", 0)
            if total > 0:
                progress = (downloaded / total) * 100
                self.progress_updated.emit(request_id, progress, total)

    @Slot(str)
    def cancel_current(self, request_id):
        logger.debug(f"Cancel requested for {request_id}")
        with QMutexLocker(self._mutex):
            if self.current_request == request_id:
                self._cancel_requested = True

class SongDownloader(QObject):
    download_progress = Signal(str, float, float)  # request_id, progress, total
    download_complete = Signal(str)                 # request_id
    download_error = Signal(str, str)               # request_id, error
    download_cancelled = Signal(str)                # request_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mutex = QMutex()
        self.worker_thread = QThread()
        self.worker = DownloadWorker()
        self.worker.moveToThread(self.worker_thread)
        
        # Using OrderedDict to maintain request order
        self.requests = OrderedDict()  # {request_id: (url, dir, status)}
        self.active_request = None

        # Worker signals
        self.worker.progress_updated.connect(self.download_progress)
        self.worker.download_finished.connect(self._handle_finished)
        self.worker.error_occurred.connect(self._handle_error)
        self.worker.download_cancelled.connect(self._handle_cancelled)

    # def start(self):
        self.worker_thread.start()

    def add_request(self, url, download_dir=".", priority=False):
        request_id = str(uuid.uuid4())
        with QMutexLocker(self._mutex):
            # Insert at beginning if priority, else append
            if priority:
                self.requests.update({request_id: (url, download_dir, "queued")})
                self.requests.move_to_end(request_id, last=False)
            else:
                self.requests[request_id] = (url, download_dir, "queued")
            
        logger.info(f"Added request {request_id}")
        self._start_next()
        return request_id

    def _start_next(self):
        with QMutexLocker(self._mutex):
            if self.active_request is not None:
                return

            for rid, (url, ddir, status) in self.requests.items():
                if status == "queued":
                    self.active_request = rid
                    # Update status to downloading
                    self.requests[rid] = (url, ddir, "downloading")
                    QMetaObject.invokeMethod(
                        self.worker,
                        "start_download",
                        Qt.QueuedConnection,
                        Q_ARG(str, rid),
                        Q_ARG(str, url),
                        Q_ARG(str, ddir)
                    )
                    return

    def _handle_finished(self, request_id):
        with QMutexLocker(self._mutex):
            if request_id in self.requests:
                del self.requests[request_id]
            self.active_request = None
            self.download_complete.emit(request_id)
        self._start_next()

    def _handle_error(self, request_id, error):
        with QMutexLocker(self._mutex):
            if request_id in self.requests:
                del self.requests[request_id]
            self.active_request = None
            self.download_error.emit(request_id, error)
        self._start_next()

    def _handle_cancelled(self, request_id):
        with QMutexLocker(self._mutex):
            if request_id in self.requests:
                # Move to end if we want to keep in queue
                # Or delete to remove completely
                del self.requests[request_id]
            self.active_request = None
            self.download_cancelled.emit(request_id)
        self._start_next()

    def cancel_request(self, request_id):
        logger.debug(f"Cancel requested for {request_id}")
        with QMutexLocker(self._mutex):
            if request_id == self.active_request:
                logger.debug(f"Canceling active request {request_id}")
                self.worker.cancel_current(request_id) #wrk but dont know why metaobject not 
                # QMetaObject.invokeMethod(
                #     self.worker,
                #     "cancel_current",
                #     Qt.QueuedConnection,
                #     Q_ARG(str, request_id)
                # )
            elif request_id in self.requests:
                logger.debug(f"Canceling queued request {request_id}")
                del self.requests[request_id]

    def pause_request(self, request_id):
        with QMutexLocker(self._mutex):
            url, ddir, _ = self.requests[request_id]
            self.requests[request_id] = (url, ddir, "paused")
            self.cancel_request(request_id)
            
                
            # elif request_id in self.requests:
            #     url, ddir, _ = self.requests[request_id]
                # self.requests[request_id] = (url, ddir, "paused")

    def resume_request(self, request_id):
        with QMutexLocker(self._mutex):
            if request_id in self.requests:
                url, ddir, _ = self.requests[request_id]
                self.requests[request_id] = (url, ddir, "queued")
                self.requests.move_to_end(request_id, last=False)
                self._start_next()

    def shutdown(self):
        self.worker_thread.quit()
        self.worker_thread.wait()
        
        
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
        # self.downloader.start()
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
        self.downloader.download_progress.connect(download_card.update_progress)
        download_card.canceled.connect(lambda request: self.downloader.cancel_request(request))
        download_card.request_id = self.downloader.add_request(video_url)
        logger.critical(download_card.request_id)
        # self.downloader.add_request(video_url)
        
        
if(__name__ == "__main__"):

    # video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    # uid = xxhash.xxh128_hexdigest(video_url)
    # print(uid)
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()