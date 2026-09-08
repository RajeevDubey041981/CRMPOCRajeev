"""Run pending-actions backfill on production."""
import paramiko
from pathlib import Path

HOST = "97.74.83.211"
USER = "indcooladmin"
PASSWORD = "JAdJh@yg4SFDP#!nGH"
REMOTE_API = "/var/www/indcool/api"
ROOT = Path(__file__).resolve().parents[1]

local_file = ROOT / "api" / "app" / "services" / "pending_action_sync.py"
remote_file = f"{REMOTE_API}/app/services/pending_action_sync.py"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
sftp = client.open_sftp()
tmp = "/tmp/pending_action_sync.py"
sftp.put(str(local_file), tmp)
sftp.close()

def run(cmd: str) -> None:
    _, stdout, stderr = client.exec_command(cmd, get_pty=True)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    if out.strip():
        print(out)
    if err.strip():
        print(err)

run(f"sudo cp {tmp} {remote_file} && sudo chown www-data:www-data {remote_file}")
run(
    f"sudo -u www-data bash -lc 'cd {REMOTE_API} && "
    f"export $(grep -E ^DATABASE_BACKEND= .env | xargs) "
    f"$(grep -E ^MYSQL_DATABASE_URL= .env | xargs) && "
    f"venv/bin/python -m app.scripts.backfill_pending_actions'"
)
client.close()
