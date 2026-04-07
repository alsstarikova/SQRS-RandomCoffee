import random
from datetime import datetime
from typing import Optional

import networkx as nx
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.emailer import Mailer
from app.db.models import Match, MeetingFeedback, User

_WEIGHT_FRESH_BASE = 10
_WEIGHT_REPEAT = 1


class MatchingAlreadyRunError(Exception):
    pass


class NotEnoughUsersError(Exception):
    pass


_Group = tuple[User, User, Optional[User]]


class MatchingService:
    def __init__(self, db: Session, mailer: Optional[Mailer] = None) -> None:
        self.db = db
        self.mailer = mailer

    def run_matching(self) -> list[Match]:
        week = datetime.utcnow().strftime("%Y-W%W")

        already_run = self.db.query(Match).filter(Match.week == week).first()
        if already_run:
            raise MatchingAlreadyRunError(f"Matching for week {week} already run")

        users = (
            self.db.query(User)
            .filter(User.is_active == True, User.is_verified == True)
            .all()
        )
        if len(users) < 2:
            raise NotEnoughUsersError("Not enough active verified users to match")

        past_rows = self.db.query(Match).all()
        past_pairs: set[frozenset] = {
            frozenset({row.user1_id, row.user2_id}) for row in past_rows
        }

        groups = self._make_groups(users, past_pairs)

        matches: list[Match] = []
        for u1, u2, u3 in groups:
            match = Match(
                user1_id=u1.id,
                user2_id=u2.id,
                user3_id=u3.id if u3 else None,
                week=week,
            )
            self.db.add(match)
            matches.append((match, u1, u2, u3))

        self.db.commit()

        for match, u1, u2, u3 in matches:
            self.db.refresh(match)
            if self.mailer:
                members = [u for u in (u1, u2, u3) if u is not None]
                for i, user in enumerate(members):
                    partners = [m for j, m in enumerate(members) if j != i]
                    try:
                        self.mailer.send_match_notification(
                            to_email=user.email,
                            partners=[(p.email, p.name) for p in partners],
                        )
                    except Exception:
                        pass

        return [m for m, *_ in matches]

    @staticmethod
    def _make_groups(users: list[User], past_pairs: set[frozenset]) -> list[_Group]:

        G = nx.Graph()
        user_by_id: dict[int, User] = {}

        for u in users:
            G.add_node(u.id)
            user_by_id[u.id] = u

        for i, u in enumerate(users):
            interests_u = {interest.name for interest in u.interests}
            for v in users[i + 1 :]:
                is_repeat = frozenset({u.id, v.id}) in past_pairs
                if is_repeat:
                    weight = _WEIGHT_REPEAT
                else:
                    common = len(
                        interests_u & {interest.name for interest in v.interests}
                    )
                    weight = _WEIGHT_FRESH_BASE + common
                G.add_edge(u.id, v.id, weight=weight)

        matching: set[tuple[int, int]] = nx.max_weight_matching(G, maxcardinality=True)

        paired_ids: set[int] = set()
        pairs: list[tuple[int, int]] = []
        for a, b in matching:
            paired_ids.add(a)
            paired_ids.add(b)
            pairs.append((a, b))

        unpaired = [u for u in users if u.id not in paired_ids]

        groups: list[_Group] = []
        if unpaired:
            weakest_idx = min(
                range(len(pairs)),
                key=lambda i: G[pairs[i][0]][pairs[i][1]]["weight"],
            )
            for i, (a, b) in enumerate(pairs):
                third = user_by_id[unpaired[0].id] if i == weakest_idx else None
                groups.append((user_by_id[a], user_by_id[b], third))
        else:
            for a, b in pairs:
                groups.append((user_by_id[a], user_by_id[b], None))

        random.shuffle(groups)
        return groups

    def get_my_matches(self, user_id: int) -> list[Match]:
        return (
            self.db.query(Match)
            .filter(
                or_(
                    Match.user1_id == user_id,
                    Match.user2_id == user_id,
                    Match.user3_id == user_id,
                )
            )
            .order_by(Match.created_at.desc())
            .all()
        )

    def confirm_meeting(
        self,
        match_id: int,
        user_id: int,
        comment: Optional[str] = None,
    ) -> MeetingFeedback:
        match = self.db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise ValueError("Match not found")

        if user_id not in (match.user1_id, match.user2_id, match.user3_id):
            raise PermissionError("User is not a participant of this match")

        existing = (
            self.db.query(MeetingFeedback)
            .filter(
                MeetingFeedback.match_id == match_id,
                MeetingFeedback.user_id == user_id,
            )
            .first()
        )
        if existing:
            raise LookupError("Already confirmed")

        feedback = MeetingFeedback(
            match_id=match_id,
            user_id=user_id,
            comment=comment,
        )
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback
