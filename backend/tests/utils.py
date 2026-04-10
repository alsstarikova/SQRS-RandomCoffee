def auth_headers(access_token: str) -> dict[str, str]:
    """Authorization header for Bearer JWT requests."""
    return {"Authorization": f"Bearer {access_token}"}
