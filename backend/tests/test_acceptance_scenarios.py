import time

from app.db.models import Match, MeetingFeedback


# ── helpers ──────────────────────────────────────────────────────


def _login(client, mailer_store, email):
    """Complete the OTP flow and return (token, headers)."""
    client.post("/login", json={"email": email})
    otp = mailer_store[email]
    resp = client.post(
        "/login", json={"email": email, "otp": otp}
    )
    token = resp.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


def _fill_profile(client, headers, **kwargs):
    return client.patch("/profile", json=kwargs, headers=headers)


def _make_match(client, mailer_store, create_user, db_session):
    """Create two users, run matching, return (token, headers, match)."""
    tok = create_user("meet_a@example.com")
    create_user("meet_b@example.com")
    hdr = {"Authorization": f"Bearer {tok}"}
    client.post("/matching/run", headers=hdr)
    match = db_session.query(Match).first()
    return tok, hdr, match


# ══════════════════════════════════════════════════════════════════
# Scenario 1 — Registration and Profile
# ══════════════════════════════════════════════════════════════════


class TestScenario1Registration:
    """Successful registration with OTP."""

    def test_request_otp_returns_200(self, client):
        resp = client.post(
            "/login", json={"email": "s1_new@example.com"}
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "OTP sent"

    def test_otp_stored_for_email(self, client, mailer_store):
        client.post(
            "/login", json={"email": "s1_store@example.com"}
        )
        assert "s1_store@example.com" in mailer_store

    def test_otp_is_six_digits(self, client, mailer_store):
        client.post(
            "/login", json={"email": "s1_dig@example.com"}
        )
        otp = mailer_store["s1_dig@example.com"]
        assert len(otp) == 6 and otp.isdigit()

    def test_correct_otp_returns_token(self, client, mailer_store):
        token, _ = _login(
            client, mailer_store, "s1_tok@example.com"
        )
        assert token

    def test_after_login_profile_accessible(
        self, client, mailer_store
    ):
        _, h = _login(
            client, mailer_store, "s1_access@example.com"
        )
        resp = client.get("/profile", headers=h)
        assert resp.status_code == 200
        assert resp.json()["email"] == "s1_access@example.com"

    def test_new_user_has_default_profile(
        self, client, mailer_store
    ):
        _, h = _login(
            client, mailer_store, "s1_dflt@example.com"
        )
        data = client.get("/profile", headers=h).json()
        assert data["name"] is None
        assert data["interests"] == []
        assert data["is_active"] is True


class TestScenario1Validation:
    """Validation on registration — invalid / empty fields."""

    def test_invalid_email_rejected(self, client):
        resp = client.post("/login", json={"email": "not-email"})
        assert resp.status_code == 422

    def test_empty_email_rejected(self, client):
        resp = client.post("/login", json={"email": ""})
        assert resp.status_code == 422

    def test_missing_email_rejected(self, client):
        resp = client.post("/login", json={})
        assert resp.status_code == 422

    def test_error_contains_detail(self, client):
        resp = client.post("/login", json={"email": "bad"})
        assert "detail" in resp.json()


class TestScenario1ProfileEditing:
    """Profile editing — update persists and displays correctly."""

    def test_full_update(self, client, mailer_store):
        _, h = _login(
            client, mailer_store, "s1_edit@example.com"
        )
        resp = _fill_profile(
            client, h,
            name="Alice",
            about="Loves coffee",
            telegram="@alice_test",
            interests=["Python", "Coffee"],
        )
        assert resp.status_code == 200
        d = resp.json()
        assert d["name"] == "Alice"
        assert d["about"] == "Loves coffee"
        assert d["telegram"] == "@alice_test"
        assert set(d["interests"]) == {"python", "coffee"}

    def test_changes_persist_on_reread(self, client, mailer_store):
        _, h = _login(
            client, mailer_store, "s1_pers@example.com"
        )
        _fill_profile(client, h, name="Bob", telegram="@bob_test")
        data = client.get("/profile", headers=h).json()
        assert data["name"] == "Bob"
        assert data["telegram"] == "@bob_test"

    def test_partial_update_preserves_fields(
        self, client, mailer_store
    ):
        _, h = _login(
            client, mailer_store, "s1_part@example.com"
        )
        _fill_profile(
            client, h,
            name="Carol", about="Hi", telegram="@carol_test",
        )
        client.patch(
            "/profile", json={"name": "Dana"}, headers=h
        )
        data = client.get("/profile", headers=h).json()
        assert data["name"] == "Dana"
        assert data["about"] == "Hi"
        assert data["telegram"] == "@carol_test"

    def test_disable_account(self, client, mailer_store):
        _, h = _login(
            client, mailer_store, "s1_dis@example.com"
        )
        assert client.post(
            "/profile/deactivate", headers=h
        ).status_code == 200
        assert client.get(
            "/profile", headers=h
        ).status_code == 403


# ══════════════════════════════════════════════════════════════════
# Scenario 2 — Weekly Matching
# ══════════════════════════════════════════════════════════════════


class TestScenario2Matching:
    """Matching creates pairs for active users only."""

    def test_active_users_get_matched(
        self, client, mailer_store, create_user
    ):
        t = create_user("s2_a@example.com")
        create_user("s2_b@example.com")
        h = {"Authorization": f"Bearer {t}"}
        resp = client.post("/matching/run", headers=h)
        assert resp.status_code == 200
        assert resp.json()["pairs_count"] >= 1

    def test_each_user_sees_their_match(
        self, client, mailer_store, create_user
    ):
        ta = create_user("s2_sa@example.com")
        tb = create_user("s2_sb@example.com")
        client.post(
            "/matching/run",
            headers={"Authorization": f"Bearer {ta}"},
        )
        for tok in (ta, tb):
            h = {"Authorization": f"Bearer {tok}"}
            matches = client.get("/matching/my", headers=h).json()
            assert len(matches) >= 1

    def test_match_includes_partner_name_email(
        self, client, mailer_store, create_user
    ):
        ta = create_user("s2_ia@example.com")
        create_user("s2_ib@example.com")
        h = {"Authorization": f"Bearer {ta}"}
        client.post("/matching/run", headers=h)
        matches = client.get("/matching/my", headers=h).json()
        p = matches[0]["partners"][0]
        assert "email" in p and "name" in p
        assert p["email"] == "s2_ib@example.com"

    def test_deactivated_user_excluded(
        self, client, mailer_store, create_user
    ):
        ta = create_user("s2_ea@example.com")
        tb = create_user("s2_eb@example.com")
        client.post(
            "/profile/deactivate",
            headers={"Authorization": f"Bearer {tb}"},
        )
        resp = client.post(
            "/matching/run",
            headers={"Authorization": f"Bearer {ta}"},
        )
        assert resp.status_code == 400

    def test_match_has_week_field(
        self, client, mailer_store, create_user
    ):
        ta = create_user("s2_wa@example.com")
        create_user("s2_wb@example.com")
        h = {"Authorization": f"Bearer {ta}"}
        client.post("/matching/run", headers=h)
        matches = client.get("/matching/my", headers=h).json()
        assert matches[0]["week"]


# ══════════════════════════════════════════════════════════════════
# Scenario 3 — Match Notification
# ══════════════════════════════════════════════════════════════════


class TestScenario3Notification:
    """Notifications are sent after matching with partner info."""

    def test_both_users_notified(
        self, client, mailer_store, create_user,
        notification_store,
    ):
        ta = create_user("s3_na@example.com")
        create_user("s3_nb@example.com")
        client.post(
            "/matching/run",
            headers={"Authorization": f"Bearer {ta}"},
        )
        assert len(notification_store) >= 2

    def test_notification_has_partner_info(
        self, client, mailer_store, create_user,
        notification_store,
    ):
        ta = create_user("s3_pa@example.com")
        create_user("s3_pb@example.com")
        client.post(
            "/matching/run",
            headers={"Authorization": f"Bearer {ta}"},
        )
        notif = notification_store[0]
        assert "to" in notif
        assert "partners" in notif
        assert len(notif["partners"]) >= 1

    def test_match_card_has_created_at(
        self, client, mailer_store, create_user
    ):
        ta = create_user("s3_ca@example.com")
        create_user("s3_cb@example.com")
        h = {"Authorization": f"Bearer {ta}"}
        client.post("/matching/run", headers=h)
        m = client.get("/matching/my", headers=h).json()[0]
        assert "created_at" in m


# ══════════════════════════════════════════════════════════════════
# Scenario 4 — Meeting Confirmation and Feedback
# ══════════════════════════════════════════════════════════════════


class TestScenario4MeetingFeedback:
    """Confirm meeting and optionally leave feedback."""

    def test_confirm_returns_200(
        self, client, mailer_store, create_user, db_session
    ):
        _, h, match = _make_match(
            client, mailer_store, create_user, db_session
        )
        resp = client.post(
            f"/matching/{match.id}/confirm",
            json={}, headers=h,
        )
        assert resp.status_code == 200

    def test_confirm_returns_match_id(
        self, client, mailer_store, create_user, db_session
    ):
        _, h, match = _make_match(
            client, mailer_store, create_user, db_session
        )
        data = client.post(
            f"/matching/{match.id}/confirm",
            json={}, headers=h,
        ).json()
        assert data["match_id"] == match.id

    def test_feedback_comment_saved_in_db(
        self, client, mailer_store, create_user, db_session
    ):
        _, h, match = _make_match(
            client, mailer_store, create_user, db_session
        )
        client.post(
            f"/matching/{match.id}/confirm",
            json={"comment": "Great chat!"},
            headers=h,
        )
        fb = db_session.query(MeetingFeedback).first()
        assert fb is not None
        assert fb.comment == "Great chat!"

    def test_feedback_without_comment(
        self, client, mailer_store, create_user, db_session
    ):
        _, h, match = _make_match(
            client, mailer_store, create_user, db_session
        )
        data = client.post(
            f"/matching/{match.id}/confirm",
            json={}, headers=h,
        ).json()
        assert data["comment"] is None

    def test_response_under_2_seconds(
        self, client, mailer_store, create_user, db_session
    ):
        _, h, match = _make_match(
            client, mailer_store, create_user, db_session
        )
        start = time.monotonic()
        resp = client.post(
            f"/matching/{match.id}/confirm",
            json={"comment": "Quick!"},
            headers=h,
        )
        elapsed = time.monotonic() - start
        assert resp.status_code == 200
        assert elapsed < 2.0

    def test_double_confirm_rejected(
        self, client, mailer_store, create_user, db_session
    ):
        _, h, match = _make_match(
            client, mailer_store, create_user, db_session
        )
        client.post(
            f"/matching/{match.id}/confirm",
            json={}, headers=h,
        )
        second = client.post(
            f"/matching/{match.id}/confirm",
            json={}, headers=h,
        )
        assert second.status_code == 409


# ══════════════════════════════════════════════════════════════════
# Scenario 5 — Authentication
# ══════════════════════════════════════════════════════════════════


class TestScenario5Authentication:
    """OTP login, invalid login, invalid OTP."""

    def test_full_otp_flow(self, client, mailer_store):
        client.post(
            "/login", json={"email": "s5_f@example.com"}
        )
        otp = mailer_store["s5_f@example.com"]
        resp = client.post(
            "/login",
            json={"email": "s5_f@example.com", "otp": otp},
        )
        assert resp.status_code == 200
        assert resp.json()["access_token"]

    def test_invalid_email_error(self, client):
        resp = client.post("/login", json={"email": "invalid"})
        assert resp.status_code == 422
        assert "detail" in resp.json()

    def test_wrong_otp_error(self, client, mailer_store):
        client.post(
            "/login", json={"email": "s5_w@example.com"}
        )
        resp = client.post(
            "/login",
            json={"email": "s5_w@example.com", "otp": "000000"},
        )
        assert resp.status_code == 400

    def test_wrong_otp_no_token(self, client, mailer_store):
        client.post(
            "/login", json={"email": "s5_nt@example.com"}
        )
        resp = client.post(
            "/login",
            json={"email": "s5_nt@example.com", "otp": "000000"},
        )
        assert resp.json().get("access_token") is None

    def test_unauthenticated_profile_blocked(self, client):
        assert client.get("/profile").status_code == 403

    def test_invalid_bearer_rejected(self, client):
        h = {"Authorization": "Bearer invalid.jwt.token"}
        assert client.get("/profile", headers=h).status_code == 401

    def test_deactivated_user_cannot_request_otp(
        self, client, mailer_store
    ):
        _, h = _login(
            client, mailer_store, "s5_d@example.com"
        )
        client.post("/profile/deactivate", headers=h)
        resp = client.post(
            "/login", json={"email": "s5_d@example.com"}
        )
        assert resp.status_code == 403


# ══════════════════════════════════════════════════════════════════
# Scenario 7 — API Documentation
# ══════════════════════════════════════════════════════════════════


class TestScenario7ApiDocs:
    """Swagger UI and OpenAPI JSON availability."""

    def test_swagger_ui_returns_html(self, client):
        resp = client.get("/docs")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_openapi_json_returns_200(self, client):
        assert client.get("/openapi.json").status_code == 200

    def test_openapi_json_structure(self, client):
        data = client.get("/openapi.json").json()
        assert "openapi" in data
        assert "paths" in data
        assert "info" in data

    def test_all_endpoints_listed(self, client):
        paths = client.get("/openapi.json").json()["paths"]
        required = [
            "/login",
            "/profile",
            "/matching/run",
            "/matching/my",
            "/matching/{match_id}/confirm",
        ]
        for ep in required:
            assert ep in paths, f"{ep} not in OpenAPI spec"

    def test_login_endpoint_has_schemas(self, client):
        login = client.get("/openapi.json").json()
        post = login["paths"]["/login"]["post"]
        assert "requestBody" in post
        assert "responses" in post

    def test_openapi_title(self, client):
        info = client.get("/openapi.json").json()["info"]
        assert info["title"] == "RandomCoffee Backend"


# ══════════════════════════════════════════════════════════════════
# Health endpoint (basic smoke test)
# ══════════════════════════════════════════════════════════════════


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
