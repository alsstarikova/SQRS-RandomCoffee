def test_register_verify_login(client, mailer_store):
    start = client.post("/login", json={"email": "user@example.com"})
    assert start.status_code == 200
    otp = mailer_store["user@example.com"]
    login = client.post("/login", json={"email": "user@example.com", "otp": otp})
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert token


def test_login_invalid_otp(client, mailer_store):
    client.post("/login", json={"email": "novalid@example.com"})
    login = client.post(
        "/login",
        json={"email": "novalid@example.com", "otp": "000000"},
    )
    assert login.status_code == 400


def test_invalid_otp(client):
    client.post("/login", json={"email": "wrongotp@example.com"})
    login = client.post("/login", json={"email": "wrongotp@example.com", "otp": "000000"})
    assert login.status_code == 400
