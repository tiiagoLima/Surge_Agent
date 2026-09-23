"""Email notifier — NotificationPort via SMTP."""

from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText

from surge.domain.models import Opportunity
from surge.domain.ports import NotificationPort

logger = logging.getLogger(__name__)


class EmailNotifier(NotificationPort):
    """Sends email notifications."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        email_from: str,
        email_to: str,
        enabled: bool = True,
    ) -> None:
        self._host = smtp_host
        self._port = smtp_port
        self._user = smtp_user
        self._password = smtp_password
        self._from = email_from
        self._to = email_to
        self._enabled = enabled

    def notify(self, opportunities: list[Opportunity]) -> None:
        if not self._enabled or not opportunities:
            return
        if not self._to or not self._from:
            logger.warning("Email not configured — skipping")
            return

        subject = f"Surge: {len(opportunities)} oportunidade(s) detectada(s)"
        body_lines = ["Surge detectou quedas relevantes:\n"]
        for opp in opportunities:
            body_lines.append(f"- {opp.summary()}")
        body = "\n".join(body_lines)

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = self._from
        msg["To"] = self._to

        try:
            with smtplib.SMTP(self._host, self._port, timeout=15) as server:
                server.ehlo()
                if self._port == 587:
                    server.starttls()
                    server.ehlo()
                if self._user and self._password:
                    server.login(self._user, self._password)
                server.send_message(msg)
            logger.info("Email sent to %s (%d opportunities)", self._to, len(opportunities))
        except Exception:
            logger.exception("Failed to send email")
            raise

    def notify_error(self, message: str) -> None:
        if not self._enabled or not self._to:
            return
        msg = MIMEText(message, "plain", "utf-8")
        msg["Subject"] = "Surge: erro no scanner"
        msg["From"] = self._from
        msg["To"] = self._to
        try:
            with smtplib.SMTP(self._host, self._port, timeout=15) as server:
                server.ehlo()
                if self._port == 587:
                    server.starttls()
                    server.ehlo()
                if self._user and self._password:
                    server.login(self._user, self._password)
                server.send_message(msg)
        except Exception:
            logger.exception("Failed to send error email")
