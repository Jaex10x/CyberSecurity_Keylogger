import json
import hashlib
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Confirm

from config.settings import (
    REQUIRE_CONSENT,
    CONSENT_LOG_FILE,
    APP_NAME,
    THEME_WARNING,
    THEME_ACCENT,
)

console = Console()

CONSENT_TERMS = 

class ConsentManager:

    def __init__(self):
        self.consent_file = CONSENT_LOG_FILE
        self.required = REQUIRE_CONSENT
        self._consent_granted = False

    def request_consent(self) -> bool:
        if not self.required:
            self._consent_granted = True
            return True

        console.print()
        console.print(
            Panel(
                Text(CONSENT_TERMS, style="bold white"),
                title=f"⚖️  {APP_NAME} - Ethical Use Agreement",
                border_style=THEME_WARNING,
                padding=(1, 2),
            )
        )
        console.print()

        try:
            consent = Confirm.ask(
                f"[bold {THEME_WARNING}]🔐 Do you accept these terms and confirm you have authorization?[/]",
                default=False,
            )
        except (KeyboardInterrupt, EOFError):
            consent = False

        if consent:
            self._consent_granted = True
            self._record_consent(granted=True)
            console.print(
                f"\n[bold {THEME_ACCENT}]✅ Consent granted. Session authorized.[/]\n"
            )
        else:
            self._consent_granted = False
            self._record_consent(granted=False)
            console.print(
                f"\n[bold {THEME_WARNING}]❌ Consent denied. Monitoring will not start.[/]\n"
            )

        return self._consent_granted

    def verify_consent(self) -> bool:
        return self._consent_granted

    def revoke_consent(self):
        self._consent_granted = False
        self._record_consent(granted=False, action="REVOKED")
        console.print(
            f"[bold {THEME_WARNING}]⚠️  Consent revoked. Monitoring stopped.[/]"
        )

    def _record_consent(self, granted: bool, action: str = None):
        record = {
            "timestamp": datetime.now().isoformat(),
            "action": action or ("GRANTED" if granted else "DENIED"),
            "machine_id": self._get_machine_hash(),
        }

        records = []
        if self.consent_file.exists():
            try:
                with open(self.consent_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except (json.JSONDecodeError, Exception):
                records = []

        records.append(record)

        self.consent_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.consent_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

    @staticmethod
    def _get_machine_hash() -> str:
        import platform
        import socket
        raw = f"{platform.node()}-{socket.gethostname()}-{platform.machine()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get_consent_history(self) -> list:
        if not self.consent_file.exists():
            return []

        try:
            with open(self.consent_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            return []
