"""Upload rebuilt UI dist to production."""
import os
from pathlib import Path

import paramiko

HOST = "97.74.83.211"
USER = "indcooladmin"
PASSWORD = "JAdJh@yg4SFDP#!nGH"
REMOTE_UI = "/var/www/indcool/ui"
UI_DIST = Path(__file__).resolve().parents[1] / "ui" / "dist"


def ssh_run(client, cmd: str) -> str:
    _, stdout, stderr = client.exec_command(cmd, get_pty=True)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    if err.strip():
        out += "\nSTDERR: " + err
    return out


def upload_file(sftp, client, local: Path, remote: str) -> None:
    tmp = f"/tmp/indcool_ui_{local.name}"
    sftp.put(str(local), tmp)
    ssh_run(client, f"sudo mkdir -p $(dirname {remote}) && sudo cp {tmp} {remote} && sudo rm -f {tmp}")


def main() -> None:
    if not UI_DIST.is_dir():
        raise SystemExit(f"Missing UI build: {UI_DIST}")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    sftp = client.open_sftp()
    count = 0
    try:
        for root_dir, _dirs, files in os.walk(UI_DIST):
            rel = Path(root_dir).relative_to(UI_DIST)
            remote_dir = REMOTE_UI if rel == Path(".") else f"{REMOTE_UI}/{rel.as_posix()}"
            ssh_run(client, f"sudo mkdir -p {remote_dir}")
            for name in files:
                local_path = Path(root_dir) / name
                remote_path = f"{remote_dir}/{name}"
                upload_file(sftp, client, local_path, remote_path)
                ssh_run(client, f"sudo chown www-data:www-data {remote_path}")
                count += 1
    finally:
        sftp.close()
        client.close()
    print(f"Uploaded {count} UI files to {REMOTE_UI}")


if __name__ == "__main__":
    main()
