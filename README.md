# Snob Group Platform

A full-stack e-commerce and learning management platform for The Snob Group.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              NGINX (Reverse Proxy)                        │
│                         /api → Backend  |  / → Frontend                    │
└─────────────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Frontend   │    │   Backend    │    │    Admin     │
│  (Next.js)   │    │  (FastAPI)   │    │  (Next.js)   │
│   Port 3000  │    │   Port 8000  │    │   Port 3000  │
└──────────────┘    └──────┬───────┘    └──────────────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │    Redis     │  │  Meilisearch │
│   (db)       │  │  (cache/     │  │  (search)    │
│              │  │   Celery)    │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
                          │
                          ▼
                  ┌──────────────┐
                  │Celery Worker │
                  │ (async tasks)│
                  └──────────────┘
```

## Quick Start

```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head
```

- **Frontend**: http://localhost:3000
- **Admin**: http://localhost:3001
- **API**: http://localhost:8000/api/v1
- **API Docs**: http://localhost:8000/api/docs

## Development Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt -r tests/requirements.txt
# Set DATABASE_URL, REDIS_URL, SECRET_KEY in .env
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend / Admin

```bash
cd frontend  # or admin
npm install
npm run dev
```

### Running Tests

```bash
cd backend
# Ensure PostgreSQL is running (e.g. docker-compose up db -d)
DATABASE_URL=postgresql+asyncpg://snobgroup:snobgroup@localhost:5432/snobgroup pytest tests/ -v
```

## Project Structure

```
sg_platform/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # API routes (auth, products, orders, courses, etc.)
│   │   ├── core/            # Config, database, security
│   │   ├── middleware/       # Auth, rate limit, security headers
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── tasks/           # Celery tasks
│   ├── tests/               # Pytest tests
│   └── scripts/             # Migration scripts
├── frontend/                # Customer-facing Next.js app
├── admin/                   # Admin dashboard Next.js app
├── nginx/                   # Production nginx config
├── docs/                    # Documentation
│   └── deployment.md       # Deployment guide
└── docker-compose.yml       # Development
    docker-compose.prod.yml  # Production
```

## API Documentation

Interactive API docs are available at **/api/docs** (Swagger UI) when the backend is running.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy 2 (async), Alembic, Celery, Redis
- **Frontend**: Next.js 15, React 19, Tailwind CSS
- **Database**: PostgreSQL 16
- **Search**: Meilisearch
- **Payments**: Stripe
- **SMS**: Twilio
- **Email**: SendGrid
- **Storage**: S3-compatible (Cloudflare R2, AWS S3)

## Contributing

1. Create a feature branch from `develop`
2. Make changes and add tests
3. Ensure `pytest backend/tests/` and `ruff check backend/` pass
4. Open a pull request to `main` or `develop`

## License

Proprietary - The Snob Group
