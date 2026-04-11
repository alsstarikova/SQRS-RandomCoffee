"""Redirect to login when the API returns 401."""

import streamlit as st

from src.api.client import ApiResult
from src.state.session import clear_session


def exit_if_unauthorized(result: ApiResult) -> None:
    if result.status_code == 401:
        clear_session()
        st.rerun()
