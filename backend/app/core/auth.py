from datetime import timedelta

import jwt

from .security import jwt_exp_minutes, jwt_secret, utcnow


class TokenError(Exception):
    pass


def create_access_token(subject: str) -> str:
    expire = utcnow() + timedelta(minutes=jwt_exp_minutes())
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, jwt_secret(), algorithm="HS256")


def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, jwt_secret(), algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise TokenError("Invalid token") from exc

    subject = payload.get("sub")
    if not subject:
        raise TokenError("Invalid token")
    return str(subject)
