def _get_token(client, mailer_store, email: str = "profile@example.com") -> str:
    client.post("/login", json={"email": email})
    otp = mailer_store[email]
    login = client.post("/login", json={"email": email, "otp": otp})
    return login.json()["access_token"]


def test_profile_update_and_get(client, mailer_store):
    token = _get_token(client, mailer_store)
    headers = {"Authorization": f"Bearer {token}"}

    update = client.patch(
        "/profile",
        json={
            "name": "Anna",
            "about": "Likes coffee",
            "telegram": "@anna_1",
            "interests": ["Python", "fast api", "coffee"],
        },
        headers=headers,
    )
    assert update.status_code == 200
    data = update.json()
    assert data["name"] == "Anna"
    assert "python" in data["interests"]

    get_profile = client.get("/profile", headers=headers)
    assert get_profile.status_code == 200
    assert get_profile.json()["telegram"] == "@anna_1"


def test_deactivate_account(client, mailer_store):
    token = _get_token(client, mailer_store, email="deact@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    deactivate = client.post("/profile/deactivate", headers=headers)
    assert deactivate.status_code == 200

    after = client.get("/profile", headers=headers)
    assert after.status_code == 403


def test_activate_account(client, mailer_store):
    token = _get_token(client, mailer_store, email="react@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    deactivate = client.post("/profile/deactivate", headers=headers)
    assert deactivate.status_code == 200

    activate = client.post("/profile/activate", headers=headers)
    assert activate.status_code == 200

    profile = client.get("/profile", headers=headers)
    assert profile.status_code == 200


def test_invalid_telegram_validation(client, mailer_store):
    token = _get_token(client, mailer_store, email="badtelegram@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    update = client.patch(
        "/profile",
        json={"telegram": "anna"},
        headers=headers,
    )
    assert update.status_code == 422


def test_invalid_interest_validation(client, mailer_store):
    token = _get_token(client, mailer_store, email="badinterest@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    update = client.patch(
        "/profile",
        json={"interests": [" ", "music"]},
        headers=headers,
    )
    assert update.status_code == 422
