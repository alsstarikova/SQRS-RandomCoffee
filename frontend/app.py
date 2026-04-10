import streamlit as st

from src.pages.auth import render_auth_page
from src.pages.dashboard import render_dashboard_page
from src.pages.profile import render_profile_page
from src.state.session import clear_session, get_auth_token, init_session_state
from src.ui.layout import render_sidebar
from src.ui.styles import inject_mobile_styles

st.set_page_config(page_title="Random Coffee", page_icon="☕", layout="centered")


def main() -> None:
    inject_mobile_styles()
    init_session_state()

    selected_page = render_sidebar(is_authenticated=bool(get_auth_token()))

    # Reset profile form when switching to Profile from another tab
    prev = st.session_state.get("_nav_previous_page")
    if (
        selected_page == "profile"
        and prev is not None
        and prev != "profile"
        and prev != "logout"
    ):
        for k in (
            "pf_initialized",
            "pf_name",
            "pf_about",
            "pf_telegram",
            "pf_interests_text",
        ):
            st.session_state.pop(k, None)
    st.session_state["_nav_previous_page"] = selected_page
    if selected_page == "logout":
        clear_session()
        st.rerun()

    if not get_auth_token():
        render_auth_page()
        return

    if selected_page == "profile":
        render_profile_page()
    else:
        render_dashboard_page()


if __name__ == "__main__":
    main()
