"""
CyberSentinel - GUI Consent Dialog
=====================================
Modal dialog that displays the ethical use agreement
and collects user consent before monitoring begins.

Uses CustomTkinter for a modern dark-themed appearance
that matches the main GUI dashboard.
"""

import customtkinter as ctk


# ═══════════════════════════════════════════════
#  CONSENT TERMS TEXT
# ═══════════════════════════════════════════════
CONSENT_TERMS = """
TERMS OF AUTHORIZED USE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

By proceeding, you acknowledge and agree to the following:

1. AUTHORIZATION
   You confirm that you have explicit written authorization
   from the system owner to run this monitoring software
   on this device.

2. LEGAL COMPLIANCE
   You will use this tool in compliance with all applicable
   local, state, national, and international laws and
   regulations.

3. EDUCATIONAL PURPOSE
   This software is intended for cybersecurity education,
   authorized penetration testing, and security research only.

4. DATA RESPONSIBILITY
   You accept full responsibility for any data collected and
   will handle it in accordance with data protection
   regulations (e.g., GDPR, CCPA).

5. NO MALICIOUS USE
   You will NOT use this tool for unauthorized surveillance,
   identity theft, corporate espionage, or any other
   malicious purpose.

6. ACCOUNTABILITY
   You understand that all monitoring sessions are logged
   and can be audited.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  VIOLATION OF THESE TERMS MAY RESULT IN
    CRIMINAL PROSECUTION.
"""

# Colors (matches gui_dashboard palette)
_BG_DARK = "#0a0a1a"
_BG_PANEL = "#1a1a2e"
_ACCENT = "#00d4ff"
_RED = "#ff1744"
_GREEN = "#00e676"
_TEXT_PRIMARY = "#e0e0e0"
_TEXT_DIM = "#616161"
_BORDER = "#0f3460"


class ConsentDialog(ctk.CTkToplevel):
    """
    Modal dialog displaying ethical use terms.

    Usage:
        dialog = ConsentDialog(parent_window)
        parent_window.wait_window(dialog)
        if dialog.result:
            # Consent was granted
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.result = False

        # ── Window config ──
        self.title("CyberSentinel — Ethical Use Agreement")
        self.geometry("680x580")
        self.resizable(False, False)
        self.configure(fg_color=_BG_DARK)

        # Make it modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 680) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 580) // 2
        self.geometry(f"680x580+{x}+{y}")

        self._build_ui()

        # Handle close via X button as decline
        self.protocol("WM_DELETE_WINDOW", self._decline)

    def _build_ui(self):
        """Build the dialog layout."""

        # ── Header ──
        header_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header_frame.pack(fill="x", padx=30, pady=(25, 5))
        header_frame.pack_propagate(False)

        ctk.CTkLabel(
            header_frame,
            text="⚖️  Ethical Use Agreement",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=_ACCENT,
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_frame,
            text="You must accept the terms below before monitoring can begin.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=_TEXT_DIM,
        ).pack(anchor="w", pady=(4, 0))

        # ── Separator ──
        ctk.CTkFrame(self, height=1, fg_color=_BORDER).pack(
            fill="x", padx=30, pady=8
        )

        # ── Terms textbox ──
        terms_box = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=_BG_PANEL,
            text_color=_TEXT_PRIMARY,
            border_color=_BORDER,
            border_width=1,
            corner_radius=10,
            wrap="word",
        )
        terms_box.pack(fill="both", expand=True, padx=30, pady=5)
        terms_box.insert("1.0", CONSENT_TERMS)
        terms_box.configure(state="disabled")

        # ── Warning label ──
        ctk.CTkLabel(
            self,
            text="⚠️  Unauthorized use of monitoring tools is illegal and unethical.",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#ff9100",
        ).pack(pady=(8, 5))

        # ── Buttons ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent", height=50)
        btn_frame.pack(fill="x", padx=30, pady=(0, 25))

        ctk.CTkButton(
            btn_frame,
            text="❌  Decline",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=_BG_PANEL,
            hover_color="#2a1525",
            text_color=_RED,
            border_color=_RED,
            border_width=1,
            width=180,
            height=42,
            corner_radius=10,
            command=self._decline,
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame,
            text="✅  Accept & Continue",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=_GREEN,
            hover_color="#00c864",
            text_color="#0a0a1a",
            width=220,
            height=42,
            corner_radius=10,
            command=self._accept,
        ).pack(side="right")

    def _accept(self):
        """User accepted the terms."""
        self.result = True
        self.grab_release()
        self.destroy()

    def _decline(self):
        """User declined the terms."""
        self.result = False
        self.grab_release()
        self.destroy()
