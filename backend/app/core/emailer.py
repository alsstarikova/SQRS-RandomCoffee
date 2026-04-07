import smtplib
from email.message import EmailMessage
from typing import Optional

from .settings import Settings

Partners = list[tuple[str, Optional[str]]]


class EmailSendError(Exception):
    pass


class Mailer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _send(self, message: EmailMessage) -> None:
        """Send a prepared EmailMessage using configured SMTP settings.

        Login is performed only when SSL or STARTTLS is enabled.
        Plain SMTP (e.g. local Mailpit) works without authentication.
        """
        s = self.settings
        needs_auth = s.smtp_use_ssl or s.smtp_use_tls

        try:
            if s.smtp_use_ssl:
                with smtplib.SMTP_SSL(s.smtp_host, s.smtp_port) as server:
                    if needs_auth:
                        server.login(s.smtp_user, s.smtp_password)
                    server.send_message(message)
            else:
                with smtplib.SMTP(s.smtp_host, s.smtp_port) as server:
                    if s.smtp_use_tls:
                        server.starttls()
                    if needs_auth:
                        server.login(s.smtp_user, s.smtp_password)
                    server.send_message(message)
        except smtplib.SMTPException as exc:
            raise EmailSendError("Failed to send email") from exc

    def send_otp(self, to_email: str, otp: str) -> None:
        if not self.settings.smtp_from:
            raise EmailSendError("SMTP credentials are not configured")

        message = EmailMessage()
        message["From"] = self.settings.smtp_from
        message["To"] = to_email
        message["Subject"] = "Your OTP code for Random Coffee"
        message.set_content(f"Hello! Your OTP code for Random Coffee: {otp}")
        self._send(message)

    def send_match_notification(
        self,
        to_email: str,
        partners: "Partners",
    ) -> None:
        if not self.settings.smtp_from:
            raise EmailSendError("SMTP credentials are not configured")

        if len(partners) == 1:
            subject = "Your Random Coffee this week!"
            intro = "This week your conversation partner is:"
        else:
            subject = "Your Random Coffee this week — a group meeting!"
            intro = (
                "This week you have a group meeting! Your conversation partners are:"
            )

        partner_lines = "\n".join(
            f"  • {name or email} — {email}" for email, name in partners
        )

        message = EmailMessage()
        message["From"] = self.settings.smtp_from
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(
            f"Hello!\n\n{intro}\n{partner_lines}\n\nHave a great conversation!",
        )
        self._send(message)
