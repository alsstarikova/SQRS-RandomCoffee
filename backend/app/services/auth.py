from datetime import datetime

from sqlalchemy.orm import Session

from app.core import EmailSendError, Mailer
from app.core.auth import create_access_token
from app.core.security import (
    generate_otp,
    new_otp_hash,
    otp_expiration,
    utcnow,
    verify_otp,
)
from app.db import User


class AuthServiceError(Exception):
    pass


class RegistrationClosedError(AuthServiceError):
    pass


class OtpError(AuthServiceError):
    pass


class AuthService:
    def __init__(self, db: Session, mailer: Mailer | None = None) -> None:
        self.db = db
        self.mailer = mailer

    def request_otp(self, email: str) -> datetime:
        existing = self.db.query(User).filter(User.email == email).first()
        if existing and not existing.is_active:
            raise RegistrationClosedError("Account deactivated")

        otp = generate_otp()
        otp_hash, otp_salt = new_otp_hash(otp)
        expires_at = otp_expiration()

        if existing:
            existing.otp_hash = f"{otp_hash}:{otp_salt}"
            existing.otp_expires_at = expires_at
            self.db.add(existing)
        else:
            user = User(
                email=email,
                otp_hash=f"{otp_hash}:{otp_salt}",
                otp_expires_at=expires_at,
                is_verified=False,
                is_active=True,
            )
            self.db.add(user)

        self.db.commit()

        if not self.mailer:
            raise AuthServiceError("Mailer not configured")

        try:
            self.mailer.send_otp(email, otp)
        except EmailSendError as exc:
            raise AuthServiceError(str(exc)) from exc

        return expires_at

    def login_with_otp(self, email: str, otp: str) -> str:
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise OtpError("Invalid credentials")

        if not user.is_active:
            raise RegistrationClosedError("Account deactivated")

        if not user.otp_hash or not user.otp_expires_at:
            raise OtpError("OTP not generated")

        if user.otp_expires_at < utcnow():
            raise OtpError("OTP expired")

        otp_hash, otp_salt = user.otp_hash.split(":", 1)
        if not verify_otp(otp, otp_hash, otp_salt):
            raise OtpError("Invalid OTP")

        user.is_verified = True
        user.otp_hash = None
        user.otp_expires_at = None
        self.db.add(user)
        self.db.commit()

        return create_access_token(user.email)
