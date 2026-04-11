import streamlit as st


def render_sidebar(is_authenticated: bool) -> str:
    if not is_authenticated:
        return "auth"

    with st.sidebar:
        st.title("Random Coffee")
        page = st.radio("Navigation", ["Dashboard", "Profile"], index=0)
        if st.button("Logout", use_container_width=True):
            return "logout"
    return "dashboard" if page == "Dashboard" else "profile"
