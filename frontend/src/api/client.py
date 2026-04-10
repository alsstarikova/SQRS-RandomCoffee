from dataclasses import dataclass
from typing import Any

import requests

from src.config import get_backend_url


def _error_message_from_payload(payload: Any) -> str:
    if not isinstance(payload, dict):
        return "Request failed"
    detail = payload.get("detail")
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        parts: list[str] = []
        for item in detail:
            if isinstance(item, dict) and "msg" in item:
                parts.append(str(item["msg"]))
        return "; ".join(parts) if parts else "Validation error"
    return "Request failed"


@dataclass
class ApiResult:
    ok: bool
    status_code: int
    data: Any = None
    error: str | None = None


class ApiClient:
    def __init__(self, timeout: int = 10) -> None:
        self.base_url = get_backend_url()
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        token: str | None = None,
        json: dict[str, Any] | None = None,
    ) -> ApiResult:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            response = requests.request(
                method=method.upper(),
                url=f"{self.base_url}{path}",
                headers=headers,
                json=json,
                timeout=self.timeout,
            )
        except requests.RequestException:
            return ApiResult(ok=False, status_code=0, error="Backend is unavailable")

        payload: Any
        try:
            payload = response.json()
        except ValueError:
            payload = None

        if 200 <= response.status_code < 300:
            return ApiResult(ok=True, status_code=response.status_code, data=payload)

        error = _error_message_from_payload(payload)

        return ApiResult(
            ok=False,
            status_code=response.status_code,
            data=payload,
            error=error,
        )
