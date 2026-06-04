import smtplib
import threading
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

from config.settings import (
    EMAIL_ENABLED,
    EMAIL_SMTP_SERVER,
    EMAIL_SMTP_PORT,
    EMAIL_SENDER,
    EMAIL_PASSWORD,
    EMAIL_RECIPIENT,
    EMAIL_REPORT_INTERVAL,
    APP_NAME,
    APP_VERSION,
    SESSION_ID,
)

class EmailReporter:

    def __init__(self):
        self.enabled = EMAIL_ENABLED and all([
            EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT
        ])
        self.smtp_server = EMAIL_SMTP_SERVER
        self.smtp_port = EMAIL_SMTP_PORT
        self.sender = EMAIL_SENDER
        self.password = EMAIL_PASSWORD
        self.recipient = EMAIL_RECIPIENT
        self.interval = EMAIL_REPORT_INTERVAL

        self._running = False
        self._thread = None
        self.total_sent = 0
        self.last_sent = None
        self.last_error = None

    def start_periodic(self):
        if not self.enabled:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._periodic_loop,
            name="EmailReporter",
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def _periodic_loop(self):
        while self._running:
            time.sleep(self.interval)
            if self._running:
                self.send_report()

    def send_report(
        self,
        subject: str = None,
        body_text: str = None,
        attachment_path: Path = None,
    ) -> bool:
        if not self.enabled:
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.sender
            msg["To"] = self.recipient
            msg["Subject"] = subject or (
                f"[{APP_NAME}] Monitoring Report - "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )

            html_body = self._build_html_report(body_text)
            msg.attach(MIMEText(html_body, "html"))

            if attachment_path and attachment_path.exists():
                self._attach_file(msg, attachment_path)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.sender, self.password)
                server.send_message(msg)

            self.total_sent += 1
            self.last_sent = datetime.now()
            self.last_error = None
            return True

        except Exception as e:
            self.last_error = str(e)
            return False

    def _build_html_report(self, body_text: str = None) -> str:
        return f

    @staticmethod
    def _attach_file(msg: MIMEMultipart, filepath: Path):
        with open(filepath, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={filepath.name}",
        )
        msg.attach(part)

    def get_stats(self) -> dict:
        return {
            "enabled": self.enabled,
            "running": self._running,
            "total_sent": self.total_sent,
            "last_sent": self.last_sent.isoformat() if self.last_sent else None,
            "last_error": self.last_error,
            "recipient": self.recipient[:3] + "***" if self.recipient else None,
            "interval_seconds": self.interval,
        }
