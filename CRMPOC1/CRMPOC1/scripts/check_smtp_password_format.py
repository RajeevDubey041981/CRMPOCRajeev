"""Check SMTP password format on production (length only, no secret printed)."""
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
    example = Path(__file__).resolve().parent / "deploy.env.example"
    for line in example.read_text(encoding="utf-8").splitlines():
        if line.startswith("INDCOOL_DEPLOY_PASSWORD="):
            return line.split("=", 1)[1].strip()
    return pwd


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
    py = r'''
from pathlib import Path
val = ""
for line in Path("/var/www/indcool/api/.env").read_text(encoding="utf-8").splitlines():
    if line.startswith("SMTP_PASSWORD="):
        val = line.split("=", 1)[1].strip()
        break
print("password_length:", len(val))
print("has_spaces:", " " in val)
print("looks_like_app_password:", len(val.replace(" ", "")) == 16)
'''
    ssh_run(client, f"cat > /tmp/pw_check.py <<'PY'\n{py}\nPY")
    print(ssh_run(client, "sudo -u www-data /var/www/indcool/api/venv/bin/python /tmp/pw_check.py"))
    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
