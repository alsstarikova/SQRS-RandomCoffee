from sqlalchemy.orm import Session

from app.db import Interest, User


class ProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def update_profile(
        self,
        user: User,
        name: str | None,
        about: str | None,
        telegram: str | None,
        interests: list[str] | None,
    ) -> User:
        if name is not None:
            user.name = name
        if about is not None:
            user.about = about
        if telegram is not None:
            user.telegram = telegram

        if interests is not None:
            cleaned = [
                self._normalize_interest(item) for item in interests if item.strip()
            ]
            unique_names = list(dict.fromkeys(cleaned))
            resolved: list[Interest] = []
            for name_item in unique_names:
                interest = (
                    self.db.query(Interest).filter(Interest.name == name_item).first()
                )
                if not interest:
                    interest = Interest(name=name_item)
                    self.db.add(interest)
                    self.db.flush()
                resolved.append(interest)
            user.interests = resolved

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def deactivate(self, user: User) -> None:
        if not user.is_active:
            raise ValueError("Account already deactivated")
        user.is_active = False
        self.db.add(user)
        self.db.commit()

    def activate(self, user: User) -> None:
        if user.is_active:
            raise ValueError("Account already active")
        user.is_active = True
        self.db.add(user)
        self.db.commit()

    @staticmethod
    def _normalize_interest(name: str) -> str:
        return " ".join(name.strip().lower().split())
