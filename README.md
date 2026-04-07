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
| Quality | Flake8, Radon, Bandit, Pytest, Pytest-cov, Locust |
| CI/CD | GitHub Actions, pre-commit hooks |
| Container | Docker, Docker Compose |

## Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose *(optional)*

### Local Development

```bash
# 1. Clone the repository
git clone <repository-url>
cd SQRS-RandomCoffee

# 2. Create and activate a virtual environment
cd backend
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows

# 3. Install all dependencies
pip install -r requirements.txt -r requirements-dev.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your SMTP credentials and SECRET_KEY

# 5. Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is available at:
- **Root / Health**: http://localhost:8000/
- **Swagger UI**: http://localhost:8000/docs
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Docker (recommended for local development)

Docker Compose starts the backend together with **Mailpit** — a lightweight local SMTP server that catches all outgoing emails and displays them in a browser UI instead of delivering them to real inboxes. No email credentials required.

```bash
# From repository root
docker compose up --build
```

Once running, the following services are available:

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Mailpit (caught emails) | http://localhost:8025 |

#### Logging in during local development

Because real email delivery is disabled, retrieve OTP codes from the Mailpit inbox:

1. Request an OTP — the email will appear in Mailpit:
   ```bash
   curl -X POST http://localhost:8000/login \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com"}'
   ```
2. Open http://localhost:8025, find the message, and copy the 6-digit code.
3. Exchange the OTP for an access token:
   ```bash
   curl -X POST http://localhost:8000/login \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "otp": "123456"}'
   ```


## Quality Gates

The project enforces the following quality checks both locally (pre-commit) and in CI:

| Gate | Tool | Command | Threshold | CI? |
|------|------|---------|-----------|-----|
| Style (lint) | Flake8 | `flake8 app/` | 0 errors | Yes |
| Cyclomatic Complexity | Radon CC | `radon cc -a -s app/` | < 10 per function | Yes |
| Maintainability Index | Radon MI | `radon mi -s app/` | > 25 per module | Yes |
| Security | Bandit | `bandit -r app/ --severity-level high` | 0 high-severity | Yes |
| Test Coverage | Pytest-cov | `pytest --cov=app --cov-fail-under=75` | ≥ 75% | Yes |
| Unit Tests | Pytest | `pytest` | 100% pass | Yes |
| Performance | Locust | `locust -f load_tests/locustfile.py --headless -u 10 -r 1 -t 1m` | P95 < 200 ms | Before release |

## Pre-commit Hooks

Pre-commit hooks run **Flake8** (style) and **Bandit** (security) automatically before each commit, preventing problematic code from entering the repository.

### Setup

```bash
# From the repository root
pip install pre-commit
pre-commit install
```

### Manual Run

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run
```

## CI/CD Pipeline

GitHub Actions runs the full quality gate suite on every **Pull Request** and **push** to `main`/`master`:

1. **Flake8** — PEP 8 style conformance (0 errors)
2. **Radon CC** — cyclomatic complexity < 10 per function
3. **Radon MI** — maintainability index > 25 per module
4. **Bandit** — 0 high-severity security findings
5. **Pytest + Coverage** — all tests pass, line coverage ≥ 75%

PRs are **blocked** from merging if any gate fails.

## Branch Protection

The `main` branch must be configured with the following protection rules:

- **Require pull request reviews** — at least 1 approving review before merge
- **Require status checks to pass** — the `quality` CI job must succeed
- **No direct pushes** — all changes go through Pull Requests

## Running Quality Checks Locally

```bash
cd backend

# Style
flake8 app/

# Cyclomatic complexity
radon cc app/ -a -s

# Maintainability index
radon mi app/ -s

# Security scan
bandit -r app/ --severity-level high

# Tests with coverage
pytest --cov=app --cov-fail-under=75 --cov-report=term-missing
```

## License

This project is developed as part of the *"Software Quality, Reliability and Security"* course.
