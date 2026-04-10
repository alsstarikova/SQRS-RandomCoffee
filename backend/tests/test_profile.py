from tests.utils import auth_headers


def test_profile_update_and_get(client, create_user):
    token = create_user("profile@example.com")
    headers = auth_headers(token)

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


def test_deactivate_account(client, create_user):
    token = create_user("deact@example.com")
    headers = auth_headers(token)

    deactivate = client.post("/profile/deactivate", headers=headers)
    assert deactivate.status_code == 200

    after = client.get("/profile", headers=headers)
    assert after.status_code == 403


def test_activate_account(client, create_user):
    token = create_user("react@example.com")
    headers = auth_headers(token)

    deactivate = client.post("/profile/deactivate", headers=headers)
    assert deactivate.status_code == 200

    activate = client.post("/profile/activate", headers=headers)
    assert activate.status_code == 200

    profile = client.get("/profile", headers=headers)
    assert profile.status_code == 200


def test_invalid_telegram_validation(client, create_user):
    token = create_user("badtelegram@example.com")
    headers = auth_headers(token)

    update = client.patch(
        "/profile",
        json={"telegram": "anna"},
        headers=headers,
    )
    assert update.status_code == 422


def test_invalid_interest_validation(client, create_user):
    token = create_user("badinterest@example.com")
    headers = auth_headers(token)

    update = client.patch(
        "/profile",
        json={"interests": [" ", "music"]},
        headers=headers,
    )
    assert update.status_code == 422
