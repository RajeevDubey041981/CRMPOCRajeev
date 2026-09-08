# Non-Docker Deployment

This app can be deployed on one Linux VPS server without Docker.

Use:

- `nginx` for the frontend and reverse proxy
- `uvicorn` + `systemd` for the FastAPI backend
- your existing MySQL or SQL Server database

## Files to share

- `deploy/nginx-indcool.conf`
- `deploy/indcool-api.service`
- `NON_DOCKER_DEPLOYMENT.md`

## Server type

This needs a server where you can install packages and run services:

- GoDaddy VPS: supported
- Dedicated Linux server: supported
- Shared hosting/cPanel only: usually not supported for this backend

## Deployment layout

- UI build files: `/var/www/indcool/ui`
- API code: `/var/www/indcool/api`
- Python virtualenv: `/var/www/indcool/api/venv`
- API env file: `/var/www/indcool/api/.env`
- Upload folder: `/var/www/indcool/uploads`

## 1. Install packages

Ubuntu/Debian example:

```bash
sudo apt update
sudo apt install -y nginx python3 python3-venv python3-pip build-essential
```

If using SQL Server, also install Microsoft ODBC Driver 18.

## 2. Upload project

Copy project files to:

```bash
/var/www/indcool
```

Expected structure:

```text
/var/www/indcool/api
/var/www/indcool/ui
```

## 3. Build the UI

```bash
cd /var/www/indcool/ui
npm install
npm run build
sudo mkdir -p /var/www/indcool/ui-live
sudo cp -r dist/* /var/www/indcool/ui-live/
```

Note:

- If you want to use the nginx config exactly as provided, copy the built files into `/var/www/indcool/ui`
- Or change the `root` line in `deploy/nginx-indcool.conf`

Recommended final location:

```bash
sudo rm -rf /var/www/indcool/ui
sudo mkdir -p /var/www/indcool/ui
sudo cp -r dist/* /var/www/indcool/ui/
```

## 4. Prepare backend virtual environment

```bash
cd /var/www/indcool/api
python3 -m venv venv
. venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Create backend `.env`

Create:

```bash
/var/www/indcool/api/.env
```

Example for MySQL:

```env
DATABASE_BACKEND=mysql
MYSQL_DATABASE_URL=mysql+mysqlconnector://root:your_password@YOUR_DB_HOST:3306/indcool
JWT_SECRET=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480
UPLOAD_DIR=/var/www/indcool/uploads
CORS_ORIGINS=http://YOUR_SERVER_IP
SEED_ADMIN_EMAIL=admin@indcool.com
SEED_ADMIN_PASSWORD=change-this-password
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
CORS_ORIGINS=http://YOUR_SERVER_IP
SEED_ADMIN_EMAIL=admin@indcool.com
SEED_ADMIN_PASSWORD=change-this-password
SEED_ADMIN_NAME=Administrator
```

## 6. Create uploads folder

```bash
sudo mkdir -p /var/www/indcool/uploads
sudo chown -R www-data:www-data /var/www/indcool/uploads
sudo chown -R www-data:www-data /var/www/indcool/api
```

## 7. Run migrations and seed

```bash
cd /var/www/indcool/api
. venv/bin/activate
alembic upgrade head
python -m app.seed
```

## 8. Install systemd service

Copy the service file:

```bash
sudo cp deploy/indcool-api.service /etc/systemd/system/indcool-api.service
sudo systemctl daemon-reload
sudo systemctl enable indcool-api
sudo systemctl start indcool-api
```

Check status:

```bash
sudo systemctl status indcool-api
journalctl -u indcool-api -f
```

## 9. Install nginx config

```bash
sudo cp deploy/nginx-indcool.conf /etc/nginx/sites-available/indcool
sudo ln -s /etc/nginx/sites-available/indcool /etc/nginx/sites-enabled/indcool
sudo nginx -t
sudo systemctl restart nginx
```

## 10. Open the app

- App: `http://YOUR_SERVER_IP/`
- Health: `http://YOUR_SERVER_IP/health`

## Notes

- The frontend calls the API on the same host, so no special frontend production env is required.
- If using a domain, replace `CORS_ORIGINS=http://YOUR_SERVER_IP` with that domain.
- For HTTPS, add Certbot or another TLS setup on top of nginx.
