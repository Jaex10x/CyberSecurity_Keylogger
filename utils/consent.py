"""
CyberSentinel - Ethical Consent Manager
=========================================
Ensures proper authorization and consent before
any monitoring activity begins.

Features:
    - Interactive consent prompt with terms display
    - Consent record logging with timestamps
    - Verification of prior consent
    - Consent revocation support
"""

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


CONSENT_TERMS = """
╔══════════════════════════════════════════════════════════════════╗
║                    TERMS OF AUTHORIZED USE                      ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  By proceeding, you acknowledge and agree to the following:      ║
║                                                                  ║
║  1. AUTHORIZATION: You confirm that you have explicit written    ║
║     authorization from the system owner to run this monitoring   ║
║     software on this device.                                     ║
║                                                                  ║
║  2. LEGAL COMPLIANCE: You will use this tool in compliance       ║
║     with all applicable local, state, national, and              ║
║     international laws and regulations.                          ║
║                                                                  ║
║  3. EDUCATIONAL PURPOSE: This software is intended for           ║
║     cybersecurity education, authorized penetration testing,     ║
║     and security research only.                                  ║
║                                                                  ║
║  4. DATA RESPONSIBILITY: You accept full responsibility for      ║
║     any data collected and will handle it in accordance with     ║
║     data protection regulations (e.g., GDPR, CCPA).             ║
║                                                                  ║
║  5. NO MALICIOUS USE: You will NOT use this tool for             ║
║     unauthorized surveillance, identity theft, corporate         ║
║     espionage, or any other malicious purpose.                   ║
║                                                                  ║
║  6. ACCOUNTABILITY: You understand that all monitoring           ║
║     sessions are logged and can be audited.                      ║
║                                                                  ║
║  VIOLATION OF THESE TERMS MAY RESULT IN CRIMINAL PROSECUTION.    ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""


class ConsentManager:
    """
    Manages ethical consent verification for monitoring sessions.
    Records all consent decisions for audit trail purposes.
    """

    def __init__(self):
        self.consent_file = CONSENT_LOG_FILE
        self.required = REQUIRE_CONSENT
        self._consent_granted = False

    def request_consent(self) -> bool:
        """
        Display consent terms and request user acknowledgment.

        Returns:
            True if consent is granted, False otherwise.
        """
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

        # Prompt for consent
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
        """Check if consent has been granted for the current session."""
        return self._consent_granted

    def revoke_consent(self):
        """Revoke previously granted consent."""
        self._consent_granted = False
        self._record_consent(granted=False, action="REVOKED")
        console.print(
            f"[bold {THEME_WARNING}]⚠️  Consent revoked. Monitoring stopped.[/]"
        )

    def _record_consent(self, granted: bool, action: str = None):
        """
        Record consent decision to audit log.

        Args:
            granted: Whether consent was granted.
            action: Optional action label (e.g., 'REVOKED').
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "action": action or ("GRANTED" if granted else "DENIED"),
            "machine_id": self._get_machine_hash(),
        }

        # Load existing records
        records = []
        if self.consent_file.exists():
            try:
                with open(self.consent_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except (json.JSONDecodeError, Exception):
                records = []

        records.append(record)

        # Save updated records
        self.consent_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.consent_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

    @staticmethod
    def _get_machine_hash() -> str:
        """Generate a non-identifying hash of the machine for audit purposes."""
        import platform
        import socket
        raw = f"{platform.node()}-{socket.gethostname()}-{platform.machine()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get_consent_history(self) -> list:
        """Retrieve the consent audit trail."""
        if not self.consent_file.exists():
            return []

        try:
            with open(self.consent_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            return []
