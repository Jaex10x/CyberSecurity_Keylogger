import customtkinter as ctk

CONSENT_TERMS = 

_BG_DARK = "
_BG_PANEL = "
_ACCENT = "
_RED = "
_GREEN = "
_TEXT_PRIMARY = "
_TEXT_DIM = "
_BORDER = "

class ConsentDialog(ctk.CTkToplevel):

    def __init__(self, parent):
        super().__init__(parent)

        self.result = False

        self.title("CyberSentinel — Ethical Use Agreement")
        self.geometry("680x580")
        self.resizable(False, False)
        self.configure(fg_color=_BG_DARK)

        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 680) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 580) // 2
        self.geometry(f"680x580+{x}+{y}")

        self._build_ui()

        self.protocol("WM_DELETE_WINDOW", self._decline)

    def _build_ui(self):

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

        ctk.CTkFrame(self, height=1, fg_color=_BORDER).pack(
            fill="x", padx=30, pady=8
        )

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

        ctk.CTkLabel(
            self,
            text="⚠️  Unauthorized use of monitoring tools is illegal and unethical.",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="
        ).pack(pady=(8, 5))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent", height=50)
        btn_frame.pack(fill="x", padx=30, pady=(0, 25))

        ctk.CTkButton(
            btn_frame,
            text="❌  Decline",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=_BG_PANEL,
            hover_color="
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
            hover_color="
            text_color="
            width=220,
            height=42,
            corner_radius=10,
            command=self._accept,
        ).pack(side="right")

    def _accept(self):
        self.result = True
        self.grab_release()
        self.destroy()

    def _decline(self):
        self.result = False
        self.grab_release()
        self.destroy()
