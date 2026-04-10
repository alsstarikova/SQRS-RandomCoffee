import streamlit as st

from src.state import browser_storage

AUTH_TOKEN_KEY = "auth_token"
USER_EMAIL_KEY = "user_email"
OTP_SENT_EMAIL_KEY = "otp_sent_for_email"
CONFIRMED_MATCH_IDS_KEY = "confirmed_match_ids"


def init_session_state() -> None:
    if AUTH_TOKEN_KEY not in st.session_state:
        restored = browser_storage.load_saved_token()
        st.session_state[AUTH_TOKEN_KEY] = restored
    if USER_EMAIL_KEY not in st.session_state:
        restored_email = browser_storage.load_saved_email()
        st.session_state[USER_EMAIL_KEY] = restored_email or ""
    if OTP_SENT_EMAIL_KEY not in st.session_state:
        st.session_state[OTP_SENT_EMAIL_KEY] = None
    if CONFIRMED_MATCH_IDS_KEY not in st.session_state:
        st.session_state[CONFIRMED_MATCH_IDS_KEY] = []


def set_auth_token(token: str) -> None:
    st.session_state[AUTH_TOKEN_KEY] = token
    browser_storage.save_token(token)


def get_auth_token() -> str | None:
    return st.session_state.get(AUTH_TOKEN_KEY)


def set_user_email(email: str) -> None:
    st.session_state[USER_EMAIL_KEY] = email
    if email:
        browser_storage.save_email(email)


def get_user_email() -> str:
    return st.session_state.get(USER_EMAIL_KEY, "")


def clear_session() -> None:
    browser_storage.clear_saved_token()
    browser_storage.clear_saved_email()
    st.session_state[AUTH_TOKEN_KEY] = None
    st.session_state[USER_EMAIL_KEY] = ""
    st.session_state[OTP_SENT_EMAIL_KEY] = None
    st.session_state[CONFIRMED_MATCH_IDS_KEY] = []


def set_otp_sent_for_email(email: str | None) -> None:
    st.session_state[OTP_SENT_EMAIL_KEY] = email


def get_otp_sent_for_email() -> str | None:
    return st.session_state.get(OTP_SENT_EMAIL_KEY)


def get_confirmed_match_ids() -> set[int]:
    raw = st.session_state.get(CONFIRMED_MATCH_IDS_KEY) or []
    return set(int(x) for x in raw)


def mark_match_confirmed(match_id: int) -> None:
    raw = list(st.session_state.get(CONFIRMED_MATCH_IDS_KEY) or [])
    if match_id not in raw:
        raw.append(match_id)
    st.session_state[CONFIRMED_MATCH_IDS_KEY] = raw
