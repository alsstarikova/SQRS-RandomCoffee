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

    def _check_credentials(self) -> None:
        if (
            not self.settings.smtp_user
            or not self.settings.smtp_password
            or not self.settings.smtp_from
        ):
            raise EmailSendError("SMTP credentials are not configured")

    def _send_message(self, message: EmailMessage, error_text: str) -> None:
        try:
            if self.settings.smtp_use_ssl:
                with smtplib.SMTP_SSL(
                    self.settings.smtp_host,
                    self.settings.smtp_port,
                ) as server:
                    server.login(
                        self.settings.smtp_user,
                        self.settings.smtp_password,
                    )
                    server.send_message(message)
            else:
                with smtplib.SMTP(
                    self.settings.smtp_host,
                    self.settings.smtp_port,
                ) as server:
                    if self.settings.smtp_use_tls:
                        server.starttls()
                    server.login(
                        self.settings.smtp_user,
                        self.settings.smtp_password,
                    )
                    server.send_message(message)
        except smtplib.SMTPException as exc:
            raise EmailSendError(error_text) from exc

    def send_otp(self, to_email: str, otp: str) -> None:
        self._check_credentials()

        message = EmailMessage()
        message["From"] = self.settings.smtp_from
        message["To"] = to_email
        message["Subject"] = "Your OTP code for Random Coffee"
        message.set_content(
            f"Hello! Your OTP code for Random Coffee: {otp}",
        )

        self._send_message(message, "Failed to send OTP email")

    def send_match_notification(
        self,
        to_email: str,
        partners: Partners,
    ) -> None:
        self._check_credentials()

        if len(partners) == 1:
            subject = "Your Random Coffee this week!"
            intro = "This week your conversation partner is:"
        else:
            subject = "Your Random Coffee this week — a group meeting!"
            intro = "This week you have a group meeting! Your conversation partners are:"

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

        self._send_message(message, "Failed to send match notification")
