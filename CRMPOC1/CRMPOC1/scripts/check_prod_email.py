"""Check production email configuration and test SMTP (secrets masked in output)."""
from __future__ import annotations

import sys
from pathlib import Path

import paramiko

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deploy import load_config, ssh_run  # noqa: E402

EMAIL_KEYS = (
    "EMAIL_ENABLED",
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "SMTP_FROM",
    "SMTP_FROM_NAME",
    "SMTP_USE_TLS",
    "SMTP_USE_AUTH",
    "APP_PUBLIC_URL",
)

ENV_PATH = "/var/www/indcool/api/.env"


def load_password(config: dict) -> str:
    pwd = config.get("INDCOOL_DEPLOY_PASSWORD", "")
    if pwd and pwd != "YOUR_PASSWORD_HERE":
        return pwd
    example = Path(__file__).resolve().parent / "deploy.env.example"
    if example.is_file():
        for line in example.read_text(encoding="utf-8").splitlines():
            if line.startswith("INDCOOL_DEPLOY_PASSWORD="):
                return line.split("=", 1)[1].strip()
    return pwd


def mask_env_line(line: str) -> str:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in line:
        return line.rstrip()
    key, val = line.split("=", 1)
    key = key.strip()
    if key == "SMTP_PASSWORD" and val.strip():
        return f"{key}=(set, len={len(val.strip())})"
    if key in {"JWT_SECRET", "MYSQL_DATABASE_URL", "SQLSERVER_DATABASE_URL"} and val.strip():
        return f"{key}=(set)"
    return f"{key}={val.strip()}"


def main() -> int:
    config = load_config()
    password = load_password(config)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(config["INDCOOL_DEPLOY_HOST"], username=config["INDCOOL_DEPLOY_USER"], password=password, timeout=30)

    print("=== Email-related .env (masked) ===")
    raw = ssh_run(client, f"sudo grep -E '^(EMAIL_|SMTP_|APP_PUBLIC_URL)=' {ENV_PATH} 2>/dev/null || true")
    for line in raw.splitlines():
        if line.strip():
            print(mask_env_line(line))

    print("\n=== Recent API email log lines ===")
    logs = ssh_run(
        client,
        "sudo journalctl -u indcool-api --since '7 days ago' --no-pager 2>/dev/null | "
        "grep -iE 'email|smtp' | tail -30",
    )
    print(logs.strip() or "(no email lines in last 7 days)")

    print("\n=== SMTP test from server ===")
    test_py = r'''
import os
from pathlib import Path
for line in Path("/var/www/indcool/api/.env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ[k.strip()] = v.strip()
import sys
sys.path.insert(0, "/var/www/indcool/api")
from app.config import settings
from app.services.email_service import send_email
print("email_enabled:", settings.email_enabled)
print("smtp_host:", settings.smtp_host)
print("smtp_port:", settings.smtp_port)
print("smtp_user:", settings.smtp_user or "(empty)")
print("smtp_from:", settings.smtp_from or settings.smtp_user or "(empty)")
print("smtp_use_tls:", settings.smtp_use_tls)
print("smtp_use_auth:", settings.smtp_use_auth)
print("smtp_password_set:", bool((settings.smtp_password or "").strip()))
try:
    ok = send_email(
        to=settings.seed_admin_email,
        subject="INDcool production email diagnostic",
        html_body="<p>Diagnostic test from check_prod_email.py</p>",
        text_body="Diagnostic test from check_prod_email.py",
    )
    print("send_result:", ok)
except Exception as e:
    print("send_error:", type(e).__name__, str(e))
'''
    ssh_run(client, f"cat > /tmp/indcool_email_diag.py <<'PY'\n{test_py}\nPY")
    print(ssh_run(client, "sudo -u www-data /var/www/indcool/api/venv/bin/python /tmp/indcool_email_diag.py"))

    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
