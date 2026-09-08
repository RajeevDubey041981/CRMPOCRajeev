# Full Deployment Steps

This guide covers how to deploy:

- `UI`
- `API`
- `Database`

for this project on a server.

It is written to be practical even if the final server OS is not fully confirmed yet.

## Deployment overview

The app has three parts:

1. `Database`
2. `API` backend
3. `UI` frontend

Recommended order:

1. Create database
2. Create tables
3. Load sample data if needed
4. Deploy API
5. Deploy UI
6. Connect UI to API
7. Test login and main screens

## Files already prepared

### SQL

- [create_tables_mysql_current.sql](C:/crmpoc/CRMPOC1/CRMPOC1/api/sql/create_tables_mysql_current.sql:1)
- [create_tables_sqlserver_current.sql](C:/crmpoc/CRMPOC1/CRMPOC1/api/sql/create_tables_sqlserver_current.sql:1)
- [sample_data_mysql_current.sql](C:/crmpoc/CRMPOC1/CRMPOC1/api/sql/sample_data_mysql_current.sql:1)

### Deployment packages

- [indcool-ui-package.zip](C:/crmpoc/CRMPOC1/CRMPOC1/release-packages/indcool-ui-package.zip)
- [indcool-api-package.zip](C:/crmpoc/CRMPOC1/CRMPOC1/release-packages/indcool-api-package.zip)

### Deployment references

- [ZIP_DEPLOY_STEPS.md](C:/crmpoc/CRMPOC1/CRMPOC1/ZIP_DEPLOY_STEPS.md:1)
- [NON_DOCKER_DEPLOYMENT.md](C:/crmpoc/CRMPOC1/CRMPOC1/NON_DOCKER_DEPLOYMENT.md:1)
- [CLICK_DEPLOY_STEPS.md](C:/crmpoc/CRMPOC1/CRMPOC1/CLICK_DEPLOY_STEPS.md:1)

## Part 1: Database setup

## Step 1. Choose database type

This app supports:

- `MySQL`
- `SQL Server`

Use:

- MySQL script: [create_tables_mysql_current.sql](C:/crmpoc/CRMPOC1/CRMPOC1/api/sql/create_tables_mysql_current.sql:1)
- SQL Server script: [create_tables_sqlserver_current.sql](C:/crmpoc/CRMPOC1/CRMPOC1/api/sql/create_tables_sqlserver_current.sql:1)

## Step 2. Create the database

Example MySQL:

```sql
CREATE DATABASE indcool;
```

Example SQL Server:

```sql
CREATE DATABASE indcool;
```

## Step 3. Run the table creation script

For MySQL:

```sql
SOURCE create_tables_mysql_current.sql;
```

For SQL Server:

Run:

```sql
:r create_tables_sqlserver_current.sql
```

or open the file in SSMS and execute it.

## Step 4. Load sample data

If you want test data immediately, run:

- [sample_data_mysql_current.sql](C:/crmpoc/CRMPOC1/CRMPOC1/api/sql/sample_data_mysql_current.sql:1)

This script currently exists for MySQL.

Sample login users created by that script:

- `admin@indcool.com / admin123`
- `ravi@indcool.com / engineer123`
- `vendor1@indcool.com / vendor123`
- `callcenter@indcool.com / call123`
- `sales@indcool.com / sales123`

## Part 2: API deployment

## Step 5. Extract the API package

Use:

- [indcool-api-package.zip](C:/crmpoc/CRMPOC1/CRMPOC1/release-packages/indcool-api-package.zip)

Extract it on the server.

Suggested folder:

```text
/var/www/indcool/api
```

or on Windows:

```text
C:\indcool\api
```

## Step 6. Install Python

Install:

- Python 3.11 or later

Also install:

- `pip`
- virtual environment support

If using SQL Server, also install:

- Microsoft ODBC Driver 18 for SQL Server

## Step 7. Create virtual environment

Linux:

