import uuid
import queue
import time
from enum import Enum
from queue import PriorityQueue

import ytmusicapi
from PySide6.QtCore import QThread, Signal, QMutex, QMutexLocker
import cachetools
from ytmusicapi import YTMusic
from typing import Tuple, Dict, Any, Optional
from loguru import logger

import sys
from src.utility.song_utils import get_stream_url


class YTMusicMethod(Enum):
    GET_HOME = "get_home"
    GET_ARTIST = "get_artist"
    GET_PLAYLIST = "get_playlist"
    GET_SONG = "get_song"
    GET_ALBUM = "get_album"
    SEARCH = "search"
    GET_MOOD_PLAYLISTS = "get_mood_playlists"
    GET_GENRE = "get_genre"
    GET_STREAM_URL = "get_stream_url"
    GET_WATCH_PLAYLIST = "get_watch_playlist"
    GET_LYRICS = "get_lyrics"

class RequestPriority(Enum):
    HIGH = 0
    NORMAL = 1
    LOW = 2

class DataFetcherWorker(QThread):
    data_fetched = Signal(object, str)  # (data, request_id)
    error_occurred = Signal(str, str)   # (error, request_id)

    RATE_LIMITS = {
        YTMusicMethod.SEARCH: 1.0,
        YTMusicMethod.GET_STREAM_URL: 0.5,
        YTMusicMethod.GET_HOME: 0.5,
        "default": 0.2
    }

    cache = cachetools.LRUCache(maxsize=256)
    mutex = QMutex()

    def __init__(self):
        super().__init__()
        self.request_queue = PriorityQueue(maxsize=50)
        self._ytmusic = YTMusic()
        self._active = True
        self._pending_requests = {}
        self._request_timeouts = {}
        self._rate_limit_adjustments = {}
        self._last_request_time = 0

    def run(self):
        """Main loop to process requests without blocking"""
        while self._active:
            self._cleanup_stale_requests()
            
            if not self.request_queue.empty():
                self._process_next_request()
            
            self._apply_rate_limits()
            
    def _cleanup_stale_requests(self):
        """Remove requests that have been pending too long"""
        with QMutexLocker(self.mutex):
            timeout_threshold = time.time() - 30  # Remove requests older than 30 seconds
            stale_keys = [key for key, timestamp in self._pending_requests.items() if timestamp < timeout_threshold]
            for key in stale_keys:
                del self._pending_requests[key]

    def _apply_rate_limits(self):
        """Non-blocking rate limiting"""
        now = time.time()
        min_interval = min(self.RATE_LIMITS.values())  # Get lowest rate limit
        elapsed = now - self._last_request_time

        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

        self._last_request_time = time.time()

    def _process_next_request(self):
        """Process the next request from the queue"""
        try:
            priority, content_hash, request_id, method, args, kwargs = self.request_queue.get_nowait()
            # request_id = str(uuid.uuid4())
            print(request_id)
            with QMutexLocker(self.mutex):
                if content_hash in self._pending_requests:
                    return  # Skip duplicate requests

                self._pending_requests[content_hash] = time.time()
            
            self._process_request(request_id, method, args, kwargs, content_hash)

        except queue.Empty:
            pass
        except Exception as e:
            logger.error(f"Request processing failed: {str(e)}")

    def _process_request(self, request_id: str, method: YTMusicMethod, args: Tuple, kwargs: Dict[str, Any], content_hash: int):
        """Executes the request and emits results"""
        try:
            cache_key = (method.value, args, frozenset(kwargs.items()))
            if cache_key in self.cache:
                self.data_fetched.emit(self.cache[cache_key], request_id)
                return

            result = self._fetch_data(method, args, kwargs)
            self.cache[cache_key] = result
            self.data_fetched.emit(result, request_id)

        except Exception as e:
            self.error_occurred.emit(str(e), request_id)
            logger.error(f"Request {request_id} failed: {str(e)}")
        finally:
            with QMutexLocker(self.mutex):
                self._pending_requests.pop(content_hash, None)

    def _fetch_data(self, method: YTMusicMethod, args: Tuple, kwargs: Dict[str, Any]) -> Any:
        """Fetch data from YTMusic API"""
        try:
            match method:
                case YTMusicMethod.GET_HOME: return self._ytmusic.get_home(*args, **kwargs)
                case YTMusicMethod.SEARCH: return self._ytmusic.search(*args, **kwargs)
                case YTMusicMethod.GET_PLAYLIST: return self._ytmusic.get_playlist(*args, **kwargs)
                case YTMusicMethod.GET_ALBUM: return self._ytmusic.get_album(*args, **kwargs)
                case YTMusicMethod.GET_ARTIST: return self._ytmusic.get_artist(*args, **kwargs)
                case YTMusicMethod.GET_GENRE: return self._ytmusic.get_mood_categories(*args, **kwargs)
                case YTMusicMethod.GET_MOOD_PLAYLISTS: return self._ytmusic.get_mood_playlists(*args, **kwargs)
                case YTMusicMethod.GET_SONG: return self._ytmusic.get_song(*args, **kwargs)
                case YTMusicMethod.GET_WATCH_PLAYLIST: return self._ytmusic.get_watch_playlist(*args, **kwargs)
                case YTMusicMethod.GET_STREAM_URL: return get_stream_url(*args, **kwargs)
                case YTMusicMethod.GET_LYRICS: return self._ytmusic.get_lyrics(*args, **kwargs)

        except Exception as e:
            if "429" in str(e):  # Rate limited
                self._adjust_rate_limit(method)
            raise

    def _adjust_rate_limit(self, method: YTMusicMethod):
        """Dynamically adjust rate limits"""
        current_limit = self.RATE_LIMITS.get(method, self.RATE_LIMITS["default"])
        new_limit = current_limit * 1.5
        self._rate_limit_adjustments[method] = new_limit
        logger.warning(f"Adjusted rate limit for {method} to {new_limit}s")

    def add_request(self, method: YTMusicMethod, *args, priority: RequestPriority = RequestPriority.NORMAL, **kwargs) -> Optional[str]:
        """Add request with duplicate prevention"""
        """Add request with duplicate prevention and it emit signal with data and request id

        Returns:
            str: request id of request
            None: if request is wrong it return none
        """
        try:
            request_id = str(uuid.uuid4())
            content_hash = hash((method, args, frozenset(kwargs.items())))

            with QMutexLocker(self.mutex):
                if content_hash in self._pending_requests:
                    return None  # Avoid duplicate requests

            self.request_queue.put((priority.value, content_hash, request_id, method, args, kwargs))
            return request_id

        except queue.Full:
            self.error_occurred.emit("Request queue full", "")
            return None

    def stop(self):
        """Stop the worker thread"""
        self._active = False
        self.wait(2500)
        logger.info("Worker thread stopped")

# --- Testing Code ---
def on_finished(data, request_id):
    """Callback when data is fetched"""
    import json
    print(f"Request ID: {request_id}")
    print(f"data: {data}")
    # with open("data/app/home.json", "w") as file:
    #     json.dump(data, file, indent=4)
    worker.stop()
    worker.exit(0)
    sys.exit(0)

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication([])

    worker = DataFetcherWorker()
    worker.start()  # Ensure worker is running before adding requests

    worker.data_fetched.connect(on_finished)
    worker.error_occurred.connect(lambda err, req_id: print(f"Error: {err} (Request ID: {req_id})"))

    # Adding multiple requests
    # print(worker.add_request(YTMusicMethod.GET_HOME))
    print(worker.add_request(YTMusicMethod.SEARCH, "arijit"))
    # worker.add_request(YTMusicMethod.SEARCH, "test", filter="songs")
    # worker.add_request(YTMusicMethod.GET_STREAM_URL, "YALvuUpY_b0")
    # worker.add_request(YTMusicMethod.GET_GENRE)

    app.exec()
