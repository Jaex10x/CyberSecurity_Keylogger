import customtkinter as ctk
import tkinter as tk
import threading
import queue
import os
from datetime import datetime, timedelta
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from config.settings import (
    APP_NAME,
    APP_VERSION,
    APP_TAGLINE,
    SESSION_ID,
    AUTO_STOP_HOURS,
    BUFFER_SIZE,
    FLUSH_INTERVAL_SECONDS,
    CAPTURE_SPECIAL_KEYS,
    CAPTURE_TIMESTAMPS,
    CLIPBOARD_ENABLED,
    CLIPBOARD_POLL_INTERVAL,
    SCREENSHOT_ENABLED,
    SCREENSHOT_INTERVAL,
    SCREENSHOT_QUALITY,
    SCREENSHOT_FORMAT,
    SCREENSHOT_DIR,
    EMAIL_ENABLED,
    LOG_DIR,
    EXPORT_DIR,
)


BG_DARKEST     = "#07071a"
BG_DARK        = "#0a0a1a"
BG_PANEL       = "#1a1a2e"
BG_CARD        = "#16213e"
BG_INPUT       = "#111128"
BG_SIDEBAR     = "#0f0f23"
BG_HOVER       = "#1a1a3e"
BG_ACTIVE      = "#141430"
ACCENT         = "#00d4ff"
ACCENT2        = "#e040fb"
GREEN          = "#00e676"
ORANGE         = "#ff9100"
RED            = "#ff1744"
YELLOW         = "#ffd600"
TEXT_PRIMARY   = "#e0e0e0"
TEXT_SECONDARY = "#9e9e9e"
TEXT_DIM       = "#616161"
BORDER         = "#0f3460"
BORDER_LIGHT   = "#1a2a5e"

SIDEBAR_W = 220
REFRESH_MS = 1000


NAV_ITEMS = [
    ("dashboard",   "🏠", "Dashboard"),
    ("keylogger",   "⌨️",  "Keylogger"),
    ("clipboard",   "📋", "Clipboard"),
    ("screenshots", "📸", "Screenshots"),
    ("encryption",  "🔐", "Logs & Crypto"),
    ("sysinfo",     "🖥️",  "System Info"),
    ("settings",    "⚙️",  "Settings"),
]


