from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_mailer
from app.api.schemas import LoginRequest, LoginResponse
from app.core import Mailer
from app.db.session import get_db
from app.services.auth import (AuthService, AuthServiceError, OtpError,
                               RegistrationClosedError)

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
    mailer: Mailer = Depends(get_mailer),
) -> LoginResponse:
    service = AuthService(db, mailer)
    if payload.otp:
        try:
            token = service.login_with_otp(payload.email, payload.otp)
        except RegistrationClosedError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(exc),
            ) from exc
        except OtpError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        return LoginResponse(
            message="Logged in",
            access_token=token,
            token_type="bearer",
        )

    try:
        expires_at = service.request_otp(payload.email)
    except RegistrationClosedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except AuthServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return LoginResponse(message="OTP sent", expires_at=expires_at)
