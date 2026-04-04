import hashlib
import os
import secrets
from datetime import datetime, timedelta


def generate_otp(length: int = 6) -> str:
    max_value = 10**length - 1
    return f"{secrets.randbelow(max_value + 1):0{length}d}"


def hash_otp(otp: str, salt: str) -> str:
    return hashlib.sha256(f"{otp}{salt}".encode()).hexdigest()


def new_otp_hash(otp: str) -> tuple[str, str]:
    salt = secrets.token_hex(8)
    return hash_otp(otp, salt), salt


def utcnow() -> datetime:
    return datetime.utcnow()


def otp_expiration(minutes: int = 10) -> datetime:
    return utcnow() + timedelta(minutes=minutes)


def verify_otp(otp: str, otp_hash: str, salt: str) -> bool:
    return secrets.compare_digest(hash_otp(otp, salt), otp_hash)


def jwt_secret() -> str:
    return os.getenv("SECRET_KEY", "change-me")


def jwt_exp_minutes() -> int:
    return int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
