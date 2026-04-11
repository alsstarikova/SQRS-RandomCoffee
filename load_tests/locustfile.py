import os
import random
import sys
import threading
from pathlib import Path


def _backend_dir() -> Path:
    """Resolve backend package dir (Locust may load this file from a temp path)."""
    env = os.environ.get("RANDOMCOFFEE_BACKEND")
    if env:
        return Path(env).resolve()
    cwd_backend = (Path.cwd() / "backend").resolve()
    if (cwd_backend / "app" / "main.py").is_file():
        return cwd_backend
    here = Path(__file__).resolve().parent
    return (here.parent / "backend").resolve()


BACKEND_DIR = _backend_dir()
sys.path.insert(0, str(BACKEND_DIR))


def _load_dotenv_file(path: Path) -> None:
    """Minimal .env loader so SECRET_KEY matches the running API (e.g. Docker)."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, val)


def _bootstrap_env() -> None:
    """Load SECRET_KEY / DB URL from backend/.env (Locust may run with cwd != project root)."""
    candidates = (
        BACKEND_DIR / ".env",
        Path.cwd() / "backend" / ".env",
        Path(__file__).resolve().parent.parent / "backend" / ".env",
    )
    for env_path in candidates:
        if env_path.is_file():
            _load_dotenv_file(env_path)
            break


_bootstrap_env()
# Same file as Docker volume ./backend:/app → ./app.db inside the container.
os.environ["DATABASE_URL"] = "sqlite:///" + str((BACKEND_DIR / "app.db").resolve())

from locust import HttpUser, between, events, task  # noqa: E402

_setup_lock = threading.Lock()
_setup_done = False
_tokens: list = []

# Pre-seed this many users/tokens (≥ concurrent Locust users; assignment uses -u 10).
NUM_USERS = 10
_counter = 0
_counter_lock = threading.Lock()

INTERESTS = [
    "python", "coffee", "music", "travel",
    "sports", "reading", "gaming", "cooking",
]


def _seed_database() -> None:
    """Create verified test users and generate JWT tokens."""
    sys.path.insert(0, str(BACKEND_DIR))
    from app.core.auth import create_access_token
    from app.db.base import Base
    from app.db.models import Interest, User
    from app.db.session import SessionLocal, engine

    global _tokens
    _tokens = []

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for i in range(NUM_USERS):
            # Must be a valid EmailStr domain (not *.local — rejected by pydantic).
            email = f"locust_{i}@example.com"
            if not db.query(User).filter(
                User.email == email
            ).first():
                db.add(User(
                    email=email,
                    is_verified=True,
                    is_active=True,
                    name=f"Locust User {i}",
                    telegram=f"@loc_{i:05d}",
                ))
            _tokens.append(create_access_token(email))

        for name in INTERESTS:
            if not db.query(Interest).filter(
                Interest.name == name
            ).first():
                db.add(Interest(name=name))
        db.commit()
    finally:
        db.close()

    if not _tokens:
        raise RuntimeError(
            "Locust seed failed: no tokens. Check RANDOMCOFFEE_BACKEND "
            f"or cwd (expected backend at {BACKEND_DIR}).",
        )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global _setup_done
    with _setup_lock:
        if not _setup_done:
            _seed_database()
            _setup_done = True


class CoffeeUser(HttpUser):
    """Simulates a typical user browsing the Random Coffee API."""

    wait_time = between(0.5, 1.5)

    def on_start(self):
        global _counter
        if not _tokens:
            raise RuntimeError("Locust tokens not initialized; seed failed.")
        with _counter_lock:
            idx = _counter % len(_tokens)
            _counter += 1
        self.auth = {"Authorization": f"Bearer {_tokens[idx]}"}

    @task(5)
    def health(self):
        self.client.get("/", name="GET /")

    @task(3)
    def get_profile(self):
        self.client.get(
            "/profile", headers=self.auth,
            name="GET /profile",
        )

    @task(2)
    def update_profile(self):
        self.client.patch(
            "/profile",
            headers=self.auth,
            json={
                "name": f"User {random.randint(1, 9999)}",
                "about": "Load testing profile",
                "interests": random.sample(INTERESTS, k=3),
            },
            name="PATCH /profile",
        )

    @task(3)
    def get_matches(self):
        self.client.get(
            "/matching/my", headers=self.auth,
            name="GET /matching/my",
        )

    @task(1)
    def swagger_docs(self):
        self.client.get("/docs", name="GET /docs")

    @task(1)
    def openapi_json(self):
        self.client.get(
            "/openapi.json", name="GET /openapi.json",
        )
