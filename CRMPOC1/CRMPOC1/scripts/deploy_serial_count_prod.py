import os
import paramiko

HOST = "97.74.83.211"
USER = "indcooladmin"
PASSWORD = "JAdJh@yg4SFDP#!nGH"
ROOT = r"c:\crmpoc\CRMPOC1\CRMPOC1"

API_FILES = [
    "app/models/item_master.py",
    "app/schemas/item_master.py",
    "app/routers/item_master.py",
    "app/schemas/order.py",
    "app/routers/orders.py",
    "alembic/versions/0020_item_master_serial_count.py",
]

UI_SRC = os.path.join(ROOT, "ui", "dist")
REMOTE_API = "/var/www/indcool/api"
REMOTE_UI = "/var/www/indcool/ui"


def run(client, cmd: str) -> str:
    _, stdout, stderr = client.exec_command(cmd, get_pty=True)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    if err.strip():
        out += "\nSTDERR: " + err
    return out


def upload_file(sftp, client, local: str, remote: str) -> None:
    tmp = f"/tmp/indcool_deploy_{os.path.basename(local)}"
    sftp.put(local, tmp)
    run(client, f"sudo cp {tmp} {remote} && sudo rm -f {tmp}")


client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
sftp = client.open_sftp()

print("=== Upload API files ===")
for rel in API_FILES:
    local = os.path.join(ROOT, "api", rel.replace("/", os.sep))
    remote = f"{REMOTE_API}/{rel.replace(chr(92), '/')}"
    print(f"  {rel}")
    upload_file(sftp, client, local, remote)

print("=== Upload UI dist ===")
for root_dir, dirs, files in os.walk(UI_SRC):
    rel = os.path.relpath(root_dir, UI_SRC)
    remote_dir = REMOTE_UI if rel == "." else f"{REMOTE_UI}/{rel.replace(chr(92), '/')}"
    run(client, f"sudo mkdir -p {remote_dir}")
    for name in files:
        local_path = os.path.join(root_dir, name)
        remote_path = f"{remote_dir}/{name}"
        upload_file(sftp, client, local_path, remote_path)
        run(client, f"sudo chown www-data:www-data {remote_path}")

sftp.close()

print("=== restart API ===")
print(run(client, "sudo systemctl restart indcool-api && sleep 2 && sudo systemctl is-active indcool-api"))

print("=== verify ===")
print(run(client, f"grep serial_count {REMOTE_API}/app/schemas/item_master.py | head -2"))
print(run(client, f"grep -l 'Serial numbers per unit' {REMOTE_UI}/assets/*.js"))
print(run(client, f"head -12 {REMOTE_UI}/index.html"))

client.close()
print("Deploy complete.")
