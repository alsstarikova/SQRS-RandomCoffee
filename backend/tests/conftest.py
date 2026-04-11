import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_mailer
from app.core.emailer import Mailer
from app.core.settings import Settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine, autocommit=False, autoflush=False, future=True
    )
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def mailer_store() -> dict:
    return {}


@pytest.fixture()
def notification_store() -> list:
    return []


@pytest.fixture()
def client(
    db_session: Session,
    mailer_store: dict,
    notification_store: list,
) -> TestClient:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    class FakeMailer(Mailer):
        def __init__(self) -> None:
            super().__init__(Settings())

        def send_otp(self, to_email: str, otp: str) -> None:
            mailer_store[to_email] = otp

        def send_match_notification(
            self, to_email: str, partners
        ) -> None:
            notification_store.append({
                "to": to_email,
                "partners": partners,
            })

    def override_get_mailer():
        return FakeMailer()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_mailer] = override_get_mailer
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def create_user(client, mailer_store):
    """Factory: register + login a user via OTP, return token."""
    def _factory(email: str) -> str:
        client.post("/login", json={"email": email})
        otp = mailer_store[email]
        resp = client.post(
            "/login", json={"email": email, "otp": otp}
        )
        return resp.json()["access_token"]
    return _factory
