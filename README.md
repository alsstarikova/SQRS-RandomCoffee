# Random Coffee

**Random Coffee** — a platform for random meetings and new acquaintances within a university or work environment. The application randomly pairs users weekly for a "coffee chat" (online or offline), helping to expand social circles.

## Key Features

- **Registration & Profile** — email-based registration with OTP verification; editable profile (name, interests, about me, Telegram alias)
- **Weekly Matching** — automatic pairing algorithm (no repeat partners, interest-aware)
- **Match Notifications** — dashboard card with partner info and highlighted common interests
- **Meeting Confirmation & Feedback** — "Meeting took place" button with optional comments
- **JWT Authentication** — stateless session via JSON Web Tokens
- **API Documentation** — interactive Swagger UI at `/docs`, OpenAPI spec at `/openapi.json`

## Tech Stack

| Layer | Tools |
|-------|-------|
| Backend | Python 3.11, FastAPI, SQLAlchemy, SQLite |
| Frontend | Streamlit |
| Package Management | Poetry |
| Quality | Flake8, Radon, Bandit, Pytest, Pytest-cov, Locust |
| CI/CD | GitHub Actions, pre-commit hooks |
| Container | Docker, Docker Compose |

## Repository Structure

```
SQRS-RandomCoffee/
├── .github/
│   └── workflows/
│       └── ci.yml                  # CI pipeline (lint, metrics, security, tests)
├── .pre-commit-config.yaml         # Pre-commit hooks (flake8 + bandit)
├── docker-compose.yml              # Docker Compose (backend + frontend)
├── backend/
│   ├── .flake8                     # Flake8 configuration
│   ├── Dockerfile                  # Backend Docker image (Poetry-based)
│   ├── pyproject.toml              # Poetry deps + tool configs (pytest, ruff, mypy, etc.)
│   ├── poetry.lock                 # Locked dependency versions
│   ├── .env.example                # Environment variables template
│   ├── app/
│   │   ├── main.py                 # FastAPI entry point + APScheduler
│   │   ├── api/                    # Route handlers
│   │   │   ├── auth.py             # POST /login (OTP request & verify)
│   │   │   ├── profile.py          # GET/PATCH /profile, activate/deactivate
│   │   │   ├── matching.py         # POST /matching/run, GET /matching/my, confirm
│   │   │   ├── schemas.py          # Pydantic request/response models
│   │   │   └── deps.py             # Dependency injection (JWT, DB, mailer)
│   │   ├── core/                   # Business logic utilities
│   │   │   ├── auth.py             # JWT token create/decode
│   │   │   ├── security.py         # OTP generation, hashing, verification
│   │   │   ├── emailer.py          # SMTP mailer (OTP + match notifications)
│   │   │   └── settings.py         # Pydantic Settings (env-based config)
│   │   ├── db/                     # Database layer
│   │   │   ├── base.py             # SQLAlchemy declarative base
│   │   │   ├── models.py           # User, Interest, Match, MeetingFeedback
│   │   │   └── session.py          # Engine & session factory
│   │   └── services/               # Service layer
│   │       ├── auth.py             # Registration, OTP, login flow
│   │       ├── profile.py          # Profile CRUD, interests
│   │       └── matching.py         # Matching algorithm (networkx, weighted graph)
│   └── tests/                      # Pytest test suite
│       ├── conftest.py             # Fixtures (in-memory DB, test client)
│       ├── test_auth.py
│       ├── test_profile.py
│       ├── test_matching.py
│       ├── test_unit_core.py
│       └── test_acceptance_scenarios.py
├── frontend/
│   ├── Dockerfile                  # Streamlit Docker image
│   ├── requirements.txt            # Frontend dependencies (streamlit, requests)
│   ├── app.py                      # Streamlit entry point
│   └── src/                        # UI pages, API client, state management
│       ├── api/                    # Backend API client + auth guard
│       ├── pages/                  # Auth, profile, dashboard pages
│       ├── state/                  # Session state management
│       └── ui/                     # Layout, CSS styles
├── load_tests/
│   └── locustfile.py               # Locust performance tests (10 users, 1 min)
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation)
- Docker & Docker Compose *(optional)*

### Local Development (Backend)

```bash
# 1. Clone the repository
git clone <repository-url>
cd SQRS-RandomCoffee/backend

