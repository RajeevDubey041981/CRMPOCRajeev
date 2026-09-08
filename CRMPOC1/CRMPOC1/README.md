# Indcool CRM — Prototype

End-to-end CRM scaffold for a small AC / electrical-appliance manufacturer.
See the original spec for module-level details.

## Sprint 1 status (this delivery)

Done:
- Docker Compose stack: Postgres 15, FastAPI, Vite/React UI
- Full DB schema (10 modules, all tables + indexes) via a single Alembic migration
- JWT auth (login / logout / me / change-password)
- Users API (admin-only CRUD)
- Dashboard API (complaints summary, installation aging, 6-month chart)
- React UI shell: sidebar + topbar matching the spec navigation, login page, live dashboard wired to real endpoints, placeholder routes for every other module
- Seed script creating the admin user and sample item masters

Coming in later sprints:
- Sprint 2: Complaint CRUD + status workflow
- Sprint 3: Installation, Order, Serial-level tracking
- Sprint 4: Call, Vendor, Item, Courier modules
- Sprint 5: Claims + photo uploads + CSV export
- Sprint 6: Access codes, SMS notifications, perf indexes

## Stack
- UI — React 18 + Vite + Tailwind CSS + Recharts + Axios + React Router
- API — Python 3.12 + FastAPI + SQLAlchemy 2.0 + Alembic + python-jose + passlib/bcrypt
- DB — Postgres 15

## Run locally

1. Copy the env file and adjust if needed:
   ```sh
   cp .env.example .env
   ```
2. Bring the stack up:
   ```sh
   docker compose up --build
   ```
3. Open http://localhost:5173 and sign in:
   - email: `admin@indcool.com`
   - password: `admin123`

API docs available at http://localhost:8000/docs.

## Project layout
```
.
├── docker-compose.yml
├── .env.example
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/                  # migrations
│   └── app/
│       ├── main.py               # FastAPI app
│       ├── config.py             # settings (pydantic-settings)
│       ├── database.py           # SQLAlchemy engine + session
│       ├── security.py           # bcrypt + JWT
│       ├── deps.py               # auth + role dependencies
│       ├── seed.py               # admin + sample items
│       ├── models/               # ORM (all modules)
│       ├── schemas/              # pydantic
│       └── routers/              # auth, users, dashboard
└── ui/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── api/client.js         # axios + auth interceptor
        ├── auth/                 # AuthContext + ProtectedRoute
        ├── layout/               # Sidebar + Topbar + Layout
        ├── components/           # StatCard
        └── pages/                # Login, Dashboard, Placeholder
```

## Common dev tasks

- Run a fresh migration: `docker compose exec api alembic revision --autogenerate -m "msg"`
- Apply migrations: `docker compose exec api alembic upgrade head`
- Re-run seed: `docker compose exec api python -m app.seed`
- Open psql: `docker compose exec db psql -U indcool -d indcool_crm`
- Tail API logs: `docker compose logs -f api`

## Notes
- Tokens are stored in `localStorage` (prototype). For production, switch to httpOnly cookies.
- Uploads land in the `api_uploads` named volume; spec calls for swapping to S3 in prod.
- The seed admin password should be rotated via the `/api/auth/change-password` endpoint before any non-local use.
