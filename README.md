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

Docker Compose starts the backend and all required services.

```bash
# From repository root
docker compose up --build
```

Once running, the following services are available:

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |

### Configuring Mail.ru SMTP

To send emails from the application (e.g. OTP codes), configure Mail.ru SMTP:

#### 1. Create an Application Password in Mail.ru

1. Open https://id.mail.ru/security
2. In the security section, find **"Passwords for external applications"** and create a password for the application (e.g. `"SQRS project"`). Select **SMTP** to enable sending emails.
3. Copy the generated password — you will need it in the next step.

#### 2. Write the settings in `.env`

```env
SMTP_HOST=smtp.mail.ru
SMTP_PORT=465
SMTP_USER=your@mail.ru
SMTP_PASSWORD=<application password from step 1>
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
