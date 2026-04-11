from unittest.mock import patch

from app.db.models import Match, MeetingFeedback

from tests.utils import auth_headers


def _get_token(client, mailer_store, email: str) -> str:
    client.post("/login", json={"email": email})
    otp = mailer_store[email]
    login = client.post("/login", json={"email": email, "otp": otp})
    return login.json()["access_token"]


def _register(client, mailer_store, email: str) -> str:
    return _get_token(client, mailer_store, email)


# ── run matching ──────────────────────────────────────────────────────────────


def test_run_matching_creates_pairs(client, mailer_store, db_session):
    token_a = _register(client, mailer_store, "alice@example.com")
    _register(client, mailer_store, "bob@example.com")

    resp = client.post("/matching/run", headers=auth_headers(token_a))
    assert resp.status_code == 200
    data = resp.json()
    assert data["pairs_count"] == 1
    assert "week" in data

    matches = db_session.query(Match).all()
    assert len(matches) == 1


def test_run_matching_twice_same_week(client, mailer_store):
    _register(client, mailer_store, "c@example.com")
    _register(client, mailer_store, "d@example.com")
    token = _get_token(client, mailer_store, "c@example.com")
    headers = auth_headers(token)

    assert client.post("/matching/run", headers=headers).status_code == 200
    assert client.post("/matching/run", headers=headers).status_code == 409


def test_run_matching_not_enough_users(client, mailer_store):
    token = _register(client, mailer_store, "alone@example.com")
    assert client.post("/matching/run", headers=auth_headers(token)).status_code == 400


def test_run_matching_requires_auth(client):
    assert client.post("/matching/run").status_code == 403


# ── тройка при нечётном числе ─────────────────────────────────────────────────


def test_odd_users_form_triple(client, mailer_store, db_session):
    token_a = _register(client, mailer_store, "t1@example.com")
    _register(client, mailer_store, "t2@example.com")
    _register(client, mailer_store, "t3@example.com")

    resp = client.post("/matching/run", headers=auth_headers(token_a))
    assert resp.status_code == 200
    # 3 пользователя → 1 матч (тройка), а не 1 пара + 1 пропущенный
    assert resp.json()["pairs_count"] == 1

    match = db_session.query(Match).first()
    assert match.user3_id is not None  # тройка сохранена


def test_triple_all_three_see_two_partners(client, mailer_store, db_session):
    token_a = _register(client, mailer_store, "tr_a@example.com")
    token_b = _register(client, mailer_store, "tr_b@example.com")
    token_c = _register(client, mailer_store, "tr_c@example.com")

    client.post("/matching/run", headers=auth_headers(token_a))

    for token in (token_a, token_b, token_c):
        resp = client.get("/matching/my", headers=auth_headers(token))
        assert resp.status_code == 200
        matches = resp.json()
        assert len(matches) == 1
        assert len(matches[0]["partners"]) == 2  # каждый видит двух партнёров


def test_triple_all_three_can_confirm(client, mailer_store, db_session):
    token_a = _register(client, mailer_store, "cftr_a@example.com")
    token_b = _register(client, mailer_store, "cftr_b@example.com")
    token_c = _register(client, mailer_store, "cftr_c@example.com")

    client.post("/matching/run", headers=auth_headers(token_a))
    match = db_session.query(Match).first()

    for token in (token_a, token_b, token_c):
        resp = client.post(
            f"/matching/{match.id}/confirm", json={}, headers=auth_headers(token)
        )
        assert resp.status_code == 200

    feedbacks = db_session.query(MeetingFeedback).all()
    assert len(feedbacks) == 3


# ── get my matches ─────────────────────────────────────────────────────────────


def test_get_my_matches_pair(client, mailer_store):
    token_a = _register(client, mailer_store, "ma@example.com")
    _register(client, mailer_store, "mb@example.com")

    client.post("/matching/run", headers=auth_headers(token_a))

    resp = client.get("/matching/my", headers=auth_headers(token_a))
    assert resp.status_code == 200
    matches = resp.json()
    assert len(matches) == 1
    assert len(matches[0]["partners"]) == 1
    assert matches[0]["partners"][0]["email"] == "mb@example.com"


# ── confirm meeting ────────────────────────────────────────────────────────────


def test_confirm_meeting(client, mailer_store, db_session):
    token_a = _register(client, mailer_store, "conf_a@example.com")
    _register(client, mailer_store, "conf_b@example.com")

    client.post("/matching/run", headers=auth_headers(token_a))
    match = db_session.query(Match).first()

    resp = client.post(
        f"/matching/{match.id}/confirm",
        json={"comment": "Отличная встреча!"},
        headers=auth_headers(token_a),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["comment"] == "Отличная встреча!"
    assert data["match_id"] == match.id


def test_confirm_meeting_no_comment(client, mailer_store, db_session):
    token_a = _register(client, mailer_store, "nocom_a@example.com")
    _register(client, mailer_store, "nocom_b@example.com")

    client.post("/matching/run", headers=auth_headers(token_a))
    match = db_session.query(Match).first()

    resp = client.post(
        f"/matching/{match.id}/confirm", json={}, headers=auth_headers(token_a)
    )
    assert resp.status_code == 200
    assert resp.json()["comment"] is None


def test_confirm_meeting_twice_returns_409(client, mailer_store, db_session):
    token_a = _register(client, mailer_store, "dup_a@example.com")
    _register(client, mailer_store, "dup_b@example.com")

    client.post("/matching/run", headers=auth_headers(token_a))
    match = db_session.query(Match).first()

    client.post(f"/matching/{match.id}/confirm", json={}, headers=auth_headers(token_a))
    second = client.post(
        f"/matching/{match.id}/confirm", json={}, headers=auth_headers(token_a)
    )
    assert second.status_code == 409


def test_confirm_meeting_wrong_user_returns_403(client, mailer_store, db_session):
    token_a = _register(client, mailer_store, "wr_a@example.com")
    _register(client, mailer_store, "wr_b@example.com")

    client.post("/matching/run", headers=auth_headers(token_a))
    match = db_session.query(Match).first()

    token_c = _register(client, mailer_store, "wr_c@example.com")
    resp = client.post(
        f"/matching/{match.id}/confirm", json={}, headers=auth_headers(token_c)
    )
    assert resp.status_code == 403


def test_confirm_nonexistent_match_returns_404(client, mailer_store):
    token = _register(client, mailer_store, "ghost@example.com")
    assert (
        client.post(
            "/matching/9999/confirm", json={}, headers=auth_headers(token)
        ).status_code
        == 404
    )


# ── no repeat pairs ────────────────────────────────────────────────────────────


def test_matching_avoids_repeat_pairs(client, mailer_store, db_session):
    token_a = _register(client, mailer_store, "rep_a@example.com")
    _register(client, mailer_store, "rep_b@example.com")
    _register(client, mailer_store, "rep_c@example.com")

    client.post("/matching/run", headers=auth_headers(token_a))

    first_matches = db_session.query(Match).all()
    first_pairs = {frozenset({m.user1_id, m.user2_id}) for m in first_matches}

    with patch("app.services.matching.datetime") as mock_dt:
        mock_dt.utcnow.return_value.strftime = lambda fmt: "2099-W99"
        client.post("/matching/run", headers=auth_headers(token_a))

    second_matches = db_session.query(Match).filter(Match.week == "2099-W99").all()
    second_pairs = {frozenset({m.user1_id, m.user2_id}) for m in second_matches}

    for pair in second_pairs:
        assert pair not in first_pairs or len(second_pairs) == 0
