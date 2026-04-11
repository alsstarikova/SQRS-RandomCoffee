"""Global Streamlit CSS: mobile-friendly layout (320px+), 44px tap targets."""

import streamlit as st


def inject_mobile_styles() -> None:
    st.markdown(
        """
        <style>
        /* No horizontal scroll on narrow viewports */
        .stApp {
            overflow-x: hidden;
        }
        /* Main content padding on small screens */
        div[data-testid="stMainBlockContainer"] {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        /* Minimum tap target ~44px (WCAG / course checklist) */
        .stButton > button {
            min-height: 44px;
            min-width: 44px;
        }
        div[data-testid="stFormSubmitButton"] > button {
            min-height: 44px;
        }
        /* Radio / sidebar controls */
        [data-testid="stSidebar"] .stButton > button {
            min-height: 44px;
        }
        /* Reduce iOS zoom on focus: keep inputs at 16px+ */
        .stTextInput input,
        .stTextArea textarea,
        [data-baseweb="input"] input {
            font-size: 16px !important;
        }
        /* Sidebar width on very small screens */
        [data-testid="stSidebar"] {
            min-width: 16rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
