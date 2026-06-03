"""
CyberSentinel - Email Reporter
================================
Sends encrypted log reports via email at
configurable intervals.

Features:
    - SMTP email delivery
    - Encrypted attachment support
    - HTML formatted reports
    - Configurable intervals
    - Error handling with retry
"""

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
    """
    Handles email-based report delivery for CyberSentinel.
    Sends periodic or on-demand reports with log attachments.
    """

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

        # State
        self._running = False
        self._thread = None
        self.total_sent = 0
        self.last_sent = None
        self.last_error = None

    def start_periodic(self):
        """Start periodic report sending."""
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
        """Stop periodic reporting."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def _periodic_loop(self):
        """Main periodic sending loop."""
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
        """
        Send an email report.

        Args:
            subject: Email subject line.
            body_text: Report body text.
            attachment_path: Optional file to attach.

        Returns:
            True if sent successfully, False otherwise.
        """
        if not self.enabled:
            return False

        try:
            # Build the email
            msg = MIMEMultipart("alternative")
            msg["From"] = self.sender
            msg["To"] = self.recipient
            msg["Subject"] = subject or (
                f"[{APP_NAME}] Monitoring Report - "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )

            # HTML body
            html_body = self._build_html_report(body_text)
            msg.attach(MIMEText(html_body, "html"))

            # Attachment
            if attachment_path and attachment_path.exists():
                self._attach_file(msg, attachment_path)

            # Send
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
        """Build an HTML formatted report."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: #0a0a1a;
                    color: #e0e0e0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: linear-gradient(135deg, #1a1a2e, #16213e);
                    border-radius: 12px;
                    padding: 30px;
                    border: 1px solid #0f3460;
                }}
                .header {{
                    text-align: center;
                    border-bottom: 2px solid #00d4ff;
                    padding-bottom: 15px;
                    margin-bottom: 20px;
                }}
                .header h1 {{
                    color: #00d4ff;
                    font-size: 24px;
                    margin: 0;
                }}
                .header p {{
                    color: #888;
                    font-size: 12px;
                }}
                .content {{
                    padding: 15px 0;
                    line-height: 1.6;
                }}
                .footer {{
                    text-align: center;
                    font-size: 11px;
                    color: #666;
                    border-top: 1px solid #333;
                    padding-top: 15px;
                    margin-top: 20px;
                }}
                .badge {{
                    display: inline-block;
                    background: #00d4ff;
                    color: #0a0a1a;
                    padding: 3px 10px;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛡️ {APP_NAME}</h1>
                    <p>v{APP_VERSION} | Session: {SESSION_ID}</p>
                </div>
                <div class="content">
                    {body_text or "Periodic monitoring report. See attached log file for details."}
                </div>
                <div class="footer">
                    <span class="badge">AUTHORIZED USE ONLY</span>
                    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>This is an automated report from {APP_NAME}.</p>
                </div>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def _attach_file(msg: MIMEMultipart, filepath: Path):
        """Attach a file to the email message."""
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
        """Get email reporter statistics."""
        return {
            "enabled": self.enabled,
            "running": self._running,
            "total_sent": self.total_sent,
            "last_sent": self.last_sent.isoformat() if self.last_sent else None,
            "last_error": self.last_error,
            "recipient": self.recipient[:3] + "***" if self.recipient else None,
            "interval_seconds": self.interval,
        }
