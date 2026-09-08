"""Run setup-e2e-service-flow.py on production and print JSON fixture to stdout."""
from __future__ import annotations

import sys
from pathlib import Path

import paramiko

HOST = "97.74.83.211"
USER = "indcooladmin"
PASSWORD = "JAdJh@yg4SFDP#!nGH"
ROOT = Path(__file__).resolve().parents[1]
LOCAL_SETUP = ROOT / "scripts" / "setup-e2e-service-flow.py"
REMOTE_SETUP = "/tmp/setup-e2e-service-flow.py"


def main() -> int:
    setup = LOCAL_SETUP.read_text(encoding="utf-8")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    sftp = client.open_sftp()
    with sftp.file(REMOTE_SETUP, "w") as f:
        f.write(setup)
    wrapper = f"""
import os, subprocess, sys
from pathlib import Path
for line in Path('/var/www/indcool/api/.env').read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if not line or line.startswith('#') or '=' not in line:
        continue
    k, v = line.split('=', 1)
    os.environ[k.strip()] = v.strip()
sys.exit(subprocess.call([sys.executable, '{REMOTE_SETUP}']))
"""
    wrapper_path = "/tmp/run_setup_e2e_prod.py"
    with sftp.file(wrapper_path, "w") as f:
        f.write(wrapper)
    sftp.close()

    cmd = (
        "sudo -u www-data env PYTHONPATH=/var/www/indcool/api "
        f"/var/www/indcool/api/venv/bin/python {wrapper_path}"
    )
    _, stdout, stderr = client.exec_command(cmd, get_pty=True)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    client.close()

    if err.strip():
        print(err, file=sys.stderr)
    start = out.find("{")
    if start < 0:
        print("Setup failed — no JSON returned", file=sys.stderr)
        print(out, file=sys.stderr)
        return 1
    json_text = out[start:].strip()
    fixture_path = ROOT / "scripts" / ".e2e-tmp" / "service-flow-fixture-prod.json"
    fixture_path.parent.mkdir(parents=True, exist_ok=True)
    fixture_path.write_text(json_text, encoding="utf-8")
    print(json_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
