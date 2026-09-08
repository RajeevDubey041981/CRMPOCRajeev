"""Enable Gmail SMTP email on production API server."""
from __future__ import annotations

import os
import paramiko

HOST = os.environ.get("INDCOOL_DEPLOY_HOST", "97.74.83.211")
USER = os.environ.get("INDCOOL_DEPLOY_USER", "indcooladmin")
PASSWORD = os.environ.get("INDCOOL_DEPLOY_PASSWORD", "JAdJh@yg4SFDP#!nGH")
ENV_PATH = "/var/www/indcool/api/.env"

EMAIL_VARS = {
    "EMAIL_ENABLED": "true",
    "SMTP_HOST": "smtp.gmail.com",
    "SMTP_PORT": "587",
    "SMTP_USER": "support@indcool.in",
    "SMTP_PASSWORD": "pboc ylmq tkho slpt",
    "SMTP_FROM": "info@indcool.in",
    "SMTP_FROM_NAME": "Indcool Service",
    "SMTP_USE_TLS": "true",
    "SMTP_USE_AUTH": "true",
    "APP_PUBLIC_URL": "https://indcoolapplainces.com",
}


def run(client: paramiko.SSHClient, cmd: str) -> str:
    _, stdout, stderr = client.exec_command(cmd, get_pty=True)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    return out + (("\n" + err) if err.strip() else "")


def merge_env(text: str, updates: dict[str, str]) -> str:
    lines = text.splitlines()
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            out.append(line)
            continue
        key = line.split("=", 1)[0].strip()
        if key in updates:
            out.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            out.append(line)
    for key, value in updates.items():
        if key not in seen:
            out.append(f"{key}={value}")
    return "\n".join(out) + "\n"


def main() -> int:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {HOST}...")
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    try:
        print("=== Read current .env ===")
        current = run(client, f"sudo cat {ENV_PATH}")

        merged = merge_env(current, EMAIL_VARS)
        tmp = "/tmp/indcool_api_env"
        sftp = client.open_sftp()
        try:
            with sftp.open(tmp, "w") as fh:
                fh.write(merged)
        finally:
            sftp.close()
        print(run(client, f"sudo cp {tmp} {ENV_PATH} && sudo chown www-data:www-data {ENV_PATH} && rm -f {tmp}"))

        print("=== Restart API ===")
        print(run(client, "sudo systemctl restart indcool-api && sleep 2 && sudo systemctl is-active indcool-api"))

        print("=== Verify settings (masked) ===")
        for key in EMAIL_VARS:
            if key == "SMTP_PASSWORD":
                print(f"{key}=(set)")
            else:
                print(f"{key}={EMAIL_VARS[key]}")

        print("=== Test SMTP from server ===")
        test_py = r'''
import os
from pathlib import Path
for line in Path("/var/www/indcool/api/.env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ[k.strip()] = v.strip()
os.environ.setdefault("DATABASE_BACKEND", "mysql")
import sys
sys.path.insert(0, "/var/www/indcool/api")
from app.config import settings
from app.services.email_service import send_email
print("email_enabled:", settings.email_enabled)
print("smtp_host:", settings.smtp_host)
print("smtp_from:", settings.smtp_from or settings.smtp_user)
ok = send_email(
    to=settings.seed_admin_email,
    subject="INDcool production email test",
    html_body="<p>Production Gmail SMTP is working.</p>",
    text_body="Production Gmail SMTP is working.",
)
print("send_result:", ok)
'''
        run(client, f"cat > /tmp/indcool_email_test.py <<'PY'\n{test_py}\nPY")
        print(run(client, "sudo -u www-data /var/www/indcool/api/venv/bin/python /tmp/indcool_email_test.py"))
    finally:
        client.close()
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
