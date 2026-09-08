import os
import paramiko
from pathlib import Path

HOST = "97.74.83.211"
USER = "indcooladmin"
PASSWORD = "JAdJh@yg4SFDP#!nGH"
ROOT = Path(__file__).resolve().parents[1]
LOCAL_UI = ROOT / "ui" / "dist"
REMOTE_UI = "/var/www/indcool/ui"


def run(client, cmd):
    _, stdout, stderr = client.exec_command(cmd, get_pty=True)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    if err.strip():
        out += "\nSTDERR: " + err
    return out


def upload_file(sftp, client, local: Path, remote: str):
    tmp = f"/tmp/indcool_ui_{local.name}"
    sftp.put(str(local), tmp)
    run(client, f"sudo cp {tmp} {remote} && sudo rm -f {tmp}")


def reset_admin_password(client):
    remote_py = r"""
import os
from pathlib import Path
from sqlalchemy import create_engine, text

for line in Path('/var/www/indcool/api/.env').read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if not line or line.startswith('#') or '=' not in line:
        continue
    k, v = line.split('=', 1)
    os.environ[k.strip()] = v.strip()

import sys
sys.path.insert(0, '/var/www/indcool/api')
from app.security import hash_password

new_password = 'admin123'
email = os.environ.get('SEED_ADMIN_EMAIL', 'admin@indcool.com')
engine = create_engine(os.environ['MYSQL_DATABASE_URL'])
with engine.begin() as conn:
    conn.execute(
        text('UPDATE users SET password_hash = :hash WHERE email = :email'),
        {'hash': hash_password(new_password), 'email': email},
    )
print(f'admin password reset to admin123 for {email}')
"""
    path = "/tmp/reset_admin_pw.py"
    sftp = client.open_sftp()
    with sftp.file(path, "w") as f:
        f.write(remote_py)
    sftp.close()
    print(run(client, f"sudo -u www-data env PYTHONPATH=/var/www/indcool/api /var/www/indcool/api/venv/bin/python {path}"))


def deploy_ui():
    if not LOCAL_UI.is_dir():
        raise SystemExit(f"Missing {LOCAL_UI}. Build UI first.")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    sftp = client.open_sftp()
    count = 0
    for root_dir, _, files in os.walk(LOCAL_UI):
        rel = Path(root_dir).relative_to(LOCAL_UI)
        remote_dir = REMOTE_UI if rel == Path(".") else f"{REMOTE_UI}/{rel.as_posix()}"
        run(client, f"sudo mkdir -p {remote_dir}")
        for name in files:
            upload_file(sftp, client, Path(root_dir) / name, f"{remote_dir}/{name}")
            run(client, f"sudo chown www-data:www-data {remote_dir}/{name}")
            count += 1
    sftp.close()
    print(f"Uploaded {count} UI files")
    print(run(client, "cat /var/www/indcool/ui/index.html"))
    print(run(client, "grep -o 'http://localhost:8010' /var/www/indcool/ui/assets/*.js | wc -l"))
    print(run(client, "sudo rm -f /var/www/indcool/ui/assets/index-DfsK9vcM.js"))
    reset_admin_password(client)
    client.close()


if __name__ == "__main__":
    deploy_ui()
