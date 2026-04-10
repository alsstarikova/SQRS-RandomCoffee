"""Persist auth token in the browser localStorage so F5 does not log the user out."""

from __future__ import annotations

import json
from typing import Optional

LS_TOKEN_KEY = "rc_auth_token"
LS_EMAIL_KEY = "rc_user_email"


def _js_eval(expression: str, component_key: str) -> Optional[str]:
    try:
        from streamlit_js_eval import streamlit_js_eval

        out = streamlit_js_eval(js_expressions=expression, key=component_key)
        if out is None or out == "null":
            return None
        if isinstance(out, str):
            return out
        return str(out)
    except Exception:
        return None


def load_saved_token() -> Optional[str]:
    expr = f"localStorage.getItem({json.dumps(LS_TOKEN_KEY)})"
    t = _js_eval(expr, "rc_load_token")
    if t and len(t) > 20:
        return t
    return None


def save_token(token: str) -> None:
    expr = (
        f"localStorage.setItem({json.dumps(LS_TOKEN_KEY)}, "
        f"{json.dumps(token)})"
    )
    _js_eval(expr, "rc_save_token")


def clear_saved_token() -> None:
    expr = f"localStorage.removeItem({json.dumps(LS_TOKEN_KEY)})"
    _js_eval(expr, "rc_clear_token")


def load_saved_email() -> Optional[str]:
    expr = f"localStorage.getItem({json.dumps(LS_EMAIL_KEY)})"
    e = _js_eval(expr, "rc_load_email")
    if e and e != "null" and "@" in e:
        return e
    return None


def save_email(email: str) -> None:
    expr = (
        f"localStorage.setItem({json.dumps(LS_EMAIL_KEY)}, "
        f"{json.dumps(email)})"
    )
    _js_eval(expr, "rc_save_email")


def clear_saved_email() -> None:
    expr = f"localStorage.removeItem({json.dumps(LS_EMAIL_KEY)})"
    _js_eval(expr, "rc_clear_email")
