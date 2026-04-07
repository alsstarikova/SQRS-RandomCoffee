from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_allow_inactive
from app.api.schemas import ProfileResponse, ProfileUpdateRequest
from app.db import User
from app.db.session import get_db
from app.services.profile import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    return ProfileResponse(
        email=current_user.email,
        name=current_user.name,
        about=current_user.about,
        telegram=current_user.telegram,
        interests=[interest.name for interest in current_user.interests],
        is_active=current_user.is_active,
    )


@router.patch("", response_model=ProfileResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    service = ProfileService(db)
    current_user = service.update_profile(
        current_user,
        name=payload.name,
        about=payload.about,
        telegram=payload.telegram,
        interests=payload.interests,
    )

    return ProfileResponse(
        email=current_user.email,
        name=current_user.name,
        about=current_user.about,
        telegram=current_user.telegram,
        interests=[interest.name for interest in current_user.interests],
        is_active=current_user.is_active,
    )


@router.post("/deactivate")
def deactivate_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    service = ProfileService(db)
    try:
        service.deactivate(current_user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {"message": "Account deactivated"}


@router.post("/activate")
def activate_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_allow_inactive),
) -> dict:
    service = ProfileService(db)
    try:
        service.activate(current_user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {"message": "Account activated"}