```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

Windows:

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Step 8. Create API environment file

Copy:

```text
.env.example
```

to:

```text
.env
```

Then update values.

Example for MySQL:

```env
DATABASE_BACKEND=mysql
MYSQL_DATABASE_URL=mysql+mysqlconnector://root:your_password@YOUR_DB_HOST:3306/indcool
JWT_SECRET=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480
UPLOAD_DIR=/var/www/indcool/uploads
CORS_ORIGINS=http://YOUR_SERVER_OR_DOMAIN
SEED_ADMIN_EMAIL=admin@indcool.com
SEED_ADMIN_PASSWORD=admin123
SEED_ADMIN_NAME=Administrator
```

Example for SQL Server:

```env
DATABASE_BACKEND=sqlserver
SQLSERVER_DATABASE_URL=Server=YOUR_DB_HOST,1433;Database=indcool;User Id=api_user;Password=your_password;Encrypt=no;TrustServerCertificate=yes;Driver=ODBC Driver 18 for SQL Server;
JWT_SECRET=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480
UPLOAD_DIR=/var/www/indcool/uploads
CORS_ORIGINS=http://YOUR_SERVER_OR_DOMAIN
SEED_ADMIN_EMAIL=admin@indcool.com
SEED_ADMIN_PASSWORD=admin123
SEED_ADMIN_NAME=Administrator
```

## Step 9. Create upload folder

Example Linux:

```bash
mkdir -p /var/www/indcool/uploads
```

Example Windows:

```bat
mkdir C:\indcool\uploads
```

Make sure the API process can write to that folder.

## Step 10. Run API

Linux:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Windows:

```bat
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Step 11. Test API

Open:

```text
http://YOUR_SERVER_IP:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Part 3: UI deployment

## Step 12. Extract the UI package

Use:

- [indcool-ui-package.zip](C:/crmpoc/CRMPOC1/CRMPOC1/release-packages/indcool-ui-package.zip)

Extract it on the server.

The deployable UI files are inside:

```text
dist
```

## Step 13. Host the UI files

Use the extracted `dist` folder as the website root.

Possible web servers:

- IIS
- Nginx
- Apache
- hosting control panel static site

If using IIS, the included `web.config` helps route React URLs correctly.

## Part 4: Connect UI and API

## Step 14. Put UI and API on the same domain if possible

Best setup:

- UI at `http://yourdomain.com/`
- API proxied through the same domain at `http://yourdomain.com/api/...`

This is simpler than exposing API separately.

## Step 15. Configure reverse proxy

Your web server should proxy:

- `/api/*` -> API server on port `8000`
- `/uploads/*` -> API server on port `8000`
- `/health` -> API server on port `8000/health`

Examples:

- IIS: URL Rewrite + ARR
- Nginx: `proxy_pass`
- Apache: `ProxyPass`

## Step 16. Set CORS correctly

In the API `.env`, set:

```env
CORS_ORIGINS=http://YOUR_SERVER_OR_DOMAIN
```

If using HTTPS:

```env
CORS_ORIGINS=https://YOUR_SERVER_OR_DOMAIN
```

## Part 5: Final testing

## Step 17. Open the website

Open:

```text
http://YOUR_SERVER_OR_DOMAIN/
```

## Step 18. Test login

If sample MySQL data was loaded, try:

```text
admin@indcool.com / admin123
```

## Step 19. Test major screens

Check:

- dashboard
- order list
- installation requests
- complaints
- serial history
- claims

## Step 20. Test uploads and API calls

Verify:

- login works
- API requests succeed
- uploaded files open correctly from `/uploads/...`

## If the target hosting is simple shared hosting

Important:

- UI can often be hosted on shared hosting
- API usually cannot run on basic shared hosting

If the provider only supports static files:

1. Deploy the UI there
2. Deploy the API on VPS or another backend server
3. Point the UI to that API server

## Recommended practical deployment options

### Option A

- UI on shared hosting
- API on VPS
- Database on MySQL or SQL Server

### Option B

- UI + API together on one VPS
- Database on same server or external DB server

## Best current files for handoff

If you need to share the deployment package with another person, send:

- [indcool-ui-package.zip](C:/crmpoc/CRMPOC1/CRMPOC1/release-packages/indcool-ui-package.zip)
- [indcool-api-package.zip](C:/crmpoc/CRMPOC1/CRMPOC1/release-packages/indcool-api-package.zip)
- [FULL_DEPLOYMENT_STEPS.md](C:/crmpoc/CRMPOC1/CRMPOC1/FULL_DEPLOYMENT_STEPS.md:1)
- plus the SQL scripts from [api/sql](C:/crmpoc/CRMPOC1/CRMPOC1/api/sql)

