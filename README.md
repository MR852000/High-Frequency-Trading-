# HFT Backtesting & Signal Engine Real Time Operation 
I make full-stack quant backend operational system/backtesting portfolio project:

- **Backend:** FastAPI (async), SQLAlchemy 2.0 (async, PostgreSQL), Redis cache
- **Frontend:** ReactPy (server-rendered React components in pure Python) — the "Barclays HFT" dashboard
- **Migrations:** Alembic
- **Containers:** Docker + Docker Compose (app, Postgres, Redis, Adminer)
- **CI/CD:** GitHub Actions (lint → test → build → push image to GHCR)

## Project layout
```
hft-engine/
├── main.py                # FastAPI entrypoint (routers, lifespan, ReactPy mount)
├── app/
│   ├── config.py            # Settings (env vars / .env)
│   ├── database.py          # Async SQLAlchemy engine + session
│   ├── models.py             # ORM models
│   ├── schemas.py             # Pydantic request/response models
│   ├── crud.py                 # DB access functions
│   ├── cache.py                 # Redis helper
│   ├── routers/                  # health.py, signals.py, backtest.py
│   └── ui.py                       # ReactPy dashboard component tree
├── alembic/                # DB migrations
├── tests/                   # pytest (SQLite in-memory, no external services needed)
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/ci-cd.yml
```

## Option A — Run with Docker (recommended, fastest)

Requires Docker Desktop.

```bash
cd hft-engine
copy .env.example .env        # Windows (or `cp .env.example .env` on macOS/Linux)
docker compose up --build
```

This starts:
| Service  | URL                          |
|----------|------------------------------|
| App (dashboard + API) | http://localhost:8000 |
| API docs (Swagger)    | http://localhost:8000/docs |
| Health check          | http://localhost:8000/health |
| Adminer (DB browser)  | http://localhost:8080 |
| Postgres              | localhost:5432 |
| Redis                 | localhost:6379 |

The app auto-creates tables on first boot in dev mode. To use real migrations instead, run once the containers are up:

```bash
docker compose exec app alembic upgrade head
```

Stop everything with `docker compose down` (add `-v` to also wipe the Postgres volume).

## Option B — Run natively (no Docker)

You'll need Python 3.12+ and a local Postgres + Redis (or point `.env` at cloud instances).

```bash
cd hft-engine
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements-dev.txt
copy .env.example .env
# edit .env: set DATABASE_URL and REDIS_URL to your local Postgres/Redis

alembic upgrade head
uvicorn main:app --reload
```

Then open http://localhost:8000.

## Running tests

Tests run against an in-memory-style SQLite DB — no Postgres/Redis required:

```bash
pip install -r requirements-dev.txt
pytest -v
```

## API endpoints

| Method | Path                     | Description                          |
|--------|--------------------------|---------------------------------------|
| GET    | `/health`                | Liveness + DB/cache status            |
| POST   | `/api/v1/signals`        | Record an HFT signal reading          |
| GET    | `/api/v1/signals`        | List recent readings (filterable)     |
| POST   | `/api/v1/backtests`      | Create a backtest run record          |
| GET    | `/api/v1/backtests`      | List backtest runs                    |
| GET    | `/api/v1/backtests/{id}` | Fetch one backtest run                |
| GET    | `/`                      | ReactPy dashboard UI                  |

Full interactive docs at `/docs` once the app is running.

## CI/CD

`.github/workflows/ci-cd.yml` runs on every push/PR to `main`:
1. **lint-and-test** — ruff lint + pytest against real Postgres/Redis service containers
2. **build-and-push** — builds the Docker image and pushes to `ghcr.io/<your-repo>` (main branch only)
3. **deploy** — placeholder stage; wire it to your target host once you have deployment credentials as GitHub secrets

## Database migrations (Alembic)

```bash
# generate a new migration after changing app/models.py
alembic revision --autogenerate -m "describe the change"

# apply migrations
alembic upgrade head
```
