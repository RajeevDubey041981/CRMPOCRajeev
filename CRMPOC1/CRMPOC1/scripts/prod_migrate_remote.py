import os
import subprocess
from pathlib import Path

env_path = Path("/var/www/indcool/api/.env")
for line in env_path.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    os.environ[key.strip()] = value.strip()

os.chdir("/var/www/indcool/api")
alembic = "/var/www/indcool/api/venv/bin/alembic"
python = "/var/www/indcool/api/venv/bin/python"

print("MYSQL snippet:", os.environ.get("MYSQL_DATABASE_URL", "")[:70])
subprocess.run([alembic, "-c", "alembic.ini", "current"], check=False)
subprocess.run([alembic, "-c", "alembic.ini", "upgrade", "head"], check=True)
subprocess.run([python, "-m", "app.seed"], check=False)
print("done")
