# Same-Server Deployment Handoff

This application can be deployed on one server if the server is a VPS or dedicated Linux machine.

It should not be deployed on basic shared hosting that does not allow long-running backend services.

## App structure

- Frontend: React/Vite UI
- Backend: FastAPI Python API
- Database: external MySQL or SQL Server

## Recommended deployment model

Deploy both app parts on the same server using Docker:

- `ui` container
  - serves the built frontend with Nginx
  - listens on port `80`
- `api` container
  - runs FastAPI with Uvicorn
  - listens internally on port `8000`
- `ui` container proxies:
  - `/api/*` -> `api:8000`
  - `/uploads/*` -> `api:8000`
  - `/health` -> `api:8000/health`

Users access the application from one URL:

- `http://YOUR_SERVER_IP/`

## Files included for deployment

- `docker-compose.prod.yml`
- `ui/Dockerfile.prod`
- `ui/nginx.conf`
- `.env.production.example`
- `DEPLOYMENT.md`

## Required server capability

The server must support:

- Docker
- Docker Compose plugin
- outbound access to the database server
- port `80` open

## Deployment steps

### 1. Copy environment file

```sh
cp .env.production.example .env.production
```

### 2. Update `.env.production`

Set these values:

```env
DATABASE_BACKEND=mysql
MYSQL_DATABASE_URL=mysql+mysqlconnector://root:your_password@YOUR_DB_HOST:3306/indcool
JWT_SECRET=replace-with-a-long-random-secret
CORS_ORIGINS=http://YOUR_SERVER_IP
SEED_ADMIN_PASSWORD=change-this-password
VITE_API_BASE_URL=
UI_PORT=80
```

If using SQL Server instead of MySQL:

```env
DATABASE_BACKEND=sqlserver
SQLSERVER_DATABASE_URL=Server=YOUR_DB_HOST,1433;Database=indcool;User Id=api_user;Password=your_password;Encrypt=no;TrustServerCertificate=yes;Driver=ODBC Driver 18 for SQL Server;
```

### 3. Build and start

```sh
docker compose --env-file .env.production -f docker-compose.prod.yml build
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

### 4. Verify

```sh
docker compose --env-file .env.production -f docker-compose.prod.yml ps
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f api
```

Check:

- App: `http://YOUR_SERVER_IP/`
- Health: `http://YOUR_SERVER_IP/health`

## Important note

If the hosting plan is GoDaddy shared hosting or normal cPanel hosting, this full-stack deployment will usually not work.

For same-server deployment, use:

- GoDaddy VPS
- GoDaddy dedicated server
- any Linux VPS from another provider

