# UI and API Zip Deployment Steps

This package is prepared as two separate zip files:

- `release-packages/indcool-ui-package.zip`
- `release-packages/indcool-api-package.zip`

Use this when you are not sure about the target server OS and want to share the UI and API separately.

## What is inside each zip

### UI zip

The UI zip contains:

- production build files in `dist`
- `web.config` for IIS-style single-page app routing
- basic UI project metadata files

This zip is meant for static hosting or web-server deployment.

### API zip

The API zip contains:

- FastAPI app code
- Alembic migrations
- SQL scripts
- `requirements.txt`
- `.env.example`
- example service/proxy config files

This zip is meant for Python backend deployment on a server that can run a long-lived service.

## Files to share

Share these three items:

- `release-packages/indcool-ui-package.zip`
- `release-packages/indcool-api-package.zip`
- `ZIP_DEPLOY_STEPS.md`

## Deployment idea

### UI

Deploy the UI zip to the web server.

Typical options:

- IIS
- Nginx
- Apache
- static hosting panel

After extracting, use the `dist` folder as the website root.

### API

Deploy the API zip to a server that supports Python 3.

Typical steps after extract:

1. Create a Python virtual environment
2. Install `requirements.txt`
3. Copy `.env.example` to `.env`
4. Fill in database and JWT settings
5. Run:

```bash
alembic upgrade head
python -m app.seed
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Same-server deployment

If both UI and API go on the same server:

- host the UI from the extracted `dist` folder
- run the API on port `8000`
- configure the web server to proxy:
  - `/api/*` to the API
  - `/uploads/*` to the API
  - `/health` to the API

## Important note

The UI can be hosted on many simple hosting environments.

The API cannot run on basic static hosting alone. It needs:

- Python support
- package installation
- long-running process or service support

If the hosting provider does not allow that, host:

- UI on shared hosting
- API on VPS or another backend server

## Output location

The zip files are available in:

```text
release-packages
```
