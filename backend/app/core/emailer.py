import smtplib
from email.message import EmailMessage
from typing import Optional

from .settings import Settings


class PartnerData:
    def __init__(
        self,
        email: str,
        name: Optional[str],
        about: Optional[str],
        telegram: Optional[str],
        interests: list[str],
        common_interests: list[str],
    ) -> None:
        self.email = email
        self.name = name
        self.about = about
        self.telegram = telegram
        self.interests = interests
        self.common_interests = common_interests


Partners = list[PartnerData]


class EmailSendError(Exception):
    pass


def _format_partner(p: "PartnerData") -> str:
    lines = [f"  • {p.name or p.email} — {p.email}"]
    if p.telegram:
        lines.append(f"    Telegram: {p.telegram}")
    if p.about:
        lines.append(f"    About: {p.about}")
    if p.interests:
        lines.append(f"    Interests: {', '.join(p.interests)}")
    if p.common_interests:
        lines.append(f"    Common interests: {', '.join(p.common_interests)}")
    return "\n".join(lines)


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

        partner_lines = "\n\n".join(
            _format_partner(p) for p in partners
        )

        message = EmailMessage()
        message["From"] = self.settings.smtp_from
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(
            f"Hello!\n\n{intro}\n{partner_lines}\n\nHave a great conversation!",
        )

        self._send_message(message, "Failed to send match notification")
