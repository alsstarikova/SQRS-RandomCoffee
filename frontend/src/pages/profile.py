import streamlit as st

from src.api.auth_guard import exit_if_unauthorized
from src.api.client import ApiClient
from src.state.session import clear_session, get_auth_token

_client = ApiClient()


def render_profile_page() -> None:
    st.title("Profile")
    token = get_auth_token()
    if not token:
        st.error("Session expired. Please sign in again.")
        return

    r = _client.request("GET", "/profile", token=token)
    exit_if_unauthorized(r)
    if r.status_code == 403:
        detail = (r.error or "").lower()
        if "deactivated" in detail:
            st.warning(
                "Your account is deactivated. You can reactivate it or sign out.",
            )
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Reactivate account", use_container_width=True, type="primary"):
                    act = _client.request("POST", "/profile/activate", token=token)
                    exit_if_unauthorized(act)
                    if act.ok:
                        st.success("Account is active again.")
                        st.rerun()
                    else:
                        st.error(act.error or "Could not reactivate.")
            with c2:
                if st.button("Sign out", use_container_width=True):
                    clear_session()
                    st.rerun()
            return
        st.error(r.error or "Could not access profile.")
        return

    if not r.ok or not isinstance(r.data, dict):
        st.error(r.error or "Could not load profile.")
        return

    data = r.data
    email = data.get("email", "")

    if "pf_initialized" not in st.session_state:
        st.session_state.pf_name = data.get("name") or ""
        st.session_state.pf_about = data.get("about") or ""
        st.session_state.pf_telegram = data.get("telegram") or ""
        interests = data.get("interests") or []
        st.session_state.pf_interests_text = "\n".join(interests)
        st.session_state.pf_initialized = True

    st.caption(f"Email: **{email}**")

    with st.form("profile_edit"):
        st.text_input("Name", max_chars=120, key="pf_name")
        st.text_area(
            "About me",
            height=120,
            max_chars=500,
            key="pf_about",
            help="Up to 500 characters",
        )
        st.text_input(
            "Telegram",
            key="pf_telegram",
            help="Format: @nickname (letters, digits, underscore; 6–33 characters including @)",
        )
        st.text_area(
            "Interests",
            height=140,
            key="pf_interests_text",
            help="One per line. At most 20 items, up to 50 characters each.",
        )
        save = st.form_submit_button("Save", use_container_width=True, type="primary")

    if save:
        name = (st.session_state.pf_name or "").strip()
        about = (st.session_state.pf_about or "").strip()
        telegram = (st.session_state.pf_telegram or "").strip()
        raw_interests = (st.session_state.pf_interests_text or "").splitlines()
        interests = [ln.strip() for ln in raw_interests if ln.strip()]

        if telegram and not telegram.startswith("@"):
            st.error("Telegram alias must start with @.")
            return

        body: dict = {
            "name": name,
            "about": about,
            "telegram": telegram if telegram else None,
            "interests": interests,
        }

        with st.spinner("Saving…"):
            upd = _client.request("PATCH", "/profile", token=token, json=body)
        exit_if_unauthorized(upd)
        if upd.ok and isinstance(upd.data, dict):
            st.success("Profile saved.")
            st.session_state.pop("pf_initialized", None)
            st.rerun()
        else:
            st.error(upd.error or "Could not save.")

    st.divider()
    st.subheader("Account")
    # Successful GET /profile implies is_active=True (inactive users get 403).
    if st.button("Deactivate account", type="secondary"):
        d = _client.request("POST", "/profile/deactivate", token=token)
        exit_if_unauthorized(d)
        if d.ok:
            st.success("Account deactivated.")
            st.session_state.pop("pf_initialized", None)
            st.rerun()
        else:
            st.error(d.error or "Could not deactivate.")
