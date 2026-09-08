"""Try common SMTP hosts for indcool.in from production (diagnostic only)."""
from __future__ import annotations

import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path

import paramiko

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deploy import load_config, ssh_run  # noqa: E402


def load_password(config: dict) -> str:
    pwd = config.get("INDCOOL_DEPLOY_PASSWORD", "")
    if pwd and pwd != "YOUR_PASSWORD_HERE":
        return pwd
    for line in Path(__file__).resolve().parent.joinpath("deploy.env.example").read_text(encoding="utf-8").splitlines():
        if line.startswith("INDCOOL_DEPLOY_PASSWORD="):
            return line.split("=", 1)[1].strip()
    return pwd


REMOTE_TEST = r'''
import os, smtplib
from email.message import EmailMessage
from pathlib import Path

env = {}
for line in Path("/var/www/indcool/api/.env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    env[k.strip()] = v.strip()

user = env.get("SMTP_USER", "")
password = env.get("SMTP_PASSWORD", "")
to = env.get("SEED_ADMIN_EMAIL", "admin@indcool.com")

candidates = [
    ("gmail-587-tls", "smtp.gmail.com", 587, "starttls"),
    ("gmail-465-ssl", "smtp.gmail.com", 465, "ssl"),
    ("secureserver-587", "smtpout.secureserver.net", 587, "starttls"),
    ("secureserver-465", "smtpout.secureserver.net", 465, "ssl"),
    ("secureserver-80", "relay-hosting.secureserver.net", 25, "plain"),
]

def try_send(label, host, port, mode):
    msg = EmailMessage()
    msg["Subject"] = f"SMTP diag {label}"
    msg["From"] = user
    msg["To"] = to
    msg.set_content("diagnostic")
    try:
        if mode == "ssl":
            smtp = smtplib.SMTP_SSL(host, port, timeout=20)
        else:
            smtp = smtplib.SMTP(host, port, timeout=20)
            smtp.ehlo()
            if mode == "starttls":
                smtp.starttls()
                smtp.ehlo()
        if user and password:
            smtp.login(user, password)
        smtp.send_message(msg)
        smtp.quit()
        return "OK"
    except Exception as e:
        return f"FAIL: {type(e).__name__}: {e}"

for label, host, port, mode in candidates:
    print(f"{label} ({host}:{port}) -> {try_send(label, host, port, mode)}")
'''


def main() -> int:
    config = load_config()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        config["INDCOOL_DEPLOY_HOST"],
        username=config["INDCOOL_DEPLOY_USER"],
        password=load_password(config),
        timeout=30,
    )
    ssh_run(client, f"cat > /tmp/smtp_diag.py <<'PY'\n{REMOTE_TEST}\nPY")
    print(ssh_run(client, "sudo -u www-data /var/www/indcool/api/venv/bin/python /tmp/smtp_diag.py"))
    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
