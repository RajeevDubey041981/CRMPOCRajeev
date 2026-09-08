"""Quick test Google SMTP relay from production (IP-allowlist relay)."""
from __future__ import annotations

import sys
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


REMOTE = r'''
import smtplib
from email.message import EmailMessage
from pathlib import Path
env = {}
for line in Path("/var/www/indcool/api/.env").read_text(encoding="utf-8").splitlines():
    line=line.strip()
    if line and not line.startswith("#") and "=" in line:
        k,v=line.split("=",1); env[k.strip()]=v.strip()
msg = EmailMessage()
msg["Subject"] = "SMTP relay test"
msg["From"] = env.get("SMTP_FROM") or env.get("SMTP_USER")
msg["To"] = env.get("SEED_ADMIN_EMAIL", "admin@indcool.com")
msg.set_content("relay test")
try:
    smtp = smtplib.SMTP("smtp-relay.gmail.com", 587, timeout=20)
    smtp.ehlo(); smtp.starttls(); smtp.ehlo()
    smtp.send_message(msg); smtp.quit(); print("smtp-relay-no-auth: OK")
except Exception as e:
    print("smtp-relay-no-auth: FAIL", type(e).__name__, str(e))
'''


def main() -> int:
    config = load_config()
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(config["INDCOOL_DEPLOY_HOST"], username=config["INDCOOL_DEPLOY_USER"], password=load_password(config), timeout=30)
    ssh_run(c, f"cat > /tmp/relay_test.py <<'PY'\n{REMOTE}\nPY")
    print(ssh_run(c, "sudo -u www-data /var/www/indcool/api/venv/bin/python /tmp/relay_test.py"))
    c.close()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
