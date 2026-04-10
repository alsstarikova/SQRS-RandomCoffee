import streamlit as st

from src.api.client import ApiClient
from src.state.session import (
    get_otp_sent_for_email,
    get_user_email,
    set_auth_token,
    set_otp_sent_for_email,
    set_user_email,
)

_client = ApiClient()


def render_auth_page() -> None:
    st.title("Random Coffee")
    st.subheader("Sign in with email and OTP")

    email_default = get_user_email() or ""
    email = st.text_input(
        "Email",
        value=email_default,
        key="auth_email_input",
    ).strip()

    send_otp = st.button("Send OTP", use_container_width=True, type="primary")
    if send_otp:
        if not email:
            st.error("Please enter your email.")
        else:
            with st.spinner("Sending code…"):
                result = _client.request("POST", "/login", json={"email": email})
            if result.ok and isinstance(result.data, dict):
                set_user_email(email)
                set_otp_sent_for_email(email.lower())
                expires = result.data.get("expires_at")
                if expires:
                    st.success(
                        f"Code sent to {email}. Valid until: {expires}.",
                    )
                else:
                    st.success(f"Code sent to {email}.")
            else:
                st.error(result.error or "Could not send the code.")

    otp_target = get_otp_sent_for_email()
    show_otp = bool(otp_target) and email.lower() == otp_target

    if otp_target and not show_otp:
        st.warning(
            "You changed the email address. Click “Send OTP” again for the new address.",
        )

    if show_otp:
        st.caption(f"Code sent to **{email}**")
        otp = st.text_input(
            "One-time code (6 characters)",
            max_chars=6,
            key="auth_otp_input",
            help="Enter the 6-character code from the email",
        ).strip()

        if st.button("Sign in", use_container_width=True, type="primary"):
            if len(otp) != 6 or not otp.isdigit():
                st.error("Enter the 6-digit code from the email.")
            else:
                with st.spinner("Verifying…"):
                    result = _client.request(
                        "POST",
                        "/login",
                        json={"email": email, "otp": otp},
                    )
                if result.ok and isinstance(result.data, dict):
                    token = result.data.get("access_token")
                    if token:
                        set_user_email(email)
                        set_auth_token(token)
                        set_otp_sent_for_email(None)
                        st.success("Signed in.")
                        st.rerun()
                    else:
                        st.error("Server did not return a token.")
                else:
                    st.error(result.error or "Invalid code or code expired.")
