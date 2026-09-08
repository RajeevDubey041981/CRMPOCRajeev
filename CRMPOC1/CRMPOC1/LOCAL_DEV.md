# Local testing without Docker Desktop

Docker Desktop on Windows is heavy (often 2–4 GB RAM + high CPU) because it runs a Linux VM even when your app only needs two small containers.

This project already supports **native local dev** — much lighter.

## Recommended setup (lowest resource use)

| Component | How to run | RAM (approx.) |
|-----------|------------|----------------|
| MySQL | Already installed on Windows | ~200–400 MB |
| API | `api\venv` + uvicorn | ~80–150 MB |
| UI | `npm run dev` (Vite) | ~150–300 MB |
| **Docker Desktop** | **Not needed** | **0 MB** |

**Total:** ~500–900 MB instead of 3–5 GB with Docker.

## Quick start

1. **Stop Docker Desktop** (right-click tray icon → Quit).
2. Ensure **MySQL** is running on Windows (port 3306, database `indcool`).
3. From repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\dev-local.ps1
```

4. Open http://localhost:5173  
   Login: `admin@indcool.com` / `admin123`

API docs: http://localhost:8010/docs

## Manual start (two terminals)

**Terminal 1 — API**

```powershell
cd api
.\venv\Scripts\activate
$env:MYSQL_DATABASE_URL = "mysql+mysqlconnector://root:YOUR_PASSWORD@127.0.0.1:3306/indcool"
python -m alembic upgrade head
python -m app.seed
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

**Terminal 2 — UI**

```powershell
cd ui
npm run dev
```

Ensure `ui\.env.local` contains:

```env
VITE_API_BASE_URL=http://localhost:8010
```

## When to use Docker

Use `docker compose up` only when you need to test:

- Linux-only container behavior
- Exact production image builds
- CI-like environment

For day-to-day UI/API changes, native dev is faster and uses far less CPU.

## Even lighter options

1. **UI only against production API** — run `npm run dev` locally and point `VITE_API_BASE_URL` at production (read-only testing; be careful with writes).
2. **Test on production** — https://indcoolapplainces.com after deploy (what you already do for verification).
3. **API only** — use http://localhost:8010/docs without starting the UI.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Can't connect to MySQL` | Start MySQL Windows service; use `127.0.0.1` not `host.docker.internal` in `.env` |
| Port 8010 in use | Change `API_PORT` in `.env` and `VITE_API_BASE_URL` in `ui\.env.local` |
| Port 5173 in use | `npm run dev -- --port 5174` |