# 2. Install dependencies via Poetry
poetry install

# 3. Configure environment
cp .env.example .env
# Edit .env with your SMTP credentials and SECRET_KEY

# 4. Run the application
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is available at:
- **Root / Health**: http://localhost:8000/
- **Swagger UI**: http://localhost:8000/docs
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Docker (recommended)

Docker Compose starts the backend and the Streamlit frontend.

```bash
# From repository root
docker compose up --build
```

| Service | URL |
|---------|-----|
| Streamlit UI | http://localhost:8501 |
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |

## Quality Gates

The project enforces the following quality checks both locally (pre-commit) and in CI:

| Gate | Tool | Command | Threshold | CI? |
|------|------|---------|-----------|-----|
| Style (lint) | Flake8 | `poetry run flake8 app/` | 0 errors | Yes |
| Cyclomatic Complexity | Radon CC | `poetry run radon cc -a -s app/` | < 10 per function | Yes |
| Maintainability Index | Radon MI | `poetry run radon mi -s app/` | > 25 per module | Yes |
| Security | Bandit | `poetry run bandit -r app/ --severity-level high` | 0 high-severity | Yes |
| Test Coverage | Pytest-cov | `poetry run pytest --cov=app --cov-fail-under=75` | >= 75% | Yes |
| Unit Tests | Pytest | `poetry run pytest` | 100% pass | Yes |
| Performance | Locust | `poetry run locust -f load_tests/locustfile.py --headless -u 10 -r 1 -t 1m` | P95 < 200 ms | Before release |

## Pre-commit Hooks

Pre-commit hooks run **Flake8** (style) and **Bandit** (security) automatically before each commit.

### Setup

```bash
# From the repository root
pip install pre-commit
pre-commit install
```

### Manual Run

```bash
pre-commit run --all-files
```

## CI/CD Pipeline

GitHub Actions runs the full quality gate suite on every **Pull Request** and **push** to `main`/`master`:

1. **Flake8** — PEP 8 style conformance (0 errors)
2. **Radon CC** — cyclomatic complexity < 10 per function
3. **Radon MI** — maintainability index > 25 per module
4. **Bandit** — 0 high-severity security findings
5. **Pytest + Coverage** — all tests pass, line coverage >= 75%

All dependencies are managed via **Poetry** (`poetry install` / `poetry run`).

PRs are **blocked** from merging if any gate fails.

## Branch Protection

The `main` branch is configured with the following protection rules:

- **Require pull request reviews** — at least 1 approving review before merge
- **Require status checks to pass** — the `quality` CI job must succeed
- **No direct pushes** — all changes go through Pull Requests

## Running Quality Checks Locally

```bash
cd backend

# Style
poetry run flake8 app/

# Cyclomatic complexity
poetry run radon cc app/ -a -s

# Maintainability index
poetry run radon mi app/ -s

# Security scan
poetry run bandit -r app/ --severity-level high

# Tests with coverage
poetry run pytest --cov=app --cov-fail-under=75 --cov-report=term-missing

# Performance (requires running API at localhost:8000)
poetry run locust -f ../load_tests/locustfile.py --headless -u 10 -r 1 -t 1m
```

## Configuring Mail SMTP

### 1. Create an Application Password (Mail.Ru)

1. Go to https://id.mail.ru/security
2. In the security section, find **"Passwords for external applications"**
3. Create a password for the application (e.g., "SQRS project") — select **SMTP**
4. Copy the generated password

### 2. Configure `.env`

```env
SMTP_HOST=smtp.mail.ru
SMTP_PORT=465
SMTP_USER=your@mail.ru
SMTP_PASSWORD=<application password from step 1>
SMTP_FROM=your@mail.ru
SMTP_USE_SSL=true
SMTP_USE_TLS=false

SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=60
DATABASE_URL=sqlite:///./app.db
```

## License

This project is developed as part of the *"Software Quality, Reliability and Security"* course.
