import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.encryption import EncryptionManager
from core.keylogger import KeystrokeEngine
from core.clipboard import ClipboardMonitor
from core.screenshot import ScreenshotCapture
from core.window_tracker import WindowTracker
from storage.file_handler import FileHandler
from utils.system_info import SystemProfiler
from utils.consent import ConsentManager

from ui.gui_dashboard import CyberSentinelApp

def main():

    crypto          = EncryptionManager()
    keylogger       = KeystrokeEngine(encryption_manager=crypto)
    clipboard       = ClipboardMonitor(encryption_manager=crypto)
    screenshot      = ScreenshotCapture()
    window_tracker  = WindowTracker()

    file_handler    = FileHandler(encryption_manager=crypto)
    sys_profiler    = SystemProfiler()
    consent_mgr     = ConsentManager()

    app = CyberSentinelApp(
        keylogger=keylogger,
        clipboard=clipboard,
        screenshot=screenshot,
        window_tracker=window_tracker,
        encryption=crypto,
        file_handler=file_handler,
        system_profiler=sys_profiler,
        consent_manager=consent_mgr,
    )

    app.mainloop()

if __name__ == "__main__":
    main()
