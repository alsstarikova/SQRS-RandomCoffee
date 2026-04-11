import os


def get_backend_url() -> str:
    return os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
