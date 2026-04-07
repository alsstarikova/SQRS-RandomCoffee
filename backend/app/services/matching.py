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

_Group = tuple[User, User, Optional[User]]


class MatchingAlreadyRunError(Exception):
    pass


class NotEnoughUsersError(Exception):
    pass


class MatchingService:
    def __init__(self, db: Session, mailer: Optional[Mailer] = None) -> None:
        self.db = db
        self.mailer = mailer

    # ── public API ────────────────────────────────────────────────────────────

    def run_matching(self) -> list[Match]:
        week = datetime.utcnow().strftime("%Y-W%W")
        self._assert_not_run(week)

        users = self._active_verified_users()
        if len(users) < 2:
            raise NotEnoughUsersError("Not enough active verified users to match")

        past_pairs = self._past_pairs()
        groups = self._make_groups(users, past_pairs)
        matches = self._save_groups(groups, week)
        self._notify(matches)
        return [m for m, *_ in matches]

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

        feedback = MeetingFeedback(match_id=match_id, user_id=user_id, comment=comment)
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback

    def _assert_not_run(self, week: str) -> None:
        if self.db.query(Match).filter(Match.week == week).first():
            raise MatchingAlreadyRunError(f"Matching for week {week} already run")

    def _active_verified_users(self) -> list[User]:
        return (
            self.db.query(User)
            .filter(User.is_active.is_(True), User.is_verified.is_(True))
            .all()
        )

    def _past_pairs(self) -> set[frozenset]:
        rows = self.db.query(Match).all()
        return {frozenset({r.user1_id, r.user2_id}) for r in rows}

    def _save_groups(self, groups: list[_Group], week: str) -> list:
        records = []
        for u1, u2, u3 in groups:
            match = Match(
                user1_id=u1.id,
                user2_id=u2.id,
                user3_id=u3.id if u3 else None,
                week=week,
            )
            self.db.add(match)
            records.append((match, u1, u2, u3))
        self.db.commit()
        for match, *_ in records:
            self.db.refresh(match)
        return records

    def _notify(self, matches: list) -> None:
        if not self.mailer:
            return
        for _, u1, u2, u3 in matches:
            members = [u for u in (u1, u2, u3) if u is not None]
            self._notify_members(members)

    def _notify_members(self, members: list[User]) -> None:
        for i, user in enumerate(members):
            partners = [m for j, m in enumerate(members) if j != i]
            self._send_notification(user, partners)

    def _send_notification(self, user: User, partners: list[User]) -> None:
        try:
            self.mailer.send_match_notification(  # type: ignore[union-attr]
                to_email=user.email,
                partners=[(p.email, p.name) for p in partners],
            )
        except Exception:
            pass

    @staticmethod
    def _make_groups(users: list[User], past_pairs: set[frozenset]) -> list[_Group]:
        G, user_by_id = MatchingService._build_graph(users, past_pairs)
        pairs = MatchingService._run_matching(G)
        groups = MatchingService._assign_third(pairs, users, user_by_id, G)
        random.shuffle(groups)
        return groups

    @staticmethod
    def _build_graph(
        users: list[User], past_pairs: set[frozenset]
    ) -> tuple[nx.Graph, dict[int, User]]:
        G: nx.Graph = nx.Graph()
        user_by_id: dict[int, User] = {}
        for u in users:
            G.add_node(u.id)
            user_by_id[u.id] = u
        for i, u in enumerate(users):
            interests_u = {interest.name for interest in u.interests}
            for v in users[i + 1:]:
                is_repeat = frozenset({u.id, v.id}) in past_pairs
                if is_repeat:
                    weight = _WEIGHT_REPEAT
                else:
                    common = len(interests_u & {interest.name for interest in v.interests})
                    weight = _WEIGHT_FRESH_BASE + common
                G.add_edge(u.id, v.id, weight=weight)
        return G, user_by_id

    @staticmethod
    def _run_matching(G: nx.Graph) -> list[tuple[int, int]]:
        matching = nx.max_weight_matching(G, maxcardinality=True)
        return list(matching)

    @staticmethod
    def _assign_third(
        pairs: list[tuple[int, int]],
        users: list[User],
        user_by_id: dict[int, User],
        G: nx.Graph,
    ) -> list[_Group]:
        paired_ids = {uid for pair in pairs for uid in pair}
        unpaired = [u for u in users if u.id not in paired_ids]

        if not unpaired:
            return [(user_by_id[a], user_by_id[b], None) for a, b in pairs]

        weakest_idx = min(
            range(len(pairs)),
            key=lambda i: G[pairs[i][0]][pairs[i][1]]["weight"],
        )
        return [
            (user_by_id[a], user_by_id[b], user_by_id[unpaired[0].id] if i == weakest_idx else None)
            for i, (a, b) in enumerate(pairs)
        ]
