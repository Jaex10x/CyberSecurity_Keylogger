import threading
import time
from datetime import datetime
from pathlib import Path

try:
    from PIL import ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from config.settings import (
    SCREENSHOT_ENABLED,
    SCREENSHOT_DIR,
    SCREENSHOT_INTERVAL,
    SCREENSHOT_QUALITY,
    SCREENSHOT_FORMAT,
    SESSION_ID,
)

class ScreenshotCapture:

    def __init__(self):
        self.enabled = SCREENSHOT_ENABLED and PIL_AVAILABLE
        self.interval = SCREENSHOT_INTERVAL
        self.quality = SCREENSHOT_QUALITY
        self.format = SCREENSHOT_FORMAT
        self.output_dir = SCREENSHOT_DIR

        self._running = False
        self._thread = None
        self.total_captures = 0
        self._last_capture_path = None
        self._last_capture_time = None

        self._on_capture_callback = None

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def set_capture_callback(self, callback):
        self._on_capture_callback = callback

    def start(self):
        if not self.enabled:
            return

        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._capture_loop,
            name="ScreenshotCapture",
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def capture_now(self) -> Path:
        if not PIL_AVAILABLE:
            return None

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"screenshot_{SESSION_ID}_{timestamp}.{self.format}"
            filepath = self.output_dir / filename

            screenshot = ImageGrab.grab()

            if self.format.lower() in ("jpg", "jpeg"):
                screenshot.save(filepath, "JPEG", quality=self.quality)
            else:
                screenshot.save(filepath, "PNG")

            self.total_captures += 1
            self._last_capture_path = filepath
            self._last_capture_time = datetime.now()

            if self._on_capture_callback:
                try:
                    self._on_capture_callback({
                        "path": str(filepath),
                        "timestamp": self._last_capture_time.isoformat(),
                        "size_kb": round(filepath.stat().st_size / 1024, 1),
                    })
                except Exception:
                    pass

            return filepath

        except Exception:
            return None

    def _capture_loop(self):
        while self._running:
            self.capture_now()
            time.sleep(self.interval)

    def get_stats(self) -> dict:
        return {
            "enabled": self.enabled,
            "running": self._running,
            "total_captures": self.total_captures,
            "interval_seconds": self.interval,
            "format": self.format,
            "quality": self.quality,
            "output_dir": str(self.output_dir),
            "last_capture": (
                self._last_capture_time.isoformat()
                if self._last_capture_time else None
            ),
            "pil_available": PIL_AVAILABLE,
        }

    def get_recent_captures(self) -> list:
        try:
            files = sorted(
                self.output_dir.glob(f"screenshot_{SESSION_ID}_*"),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )
            return [
                {
                    "filename": f.name,
                    "size_kb": round(f.stat().st_size / 1024, 1),
                    "timestamp": datetime.fromtimestamp(
                        f.stat().st_mtime
                    ).isoformat(),
                }
                for f in files[:20]
            ]
        except Exception:
            return []

    @property
    def is_running(self) -> bool:
        return self._running
