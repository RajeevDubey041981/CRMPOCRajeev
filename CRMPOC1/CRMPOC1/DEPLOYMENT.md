# Production Deployment

This project can be deployed on one server with two containers:

- `ui`: Nginx serving the built React app
- `api`: FastAPI serving `/api/*`, `/uploads/*`, and `/health`

The UI container proxies API traffic to the API container, so users access everything from one host and one port.

## What was added

- `docker-compose.prod.yml`: production stack
- `ui/Dockerfile.prod`: builds the React app and serves it with Nginx
- `ui/nginx.conf`: SPA routing plus reverse proxy for API and uploads
- `.env.production.example`: production environment template

## Server requirements

- Ubuntu 22.04+ or another Linux server
- Docker and Docker Compose plugin installed
- Port `80` open on the server
- Access from the server to your database host

## Files to prepare

1. Copy the production env file:

```sh
cp .env.production.example .env.production
```

2. Edit `.env.production` and set:

- `DATABASE_BACKEND` to `mysql` or `sqlserver`
- the matching database URL
- `JWT_SECRET`
- `CORS_ORIGINS`
- `SEED_ADMIN_PASSWORD`

If you deploy behind a domain like `http://crm.example.com`, set:

```env
CORS_ORIGINS=http://crm.example.com
```

If you use HTTPS later, change that to:

```env
CORS_ORIGINS=https://crm.example.com
```

## Deploy on one server

Run these commands on the server from the project root:

```sh
docker compose --env-file .env.production -f docker-compose.prod.yml build
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

Then verify:

```sh
docker compose --env-file .env.production -f docker-compose.prod.yml ps
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f api
```

Open:

- `http://YOUR_SERVER_IP/`

Health check:

- `http://YOUR_SERVER_IP/health`

API docs:

- `http://YOUR_SERVER_IP/docs` will not work through nginx
- use `http://YOUR_SERVER_IP/api/...` for app traffic
- if you need docs publicly, expose the API container separately or add another nginx route

## Optional: expose FastAPI docs through nginx

If you want `/docs` and `/openapi.json` from the same host, add these blocks to `ui/nginx.conf`:

```nginx
location /docs {
  proxy_pass http://api:8000/docs;
}

location /openapi.json {
  proxy_pass http://api:8000/openapi.json;
}
```

Then rebuild and restart the UI container.

## Updating after code changes

```sh
docker compose --env-file .env.production -f docker-compose.prod.yml build
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

## Uploads

Uploaded files are stored in the Docker volume `api_uploads`.

To inspect volumes:

```sh
docker volume ls
```

## Notes

- The current production stack assumes your database is outside this compose stack.
- The API container runs `alembic upgrade head` during startup.
- The seed step runs on startup too; it is safe for keeping the admin bootstrap path available, but you may later want to remove it after first deployment.
- For real production use, put this behind HTTPS using Nginx on the host, Cloudflare, or a load balancer.
