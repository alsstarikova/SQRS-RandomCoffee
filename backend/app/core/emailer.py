import smtplib
from email.message import EmailMessage

from .settings import Settings


class EmailSendError(Exception):
    pass


class Mailer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send_otp(self, to_email: str, otp: str) -> None:
        if (
            not self.settings.smtp_user
            or not self.settings.smtp_password
            or not self.settings.smtp_from
        ):
            raise EmailSendError("SMTP credentials are not configured")

        message = EmailMessage()
        message["From"] = self.settings.smtp_from
        message["To"] = to_email
        message["Subject"] = "Your OTP code for Random Coffee"
        message.set_content(
            f"Hello! Your OTP code for Random Coffee: {otp}",
        )

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
            raise EmailSendError("Failed to send OTP email") from exc
