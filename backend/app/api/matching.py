from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_mailer
from app.api.schemas import FeedbackRequest, FeedbackResponse, MatchResponse, MatchRunResponse, PartnerInfo
from app.core.emailer import Mailer
from app.db.models import User
from app.services.matching import MatchingAlreadyRunError, MatchingService, NotEnoughUsersError

router = APIRouter(prefix="/matching", tags=["matching"])


@router.post("/run", response_model=MatchRunResponse)
def run_matching(
    db: Session = Depends(get_db),
    mailer: Mailer = Depends(get_mailer),
    current_user: User = Depends(get_current_user),
) -> MatchRunResponse:
    service = MatchingService(db=db, mailer=mailer)
    try:
        matches = service.run_matching()
    except MatchingAlreadyRunError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except NotEnoughUsersError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    week = matches[0].week if matches else ""
    return MatchRunResponse(week=week, pairs_count=len(matches))


@router.get("/my", response_model=list[MatchResponse])
def get_my_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MatchResponse]:
    service = MatchingService(db=db)
    matches = service.get_my_matches(current_user.id)

    result = []
    for match in matches:
        all_users = [u for u in (match.user1, match.user2, match.user3) if u is not None]
        partners = [
            PartnerInfo(email=u.email, name=u.name)
            for u in all_users
            if u.id != current_user.id
        ]
        result.append(
            MatchResponse(
                id=match.id,
                week=match.week,
                partners=partners,
                created_at=match.created_at,
            )
        )
    return result


@router.post("/{match_id}/confirm", response_model=FeedbackResponse)
def confirm_meeting(
    match_id: int,
    body: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackResponse:
    service = MatchingService(db=db)
    try:
        feedback = service.confirm_meeting(
            match_id=match_id,
            user_id=current_user.id,
            comment=body.comment,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return FeedbackResponse(
        match_id=feedback.match_id,
        confirmed_at=feedback.confirmed_at,
        comment=feedback.comment,
    )