class StatusCard(ctk.CTkFrame):

    def __init__(self, master, icon: str, value: str, label: str,
                 accent_color: str = ACCENT, **kw):
        super().__init__(master, fg_color=BG_CARD, corner_radius=12,
                         border_width=1, border_color=BORDER, **kw)

        pad = ctk.CTkFrame(self, fg_color="transparent")
        pad.pack(fill="both", expand=True, padx=18, pady=14)

        bar = ctk.CTkFrame(pad, height=3, fg_color=accent_color,
                           corner_radius=2)
        bar.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            pad, text=icon,
            font=ctk.CTkFont(size=26),
        ).pack(anchor="w")

        self._value_label = ctk.CTkLabel(
            pad, text=value,
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        self._value_label.pack(anchor="w", pady=(4, 0))

        ctk.CTkLabel(
            pad, text=label,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w")

    def set_value(self, value: str):
        self._value_label.configure(text=value)


class GaugeBar(ctk.CTkFrame):

    def __init__(self, master, label: str, icon: str,
                 color: str = ACCENT, **kw):
        super().__init__(master, fg_color=BG_CARD, corner_radius=12,
                         border_width=1, border_color=BORDER, **kw)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=18, pady=12)

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x")

        ctk.CTkLabel(
            row, text=f"{icon}  {label}",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        self._pct_label = ctk.CTkLabel(
            row, text="0 %",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=color,
        )
        self._pct_label.pack(side="right")

        self._bar = ctk.CTkProgressBar(
            inner, height=10, corner_radius=5,
            fg_color=BG_DARK, progress_color=color,
        )
        self._bar.pack(fill="x", pady=(8, 0))
        self._bar.set(0)

    def set_value(self, percent: float):
        self._bar.set(percent / 100)
        self._pct_label.configure(text=f"{percent:.0f} %")
        if percent > 85:
            c = RED
        elif percent > 65:
            c = ORANGE
        else:
            c = GREEN
        self._bar.configure(progress_color=c)
        self._pct_label.configure(text_color=c)


class CyberSentinelApp(ctk.CTk):


    def __init__(
        self,
        keylogger=None,
        clipboard=None,
        screenshot=None,
        window_tracker=None,
        encryption=None,
        file_handler=None,
        system_profiler=None,
        consent_manager=None,
    ):
        super().__init__()

        self.keylogger        = keylogger
        self.clip_monitor     = clipboard
        self.screenshot_cap   = screenshot
        self.window_tracker   = window_tracker
        self.encryption       = encryption
        self.file_handler     = file_handler
        self.sys_profiler     = system_profiler
        self.consent_mgr      = consent_manager

        self._monitoring      = False
        self._key_queue       = queue.Queue()
        self._clip_queue      = queue.Queue()
        self._current_page    = None
        self._pages           = {}
        self._nav_btns        = {}
        self._w               = {}

        ctk.set_appearance_mode("dark")
        self.title(f"{APP_NAME}  ·  v{APP_VERSION}")
        self.geometry("1320x820")
        self.minsize(1060, 640)
        self.configure(fg_color=BG_DARK)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self._build_sidebar()
        self._content = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        self._content.pack(side="right", fill="both", expand=True)

        self._build_page_dashboard()
        self._build_page_keylogger()
        self._build_page_clipboard()
        self._build_page_screenshots()
        self._build_page_encryption()
        self._build_page_sysinfo()
        self._build_page_settings()

        self._select_page("dashboard")

        if self.keylogger:
            self.keylogger.set_key_callback(self._on_key_event)
        if self.clip_monitor:
            self.clip_monitor.set_capture_callback(self._on_clip_event)

        self.after(REFRESH_MS, self._tick)


    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=SIDEBAR_W, fg_color=BG_SIDEBAR,
                          corner_radius=0)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        logo_f = ctk.CTkFrame(sb, fg_color="transparent", height=80)
        logo_f.pack(fill="x", padx=16, pady=(22, 6))
        logo_f.pack_propagate(False)

        ctk.CTkLabel(logo_f, text="🛡️",
                     font=ctk.CTkFont(size=30)).pack(anchor="w")
        ctk.CTkLabel(logo_f, text=APP_NAME,
                     font=ctk.CTkFont(family="Segoe UI", size=17,
                                      weight="bold"),
                     text_color=ACCENT).pack(anchor="w")
        ctk.CTkLabel(logo_f, text=APP_TAGLINE,
                     font=ctk.CTkFont(size=10),
                     text_color=TEXT_DIM).pack(anchor="w")

        ctk.CTkFrame(sb, height=1, fg_color=BORDER).pack(
            fill="x", padx=16, pady=10)

        for key, icon, label in NAV_ITEMS:
            btn = ctk.CTkButton(
                sb, text=f"  {icon}  {label}",
                font=ctk.CTkFont(family="Segoe UI", size=14),
                fg_color="transparent", text_color=TEXT_SECONDARY,
                hover_color=BG_HOVER, anchor="w",
                height=42, corner_radius=8,
                command=lambda k=key: self._select_page(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._nav_btns[key] = btn

        ctk.CTkFrame(sb, fg_color="transparent").pack(
            fill="both", expand=True)

        self._w["sb_status"] = ctk.CTkLabel(
            sb, text="● Idle", font=ctk.CTkFont(size=12),
            text_color=TEXT_DIM)
        self._w["sb_status"].pack(padx=16, pady=(0, 4), anchor="w")

        ctk.CTkLabel(sb, text=f"Session {SESSION_ID}",
                     font=ctk.CTkFont(size=9),
                     text_color=TEXT_DIM).pack(padx=16, pady=(0, 14),
                                               anchor="w")

    def _select_page(self, name):
        for k, b in self._nav_btns.items():
            if k == name:
                b.configure(fg_color=BG_ACTIVE, text_color=ACCENT)
            else:
                b.configure(fg_color="transparent", text_color=TEXT_SECONDARY)
        for k, p in self._pages.items():
            p.pack_forget()
        self._pages[name].pack(in_=self._content, fill="both", expand=True)
        self._current_page = name


    def _build_page_dashboard(self):
        page = ctk.CTkScrollableFrame(self, fg_color=BG_DARK,
                                       corner_radius=0)
        self._pages["dashboard"] = page

        self._page_title(page, "🏠  Dashboard", "Real-time monitoring overview")

        cards_row = ctk.CTkFrame(page, fg_color="transparent")
        cards_row.pack(fill="x", padx=24, pady=(0, 12))
        cards_row.columnconfigure((0, 1, 2, 3), weight=1, uniform="c")

        self._w["card_keys"] = StatusCard(
            cards_row, "⌨️", "0", "Total Keystrokes", ACCENT)
        self._w["card_keys"].grid(row=0, column=0, padx=6, pady=6,
                                   sticky="nsew")

        self._w["card_clip"] = StatusCard(
            cards_row, "📋", "0", "Clipboard Captures", ACCENT2)
        self._w["card_clip"].grid(row=0, column=1, padx=6, pady=6,
                                   sticky="nsew")

        self._w["card_shots"] = StatusCard(
            cards_row, "📸", "0", "Screenshots", GREEN)
        self._w["card_shots"].grid(row=0, column=2, padx=6, pady=6,
                                    sticky="nsew")

        self._w["card_window"] = StatusCard(
            cards_row, "🪟", "—", "Active Window", ORANGE)
        self._w["card_window"].grid(row=0, column=3, padx=6, pady=6,
                                     sticky="nsew")

        mid_row = ctk.CTkFrame(page, fg_color="transparent")
        mid_row.pack(fill="x", padx=24, pady=(0, 12))
        mid_row.columnconfigure((0, 1), weight=1, uniform="m")

        mod_panel = ctk.CTkFrame(mid_row, fg_color=BG_CARD,
                                  corner_radius=12, border_width=1,
                                  border_color=BORDER)
        mod_panel.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")

        mp = ctk.CTkFrame(mod_panel, fg_color="transparent")
        mp.pack(fill="both", expand=True, padx=18, pady=14)

        ctk.CTkLabel(mp, text="🔌  Module Status",
                     font=ctk.CTkFont(family="Segoe UI", size=14,
                                      weight="bold"),
                     text_color=ACCENT).pack(anchor="w", pady=(0, 10))

        self._w["mod_labels"] = {}
        for mod_key, mod_icon, mod_name in [
            ("keylogger", "⌨️", "Keystroke Engine"),
            ("clipboard", "📋", "Clipboard Monitor"),
            ("screenshot", "📸", "Screenshot Capture"),
            ("window", "🪟", "Window Tracker"),
            ("encryption", "🔐", "Encryption"),
        ]:
            row_f = ctk.CTkFrame(mp, fg_color="transparent")
            row_f.pack(fill="x", pady=3)
            ctk.CTkLabel(row_f, text=f"{mod_icon}  {mod_name}",
                         font=ctk.CTkFont(size=13),
                         text_color=TEXT_PRIMARY).pack(side="left")
            lbl = ctk.CTkLabel(row_f, text="● OFF",
                               font=ctk.CTkFont(size=12, weight="bold"),
                               text_color=RED)
            lbl.pack(side="right")
            self._w["mod_labels"][mod_key] = lbl

        ses_panel = ctk.CTkFrame(mid_row, fg_color=BG_CARD,
                                  corner_radius=12, border_width=1,
                                  border_color=BORDER)
        ses_panel.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")

        sp = ctk.CTkFrame(ses_panel, fg_color="transparent")
        sp.pack(fill="both", expand=True, padx=18, pady=14)

        ctk.CTkLabel(sp, text="📊  Session Info",
                     font=ctk.CTkFont(family="Segoe UI", size=14,
                                      weight="bold"),
                     text_color=ACCENT).pack(anchor="w", pady=(0, 10))

        self._w["ses_labels"] = {}
        for s_key, s_label in [
            ("id", "Session ID"),
            ("started", "Started"),
            ("elapsed", "Elapsed"),
            ("kpm", "Keys / min"),
            ("autostop", "Auto-stop"),
        ]:
            rf = ctk.CTkFrame(sp, fg_color="transparent")
            rf.pack(fill="x", pady=3)
            ctk.CTkLabel(rf, text=s_label,
                         font=ctk.CTkFont(size=13),
                         text_color=TEXT_SECONDARY).pack(side="left")
            lbl = ctk.CTkLabel(rf, text="—",
                               font=ctk.CTkFont(size=13, weight="bold"),
                               text_color=TEXT_PRIMARY)
            lbl.pack(side="right")
            self._w["ses_labels"][s_key] = lbl

        self._w["ses_labels"]["id"].configure(text=SESSION_ID)
        self._w["ses_labels"]["autostop"].configure(
            text=f"{AUTO_STOP_HOURS}h")

        gauge_row = ctk.CTkFrame(page, fg_color="transparent")
        gauge_row.pack(fill="x", padx=24, pady=(0, 12))
        gauge_row.columnconfigure((0, 1), weight=1, uniform="g")

        self._w["gauge_cpu"] = GaugeBar(gauge_row, "CPU Usage", "🧠",
                                         ACCENT)
        self._w["gauge_cpu"].grid(row=0, column=0, padx=6, pady=6,
                                   sticky="nsew")

        self._w["gauge_ram"] = GaugeBar(gauge_row, "Memory Usage", "💾",
                                         ACCENT2)
        self._w["gauge_ram"].grid(row=0, column=1, padx=6, pady=6,
                                   sticky="nsew")

        btn_frame = ctk.CTkFrame(page, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(4, 20))

        self._w["btn_toggle"] = ctk.CTkButton(
            btn_frame,
            text="▶  START MONITORING",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            fg_color=GREEN, hover_color="#00c864",
            text_color="#0a0a1a",
            height=52, corner_radius=12,
            command=self._toggle_monitoring,
        )
        self._w["btn_toggle"].pack(fill="x")


    def _build_page_keylogger(self):
        page = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        self._pages["keylogger"] = page

        self._page_title(page, "⌨️  Keylogger",
                         "Live keystroke capture feed")

        stat_bar = ctk.CTkFrame(page, fg_color=BG_CARD, corner_radius=10,
                                 height=44, border_width=1,
                                 border_color=BORDER)
        stat_bar.pack(fill="x", padx=24, pady=(0, 10))
        stat_bar.pack_propagate(False)

        sb_inner = ctk.CTkFrame(stat_bar, fg_color="transparent")
        sb_inner.pack(fill="both", expand=True, padx=16)

        for s_key, s_text, s_color in [
            ("kl_total", "Keys: 0", ACCENT),
            ("kl_kpm", "KPM: 0", GREEN),
            ("kl_buffer", "Buffer: 0", ORANGE),
        ]:
            lbl = ctk.CTkLabel(sb_inner, text=s_text,
                               font=ctk.CTkFont(family="Segoe UI",
                                                 size=13, weight="bold"),
                               text_color=s_color)
            lbl.pack(side="left", padx=(0, 28))
            self._w[s_key] = lbl

        self._w["kl_status"] = ctk.CTkLabel(
            sb_inner, text="● Stopped",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=RED)
        self._w["kl_status"].pack(side="right")

        self._w["kl_textbox"] = ctk.CTkTextbox(
            page,
            font=ctk.CTkFont(family="Consolas", size=14),
            fg_color=BG_PANEL, text_color=GREEN,
            border_color=BORDER, border_width=1,
            corner_radius=10, wrap="word",
        )
        self._w["kl_textbox"].pack(fill="both", expand=True,
                                    padx=24, pady=(0, 10))
        self._w["kl_textbox"].configure(state="disabled")

        ctrl = ctk.CTkFrame(page, fg_color="transparent")
        ctrl.pack(fill="x", padx=24, pady=(0, 18))

        ctk.CTkButton(
            ctrl, text="▶ Start", width=110, height=38,
            fg_color=GREEN, hover_color="#00c864",
            text_color="#0a0a1a", corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._start_keylogger,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            ctrl, text="■ Stop", width=110, height=38,
            fg_color=RED, hover_color="#d50000",
            text_color="#ffffff", corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._stop_keylogger,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            ctrl, text="🗑 Clear", width=110, height=38,
            fg_color=BG_CARD, hover_color=BG_HOVER,
            text_color=TEXT_SECONDARY, corner_radius=8,
            border_width=1, border_color=BORDER,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._clear_keylog,
        ).pack(side="left")


    def _build_page_clipboard(self):
        page = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        self._pages["clipboard"] = page

        self._page_title(page, "📋  Clipboard Monitor",
                         "Captured clipboard changes in real-time")

        stat_bar = ctk.CTkFrame(page, fg_color=BG_CARD, corner_radius=10,
                                 height=44, border_width=1,
                                 border_color=BORDER)
        stat_bar.pack(fill="x", padx=24, pady=(0, 10))
        stat_bar.pack_propagate(False)

        sb_inner = ctk.CTkFrame(stat_bar, fg_color="transparent")
        sb_inner.pack(fill="both", expand=True, padx=16)

        self._w["cb_total"] = ctk.CTkLabel(
            sb_inner, text="Captures: 0",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=ACCENT2)
        self._w["cb_total"].pack(side="left", padx=(0, 28))

        self._w["cb_poll"] = ctk.CTkLabel(
            sb_inner, text=f"Poll: {CLIPBOARD_POLL_INTERVAL}s",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_SECONDARY)
        self._w["cb_poll"].pack(side="left")

        self._w["cb_status"] = ctk.CTkLabel(
            sb_inner, text="● Stopped",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=RED)
        self._w["cb_status"].pack(side="right")

        self._w["cb_feed"] = ctk.CTkScrollableFrame(
            page, fg_color=BG_PANEL, corner_radius=10,
            border_width=1, border_color=BORDER)
        self._w["cb_feed"].pack(fill="both", expand=True,
                                 padx=24, pady=(0, 18))

        self._w["cb_placeholder"] = ctk.CTkLabel(
            self._w["cb_feed"],
            text="No clipboard changes captured yet…\nStart monitoring to begin.",
            font=ctk.CTkFont(size=13), text_color=TEXT_DIM,
            justify="center")
        self._w["cb_placeholder"].pack(pady=40)


    def _build_page_screenshots(self):
        page = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        self._pages["screenshots"] = page

        self._page_title(page, "📸  Screenshots",
                         "Captured screen images")

        top = ctk.CTkFrame(page, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(0, 10))

        self._w["ss_total"] = ctk.CTkLabel(
            top, text="Total: 0",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=GREEN)
        self._w["ss_total"].pack(side="left", padx=(0, 20))

        self._w["ss_interval"] = ctk.CTkLabel(
            top, text=f"Interval: {SCREENSHOT_INTERVAL}s",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_SECONDARY)
        self._w["ss_interval"].pack(side="left", padx=(0, 20))

        self._w["ss_fmt"] = ctk.CTkLabel(
            top, text=f"Format: {SCREENSHOT_FORMAT.upper()}  "
                      f"Q:{SCREENSHOT_QUALITY}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_SECONDARY)
        self._w["ss_fmt"].pack(side="left")

        ctk.CTkButton(
            top, text="📷 Capture Now", width=150, height=36,
            fg_color=GREEN, hover_color="#00c864",
            text_color="#0a0a1a", corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._capture_screenshot_now,
        ).pack(side="right")

        self._w["ss_gallery"] = ctk.CTkScrollableFrame(
            page, fg_color=BG_PANEL, corner_radius=10,
            border_width=1, border_color=BORDER)
        self._w["ss_gallery"].pack(fill="both", expand=True,
                                    padx=24, pady=(0, 18))

        self._w["ss_placeholder"] = ctk.CTkLabel(
            self._w["ss_gallery"],
            text="No screenshots yet.\nStart monitoring or click "
                 "'Capture Now'.",
            font=ctk.CTkFont(size=13), text_color=TEXT_DIM,
            justify="center")
        self._w["ss_placeholder"].pack(pady=40)

        self._ss_images = []


    def _build_page_encryption(self):
        page = ctk.CTkScrollableFrame(self, fg_color=BG_DARK,
                                       corner_radius=0)
        self._pages["encryption"] = page

        self._page_title(page, "🔐  Logs & Encryption",
                         "Manage log files and encryption keys")

        enc_card = ctk.CTkFrame(page, fg_color=BG_CARD, corner_radius=12,
                                 border_width=1, border_color=BORDER)
        enc_card.pack(fill="x", padx=24, pady=(0, 14))

        ec_inner = ctk.CTkFrame(enc_card, fg_color="transparent")
        ec_inner.pack(fill="x", padx=18, pady=14)

        ctk.CTkLabel(ec_inner, text="🔑  Encryption Status",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=ACCENT).pack(anchor="w", pady=(0, 8))

        self._w["enc_labels"] = {}
        for ek, el in [
            ("enabled", "Encryption"),
            ("key_loaded", "Key Loaded"),
            ("created", "Key Created"),
            ("rotated", "Last Rotated"),
            ("rotations", "Rotation Count"),
        ]:
            rf = ctk.CTkFrame(ec_inner, fg_color="transparent")
            rf.pack(fill="x", pady=2)
            ctk.CTkLabel(rf, text=el,
                         font=ctk.CTkFont(size=12),
                         text_color=TEXT_SECONDARY).pack(side="left")
            lbl = ctk.CTkLabel(rf, text="—",
                               font=ctk.CTkFont(size=12, weight="bold"),
                               text_color=TEXT_PRIMARY)
            lbl.pack(side="right")
            self._w["enc_labels"][ek] = lbl

        self._refresh_encryption_status()

        ctk.CTkLabel(page, text="📂  Log Files",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=ACCENT).pack(anchor="w", padx=30,
                                              pady=(6, 8))

        hdr = ctk.CTkFrame(page, fg_color=BG_CARD, corner_radius=8,
                            height=36)
        hdr.pack(fill="x", padx=24, pady=(0, 2))
        hdr.pack_propagate(False)

        h_inner = ctk.CTkFrame(hdr, fg_color="transparent")
        h_inner.pack(fill="both", expand=True, padx=12)
        h_inner.columnconfigure(0, weight=3)
        h_inner.columnconfigure(1, weight=1)
        h_inner.columnconfigure(2, weight=2)
        h_inner.columnconfigure(3, weight=1)

        for ci, ct in enumerate(["Filename", "Size", "Modified",
                                  "Encrypted"]):
            ctk.CTkLabel(h_inner, text=ct,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=TEXT_SECONDARY).grid(
                row=0, column=ci, sticky="w", padx=4)

        self._w["enc_filelist"] = ctk.CTkScrollableFrame(
            page, fg_color=BG_PANEL, corner_radius=10,
            border_width=1, border_color=BORDER, height=200)
        self._w["enc_filelist"].pack(fill="x", padx=24, pady=(0, 12))

        self._refresh_log_files()

        exp_row = ctk.CTkFrame(page, fg_color="transparent")
        exp_row.pack(fill="x", padx=24, pady=(0, 6))

        ctk.CTkLabel(exp_row, text="Export logs as:",
                     font=ctk.CTkFont(size=13),
                     text_color=TEXT_SECONDARY).pack(side="left",
                                                      padx=(6, 14))

        for fmt, color in [("TXT", ACCENT), ("CSV", ACCENT2),
                            ("JSON", GREEN)]:
            ctk.CTkButton(
                exp_row, text=f"📥 {fmt}", width=100, height=34,
                fg_color=BG_CARD, hover_color=BG_HOVER,
                text_color=color, corner_radius=8,
                border_width=1, border_color=BORDER,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda f=fmt.lower(): self._export_logs(f),
            ).pack(side="left", padx=4)

        ctk.CTkButton(
            exp_row, text="🔄 Refresh", width=100, height=34,
            fg_color=BG_CARD, hover_color=BG_HOVER,
            text_color=TEXT_SECONDARY, corner_radius=8,
            border_width=1, border_color=BORDER,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._refresh_log_files,
        ).pack(side="right")

        self._w["enc_storage"] = ctk.CTkLabel(
            page, text="",
            font=ctk.CTkFont(size=11), text_color=TEXT_DIM)
        self._w["enc_storage"].pack(anchor="w", padx=30, pady=(4, 16))

        self._refresh_storage_stats()


    def _build_page_sysinfo(self):
        page = ctk.CTkScrollableFrame(self, fg_color=BG_DARK,
                                       corner_radius=0)
        self._pages["sysinfo"] = page

        self._page_title(page, "🖥️  System Information",
                         "Hardware and software profile")

        self._w["sysinfo_container"] = page
        self._refresh_sysinfo()


    def _build_page_settings(self):
        page = ctk.CTkScrollableFrame(self, fg_color=BG_DARK,
                                       corner_radius=0)
        self._pages["settings"] = page

        self._page_title(page, "⚙️  Settings",
                         "Configure monitoring parameters")

        self._settings_section(page, "⌨️ Keylogger")

        kl_grid = ctk.CTkFrame(page, fg_color="transparent")
        kl_grid.pack(fill="x", padx=30, pady=(0, 16))
        kl_grid.columnconfigure((0, 1), weight=1, uniform="s")

        self._setting_display(kl_grid, "Buffer Size",
                              str(BUFFER_SIZE), 0, 0)
        self._setting_display(kl_grid, "Flush Interval",
                              f"{FLUSH_INTERVAL_SECONDS}s", 0, 1)
        self._setting_display(kl_grid, "Special Keys",
                              "✅ On" if CAPTURE_SPECIAL_KEYS else "❌ Off",
                              1, 0)
        self._setting_display(kl_grid, "Timestamps",
                              "✅ On" if CAPTURE_TIMESTAMPS else "❌ Off",
                              1, 1)

        self._settings_section(page, "📋 Clipboard")

        cb_grid = ctk.CTkFrame(page, fg_color="transparent")
        cb_grid.pack(fill="x", padx=30, pady=(0, 16))
        cb_grid.columnconfigure((0, 1), weight=1, uniform="s")

        self._setting_display(cb_grid, "Enabled",
                              "✅ On" if CLIPBOARD_ENABLED else "❌ Off",
                              0, 0)
        self._setting_display(cb_grid, "Poll Interval",
                              f"{CLIPBOARD_POLL_INTERVAL}s", 0, 1)

        self._settings_section(page, "📸 Screenshots")

        ss_grid = ctk.CTkFrame(page, fg_color="transparent")
        ss_grid.pack(fill="x", padx=30, pady=(0, 16))
        ss_grid.columnconfigure((0, 1), weight=1, uniform="s")

        self._setting_display(ss_grid, "Enabled",
                              "✅ On" if SCREENSHOT_ENABLED else "❌ Off",
                              0, 0)
        self._setting_display(ss_grid, "Interval",
                              f"{SCREENSHOT_INTERVAL}s", 0, 1)
        self._setting_display(ss_grid, "Format",
                              SCREENSHOT_FORMAT.upper(), 1, 0)
        self._setting_display(ss_grid, "Quality",
                              str(SCREENSHOT_QUALITY), 1, 1)

        self._settings_section(page, "📧 Email Reporting")

        em_grid = ctk.CTkFrame(page, fg_color="transparent")
        em_grid.pack(fill="x", padx=30, pady=(0, 16))
        em_grid.columnconfigure((0, 1), weight=1, uniform="s")

        self._setting_display(em_grid, "Enabled",
                              "✅ On" if EMAIL_ENABLED else "❌ Off",
                              0, 0)

        self._settings_section(page, "⚖️ Ethical Safeguards")

        sg_grid = ctk.CTkFrame(page, fg_color="transparent")
        sg_grid.pack(fill="x", padx=30, pady=(0, 16))
        sg_grid.columnconfigure((0, 1), weight=1, uniform="s")

        self._setting_display(sg_grid, "Auto-Stop",
                              f"{AUTO_STOP_HOURS} hours", 0, 0)
        self._setting_display(sg_grid, "Consent Required",
                              "✅ Yes", 0, 1)

        self._settings_section(page, "📁 Directories")

        dir_grid = ctk.CTkFrame(page, fg_color="transparent")
        dir_grid.pack(fill="x", padx=30, pady=(0, 20))

        for d_label, d_path in [
            ("Log Directory", str(LOG_DIR)),
            ("Screenshot Dir", str(SCREENSHOT_DIR)),
            ("Export Directory", str(EXPORT_DIR)),
        ]:
            rf = ctk.CTkFrame(dir_grid, fg_color="transparent")
            rf.pack(fill="x", pady=3)
            ctk.CTkLabel(rf, text=d_label,
                         font=ctk.CTkFont(size=12),
                         text_color=TEXT_SECONDARY).pack(side="left")
            ctk.CTkLabel(rf, text=d_path,
                         font=ctk.CTkFont(family="Consolas", size=11),
                         text_color=TEXT_DIM).pack(side="right")


    def _page_title(self, parent, title: str, subtitle: str):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=24, pady=(20, 14))
        ctk.CTkLabel(
            f, text=title,
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            f, text=subtitle,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_DIM,
        ).pack(anchor="w", pady=(2, 0))

    @staticmethod
    def _settings_section(parent, title: str):
        ctk.CTkLabel(
            parent, text=title,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=ACCENT,
        ).pack(anchor="w", padx=30, pady=(10, 6))
        ctk.CTkFrame(parent, height=1, fg_color=BORDER).pack(
            fill="x", padx=30, pady=(0, 8))

    @staticmethod
    def _setting_display(parent, label: str, value: str,
                         row: int, col: int):
        card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10,
                            border_width=1, border_color=BORDER)
        card.grid(row=row, column=col, padx=6, pady=5, sticky="nsew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(inner, text=label,
                     font=ctk.CTkFont(size=11),
                     text_color=TEXT_SECONDARY).pack(anchor="w")
        ctk.CTkLabel(inner, text=value,
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=TEXT_PRIMARY).pack(anchor="w",
                                                    pady=(2, 0))


    def _tick(self):
        try:
            self._drain_key_queue()
            self._drain_clip_queue()

            if self._current_page == "dashboard":
                self._update_dashboard()
            elif self._current_page == "keylogger":
                self._update_keylogger_stats()
            elif self._current_page == "clipboard":
                self._update_clipboard_stats()
            elif self._current_page == "screenshots":
                self._update_screenshot_stats()
        except Exception:
            pass

        self.after(REFRESH_MS, self._tick)


    def _update_dashboard(self):
        if self.keylogger:
            st = self.keylogger.get_stats()
            self._w["card_keys"].set_value(f"{st['total_keystrokes']:,}")
            self._w["ses_labels"]["kpm"].configure(
                text=f"{st['keys_per_minute']}")
            elapsed = st["elapsed_seconds"]
            h, rem = divmod(int(elapsed), 3600)
            m, s = divmod(rem, 60)
            self._w["ses_labels"]["elapsed"].configure(
                text=f"{h:02d}:{m:02d}:{s:02d}")
            if self.keylogger.start_time:
                self._w["ses_labels"]["started"].configure(
                    text=self.keylogger.start_time.strftime("%H:%M:%S"))

        if self.clip_monitor:
            self._w["card_clip"].set_value(
                str(self.clip_monitor.total_captures))

        if self.screenshot_cap:
            self._w["card_shots"].set_value(
                str(self.screenshot_cap.total_captures))

        if self.window_tracker:
            title = self.window_tracker.current_window
            if title:
                short = (title[:30] + "…") if len(title) > 30 else title
                self._w["card_window"].set_value(short)

        mods = {
            "keylogger":  self.keylogger and self.keylogger.is_running,
            "clipboard":  self.clip_monitor and self.clip_monitor.is_running,
            "screenshot": self.screenshot_cap and self.screenshot_cap.is_running,
            "window":     self.window_tracker and self.window_tracker.is_running,
            "encryption": self.encryption and self.encryption.enabled,
        }
        for mk, running in mods.items():
            lbl = self._w["mod_labels"][mk]
            if running:
                lbl.configure(text="● ON", text_color=GREEN)
            else:
                lbl.configure(text="● OFF", text_color=RED)

        if PSUTIL_AVAILABLE:
            self._w["gauge_cpu"].set_value(psutil.cpu_percent(interval=0))
            self._w["gauge_ram"].set_value(
                psutil.virtual_memory().percent)

        if self._monitoring:
            self._w["sb_status"].configure(
                text="● Monitoring", text_color=GREEN)
        else:
            self._w["sb_status"].configure(
                text="● Idle", text_color=TEXT_DIM)


    def _update_keylogger_stats(self):
        if not self.keylogger:
            return
        st = self.keylogger.get_stats()
        self._w["kl_total"].configure(
            text=f"Keys: {st['total_keystrokes']:,}")
        self._w["kl_kpm"].configure(
            text=f"KPM: {st['keys_per_minute']}")
        self._w["kl_buffer"].configure(
            text=f"Buffer: {st['buffer_size']}")
        if st["running"]:
            self._w["kl_status"].configure(
                text="● Running", text_color=GREEN)
        else:
            self._w["kl_status"].configure(
                text="● Stopped", text_color=RED)


    def _update_clipboard_stats(self):
        if not self.clip_monitor:
            return
        st = self.clip_monitor.get_stats()
        self._w["cb_total"].configure(
            text=f"Captures: {st['total_captures']}")
        if st["running"]:
            self._w["cb_status"].configure(
                text="● Running", text_color=GREEN)
        else:
            self._w["cb_status"].configure(
                text="● Stopped", text_color=RED)


    def _update_screenshot_stats(self):
        if not self.screenshot_cap:
            return
        st = self.screenshot_cap.get_stats()
        self._w["ss_total"].configure(
            text=f"Total: {st['total_captures']}")


    def _on_key_event(self, record):
        self._key_queue.put(record)

    def _on_clip_event(self, entry):
        self._clip_queue.put(entry)

    def _drain_key_queue(self):
        count = 0
        while count < 200:
            try:
                rec = self._key_queue.get_nowait()
            except queue.Empty:
                break
            key = rec.get("key", "")
            tb = self._w["kl_textbox"]
            tb.configure(state="normal")
            tb.insert("end", key)
            tb.see("end")
            tb.configure(state="disabled")
            count += 1

    def _drain_clip_queue(self):
        while True:
            try:
                entry = self._clip_queue.get_nowait()
            except queue.Empty:
                break
            self._add_clip_entry_widget(entry)

    def _add_clip_entry_widget(self, entry: dict):
        ph = self._w.get("cb_placeholder")
        if ph and ph.winfo_exists():
            ph.destroy()
            self._w.pop("cb_placeholder", None)

        feed = self._w["cb_feed"]

        card = ctk.CTkFrame(feed, fg_color=BG_CARD, corner_radius=8,
                            border_width=1, border_color=BORDER)
        card.pack(fill="x", padx=8, pady=4)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)

        ts = entry.get("timestamp", "")
        time_str = ts.split("T")[1][:8] if "T" in ts else ts

        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x")

        ctk.CTkLabel(top_row, text=f"🕐 {time_str}",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=ACCENT2).pack(side="left")

        length = entry.get("length", 0)
        ctk.CTkLabel(top_row, text=f"{length} chars",
                     font=ctk.CTkFont(size=10),
                     text_color=TEXT_DIM).pack(side="right")

        content = entry.get("content", "")[:200]
        ctk.CTkLabel(inner, text=content,
                     font=ctk.CTkFont(family="Consolas", size=11),
                     text_color=TEXT_PRIMARY,
                     wraplength=600, justify="left").pack(
            anchor="w", pady=(4, 0))


    def _toggle_monitoring(self):
        if self._monitoring:
            self._stop_all()
        else:
            self._start_all()

    def _start_all(self):
        if self.consent_mgr and self.consent_mgr.required:
            from ui.consent_dialog import ConsentDialog
            dialog = ConsentDialog(self)
            self.wait_window(dialog)
            if not dialog.result:
                return
            self.consent_mgr._consent_granted = True
            self.consent_mgr._record_consent(granted=True)

        if self.keylogger and not self.keylogger.is_running:
            self.keylogger.start()
        if self.clip_monitor and not self.clip_monitor.is_running:
            self.clip_monitor.start()
        if self.screenshot_cap and not self.screenshot_cap.is_running:
            self.screenshot_cap.start()
        if self.window_tracker and not self.window_tracker.is_running:
            self.window_tracker.start()

        self._monitoring = True
        self._w["btn_toggle"].configure(
            text="■  STOP MONITORING",
            fg_color=RED, hover_color="#d50000",
            text_color="#ffffff",
        )

    def _stop_all(self):
        if self.keylogger and self.keylogger.is_running:
            self.keylogger.stop()
        if self.clip_monitor and self.clip_monitor.is_running:
            self.clip_monitor.stop()
        if self.screenshot_cap and self.screenshot_cap.is_running:
            self.screenshot_cap.stop()
        if self.window_tracker and self.window_tracker.is_running:
            self.window_tracker.stop()

        self._monitoring = False
        self._w["btn_toggle"].configure(
            text="▶  START MONITORING",
            fg_color=GREEN, hover_color="#00c864",
            text_color="#0a0a1a",
        )

    def _start_keylogger(self):
        if self.keylogger and not self.keylogger.is_running:
            self.keylogger.start()

    def _stop_keylogger(self):
        if self.keylogger and self.keylogger.is_running:
            self.keylogger.stop()

    def _clear_keylog(self):
        tb = self._w["kl_textbox"]
        tb.configure(state="normal")
        tb.delete("1.0", "end")
        tb.configure(state="disabled")

    def _capture_screenshot_now(self):
        if self.screenshot_cap:
            threading.Thread(
                target=self.screenshot_cap.capture_now,
                daemon=True,
            ).start()
            self.after(1500, self._refresh_screenshot_gallery)


    def _refresh_encryption_status(self):
        if not self.encryption:
            return
        st = self.encryption.get_status()
        lbls = self._w["enc_labels"]
        lbls["enabled"].configure(
            text="🔒 Active" if st["enabled"] else "🔓 Disabled",
            text_color=GREEN if st["enabled"] else RED)
        lbls["key_loaded"].configure(
            text="✅ Yes" if st["key_loaded"] else "❌ No",
            text_color=GREEN if st["key_loaded"] else RED)
        lbls["created"].configure(
            text=st.get("created_at", "—")[:19])
        lbls["rotated"].configure(
            text=st.get("rotated_at", "—")[:19])
        lbls["rotations"].configure(
            text=str(st.get("rotation_count", 0)))

    def _refresh_log_files(self):
        if not self.file_handler:
            return

        container = self._w["enc_filelist"]
        for child in container.winfo_children():
            child.destroy()

        files = self.file_handler.list_log_files()
        if not files:
            ctk.CTkLabel(container, text="No log files found.",
                         font=ctk.CTkFont(size=12),
                         text_color=TEXT_DIM).pack(pady=20)
            return

        for f in files:
            row = ctk.CTkFrame(container, fg_color="transparent",
                               height=32)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=4)
            inner.columnconfigure(0, weight=3)
            inner.columnconfigure(1, weight=1)
            inner.columnconfigure(2, weight=2)
            inner.columnconfigure(3, weight=1)

            ctk.CTkLabel(inner, text=f["filename"],
                         font=ctk.CTkFont(family="Consolas", size=11),
                         text_color=TEXT_PRIMARY).grid(
                row=0, column=0, sticky="w", padx=4)

            ctk.CTkLabel(inner, text=f"{f['size_kb']} KB",
                         font=ctk.CTkFont(size=11),
                         text_color=TEXT_SECONDARY).grid(
                row=0, column=1, sticky="w", padx=4)

            ctk.CTkLabel(inner, text=f["modified"],
                         font=ctk.CTkFont(size=11),
                         text_color=TEXT_SECONDARY).grid(
                row=0, column=2, sticky="w", padx=4)

            enc_text = "✅ Yes" if f["encrypted"] else "❌ No"
            enc_color = GREEN if f["encrypted"] else ORANGE
            ctk.CTkLabel(inner, text=enc_text,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=enc_color).grid(
                row=0, column=3, sticky="w", padx=4)

        self._refresh_storage_stats()

    def _refresh_storage_stats(self):
        if not self.file_handler:
            return
        stats = self.file_handler.get_storage_stats()
        self._w["enc_storage"].configure(
            text=f"📁 {stats['total_files']} files  ·  "
                 f"💾 {stats['total_size_mb']} MB  ·  "
                 f"📂 {stats['log_directory']}")

    def _export_logs(self, fmt: str):
        if not self.file_handler:
            return
        try:
            out = self.file_handler.export_logs(output_format=fmt)
            self._show_toast(f"✅ Exported to {out}")
        except Exception as e:
            self._show_toast(f"❌ Export failed: {e}")

    def _refresh_screenshot_gallery(self):
        if not self.screenshot_cap:
            return

        container = self._w["ss_gallery"]
        for child in container.winfo_children():
            child.destroy()
        self._ss_images.clear()

        captures = self.screenshot_cap.get_recent_captures()
        if not captures:
            ctk.CTkLabel(container,
                         text="No screenshots yet.",
                         font=ctk.CTkFont(size=13),
                         text_color=TEXT_DIM).pack(pady=40)
            return

        grid_frame = ctk.CTkFrame(container, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=8, pady=8)

        cols = 3
        for i, cap in enumerate(captures):
            r, c = divmod(i, cols)
            card = ctk.CTkFrame(grid_frame, fg_color=BG_CARD,
                                corner_radius=8, border_width=1,
                                border_color=BORDER)
            card.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")
            grid_frame.columnconfigure(c, weight=1)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=8, pady=8)

            filepath = SCREENSHOT_DIR / cap["filename"]
            if PIL_AVAILABLE and filepath.exists():
                try:
                    img = Image.open(filepath)
                    img.thumbnail((240, 150))
                    ctk_img = ctk.CTkImage(
                        light_image=img, dark_image=img,
                        size=img.size)
                    self._ss_images.append(ctk_img)
                    ctk.CTkLabel(inner, image=ctk_img,
                                 text="").pack()
                except Exception:
                    ctk.CTkLabel(inner, text="🖼️ Preview unavailable",
                                 text_color=TEXT_DIM).pack(pady=10)
            else:
                ctk.CTkLabel(inner, text="🖼️",
                             font=ctk.CTkFont(size=40),
                             text_color=TEXT_DIM).pack(pady=10)

            ctk.CTkLabel(inner, text=cap["filename"][:30],
                         font=ctk.CTkFont(family="Consolas", size=9),
                         text_color=TEXT_SECONDARY).pack()
            ctk.CTkLabel(inner, text=f"{cap['size_kb']} KB",
                         font=ctk.CTkFont(size=9),
                         text_color=TEXT_DIM).pack()

        self._w["ss_total"].configure(
            text=f"Total: {self.screenshot_cap.total_captures}")

    def _refresh_sysinfo(self):
        container = self._w["sysinfo_container"]

        children = container.winfo_children()
        for child in children[1:]:
            child.destroy()

        if not self.sys_profiler:
            ctk.CTkLabel(container, text="System profiler not available.",
                         text_color=TEXT_DIM).pack(pady=30)
            return

        profile = self.sys_profiler.collect_all()
        os_info = profile.get("os_info", {})
        hw = profile.get("hardware", {})
        net = profile.get("network", {})
        user = profile.get("user_info", {})
        procs = profile.get("processes", [])

        self._sysinfo_card(container, "🏗️ Operating System", [
            ("System", f"{os_info.get('system', '?')} "
                       f"{os_info.get('release', '')}"),
            ("Architecture", f"{os_info.get('architecture', '?')} "
                             f"({os_info.get('machine', '')})"),
            ("Processor", os_info.get("processor", "?")[:60]),
            ("Python", os_info.get("python_version", "?")),
        ])

        self._sysinfo_card(container, "🧠 Hardware", [
            ("CPU Cores",
             f"{hw.get('cpu_count_physical', '?')} physical / "
             f"{hw.get('cpu_count_logical', '?')} logical"),
            ("RAM",
             f"{hw.get('ram_total_gb', '?')} GB "
             f"({hw.get('ram_usage_percent', '?')}% used)"),
            ("Disk",
             f"{hw.get('disk_total_gb', '?')} GB "
             f"({hw.get('disk_usage_percent', '?')}% used)"),
        ])

        self._sysinfo_card(container, "🌐 Network", [
            ("Hostname", net.get("hostname", "?")),
            ("Local IP", net.get("local_ip", "?")),
            ("Net Sent", f"{net.get('bytes_sent_mb', '?')} MB"),
            ("Net Recv", f"{net.get('bytes_recv_mb', '?')} MB"),
        ])

        self._sysinfo_card(container, "👤 User", [
            ("Username", user.get("username", "?")),
            ("Home", user.get("home_directory", "?")),
        ])

        if procs and not (len(procs) == 1 and "error" in procs[0]):
            ctk.CTkLabel(container, text="📊  Top Processes (by Memory)",
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=ACCENT).pack(
                anchor="w", padx=30, pady=(14, 6))

            phdr = ctk.CTkFrame(container, fg_color=BG_CARD,
                                corner_radius=8, height=30)
            phdr.pack(fill="x", padx=24, pady=(0, 2))
            phdr.pack_propagate(False)

            phi = ctk.CTkFrame(phdr, fg_color="transparent")
            phi.pack(fill="both", expand=True, padx=12)
            phi.columnconfigure(0, weight=0, minsize=60)
            phi.columnconfigure(1, weight=2)
            phi.columnconfigure(2, weight=1)
            phi.columnconfigure(3, weight=1)
            phi.columnconfigure(4, weight=1)

            for ci, ct in enumerate(["PID", "Name", "CPU%",
                                      "Mem%", "Status"]):
                ctk.CTkLabel(phi, text=ct,
                             font=ctk.CTkFont(size=10, weight="bold"),
                             text_color=TEXT_SECONDARY).grid(
                    row=0, column=ci, sticky="w", padx=4)

            proc_frame = ctk.CTkFrame(container, fg_color=BG_PANEL,
                                      corner_radius=10, border_width=1,
                                      border_color=BORDER)
            proc_frame.pack(fill="x", padx=24, pady=(0, 18))

            for p in procs[:15]:
                prow = ctk.CTkFrame(proc_frame, fg_color="transparent",
                                    height=26)
                prow.pack(fill="x", pady=0)
                prow.pack_propagate(False)

                pri = ctk.CTkFrame(prow, fg_color="transparent")
                pri.pack(fill="both", expand=True, padx=12)
                pri.columnconfigure(0, weight=0, minsize=60)
                pri.columnconfigure(1, weight=2)
                pri.columnconfigure(2, weight=1)
                pri.columnconfigure(3, weight=1)
                pri.columnconfigure(4, weight=1)

                vals = [
                    str(p.get("pid", "")),
                    (p.get("name", "")[:28]),
                    str(p.get("cpu_percent", "")),
                    str(p.get("memory_percent", "")),
                    p.get("status", ""),
                ]
                for vi, vt in enumerate(vals):
                    ctk.CTkLabel(pri, text=vt,
                                 font=ctk.CTkFont(
                                     family="Consolas", size=10),
                                 text_color=TEXT_PRIMARY).grid(
                        row=0, column=vi, sticky="w", padx=4)

        ctk.CTkButton(
            container, text="🔄 Refresh System Info",
            width=200, height=36,
            fg_color=BG_CARD, hover_color=BG_HOVER,
            text_color=ACCENT, corner_radius=8,
            border_width=1, border_color=BORDER,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._refresh_sysinfo,
        ).pack(pady=(8, 20))

    def _sysinfo_card(self, parent, title: str,
                      rows: list):
        card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12,
                            border_width=1, border_color=BORDER)
        card.pack(fill="x", padx=24, pady=5)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=12)

        ctk.CTkLabel(inner, text=title,
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=ACCENT).pack(anchor="w", pady=(0, 6))

        for label, value in rows:
            rf = ctk.CTkFrame(inner, fg_color="transparent")
            rf.pack(fill="x", pady=2)
            ctk.CTkLabel(rf, text=label,
                         font=ctk.CTkFont(size=12),
                         text_color=TEXT_SECONDARY).pack(side="left")
            ctk.CTkLabel(rf, text=str(value),
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=TEXT_PRIMARY).pack(side="right")


    def _show_toast(self, message: str, duration_ms: int = 3000):
        toast = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=10,
                             border_width=1, border_color=ACCENT)
        toast.place(relx=0.5, rely=0.95, anchor="center")

        ctk.CTkLabel(
            toast, text=f"  {message}  ",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=ACCENT,
        ).pack(padx=16, pady=8)

        self.after(duration_ms, toast.destroy)


    def _on_closing(self):
        self._stop_all()
        self.destroy()
