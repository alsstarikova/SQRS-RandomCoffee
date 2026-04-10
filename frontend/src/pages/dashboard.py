import streamlit as st

from src.api.auth_guard import exit_if_unauthorized
from src.api.client import ApiClient
from src.state.session import get_auth_token, get_confirmed_match_ids, mark_match_confirmed

_client = ApiClient()


def _is_confirmed(match_id: int) -> bool:
    return match_id in get_confirmed_match_ids()


def render_dashboard_page() -> None:
    st.title("Dashboard")
    token = get_auth_token()
    if not token:
        st.error("Session expired. Please sign in again.")
        return

    with st.spinner("Loading matches…"):
        r = _client.request("GET", "/matching/my", token=token)

    exit_if_unauthorized(r)
    if not r.ok:
        st.error(r.error or "Could not load matches.")
        return

    matches = r.data if isinstance(r.data, list) else []
    if not matches:
        st.info(
            "You have no matches yet. After the weekly matching runs, "
            "your partner will appear here.",
        )
        return

    st.subheader("This week's match")

    for m in matches:
        mid = int(m.get("id", 0))
        week = m.get("week", "")
        created = m.get("created_at", "")
        partners = m.get("partners") or []

        with st.container(border=True):
            st.markdown(f"**Week {week}**")
            if created:
                st.caption(f"Created: {created}")

            for p in partners:
                name = p.get("name") or "Partner"
                email = p.get("email", "")
                st.markdown(f"- **{name}** — `{email}`")

            if _is_confirmed(mid):
                st.success("Meeting confirmed. Thank you.")
                continue

            with st.form(f"meeting_form_{mid}"):
                comment = st.text_area(
                    "Optional feedback",
                    key=f"meeting_comment_{mid}",
                    height=100,
                    max_chars=1000,
                    help="Optional comment after the meeting.",
                )
                submitted = st.form_submit_button(
                    "Meeting took place",
                    use_container_width=True,
                    type="primary",
                )
                if submitted:
                    body: dict = {}
                    c = (comment or "").strip()
                    if c:
                        body["comment"] = c

                    with st.spinner("Submitting…"):
                        res = _client.request(
                            "POST",
                            f"/matching/{mid}/confirm",
                            token=token,
                            json=body,
                        )

                    exit_if_unauthorized(res)
                    if res.ok:
                        mark_match_confirmed(mid)
                        st.success("Meeting recorded. Thank you.")
                        st.rerun()
                    elif res.status_code == 409:
                        mark_match_confirmed(mid)
                        st.info("This meeting was already confirmed.")
                        st.rerun()
                    else:
                        st.error(res.error or "Could not confirm the meeting.")
