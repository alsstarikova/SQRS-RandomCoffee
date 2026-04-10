from datetime import datetime, timedelta

import pytest

from app.core.auth import TokenError, create_access_token, decode_token
from app.core.security import (
    generate_otp,
    hash_otp,
    jwt_exp_minutes,
    jwt_secret,
    new_otp_hash,
    otp_expiration,
    utcnow,
    verify_otp,
)


# ── OTP generation ───────────────────────────────────────────────


class TestGenerateOtp:
    def test_default_length_six(self):
        assert len(generate_otp()) == 6

    def test_digits_only(self):
        for _ in range(20):
            assert generate_otp().isdigit()

    def test_custom_length(self):
        otp = generate_otp(length=8)
        assert len(otp) == 8 and otp.isdigit()

    def test_produces_varying_values(self):
        values = {generate_otp() for _ in range(50)}
        assert len(values) > 1


# ── OTP hashing ──────────────────────────────────────────────────


class TestOtpHashing:
    def test_hash_and_verify_roundtrip(self):
        hashed, salt = new_otp_hash("123456")
        assert verify_otp("123456", hashed, salt)

    def test_wrong_otp_fails_verification(self):
        hashed, salt = new_otp_hash("123456")
        assert not verify_otp("654321", hashed, salt)

    def test_same_salt_deterministic(self):
        assert hash_otp("111111", "s") == hash_otp("111111", "s")

    def test_different_salt_different_hash(self):
        assert hash_otp("111111", "a") != hash_otp("111111", "b")


# ── time helpers ─────────────────────────────────────────────────


class TestTimeHelpers:
    def test_utcnow_type(self):
        assert isinstance(utcnow(), datetime)

    def test_otp_expiration_in_future(self):
        assert otp_expiration() > utcnow()

    def test_otp_expiration_custom_minutes(self):
        exp = otp_expiration(minutes=5)
        expected = utcnow() + timedelta(minutes=5)
        assert abs((exp - expected).total_seconds()) < 2


# ── JWT config ───────────────────────────────────────────────────


class TestJwtConfig:
    def test_secret_is_string(self):
        assert isinstance(jwt_secret(), str)

    def test_exp_minutes_positive_int(self):
        val = jwt_exp_minutes()
        assert isinstance(val, int) and val > 0


# ── JWT tokens ───────────────────────────────────────────────────


class TestJwtTokens:
    def test_create_and_decode(self):
        token = create_access_token("user@example.com")
        assert decode_token(token) == "user@example.com"

    def test_decode_invalid_raises(self):
        with pytest.raises(TokenError):
            decode_token("not.a.valid.token")

    def test_decode_empty_raises(self):
        with pytest.raises(TokenError):
            decode_token("")

    def test_token_is_nonempty_string(self):
        token = create_access_token("a@b.com")
        assert isinstance(token, str) and len(token) > 0
