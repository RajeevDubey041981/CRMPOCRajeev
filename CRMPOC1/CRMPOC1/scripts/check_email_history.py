"""Find last successful email and recent SMTP errors on production."""
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


def main() -> int:
    config = load_config()
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(config["INDCOOL_DEPLOY_HOST"], username=config["INDCOOL_DEPLOY_USER"], password=load_password(config), timeout=30)

    print("=== Last successful 'email sent' in API logs ===")
    print(ssh_run(
        c,
        "sudo journalctl -u indcool-api --since '14 days ago' --no-pager 2>/dev/null | "
        "grep 'email sent:' | tail -5",
    ).strip() or "(none found)")

    print("\n=== First SMTP auth failure in last 14 days ===")
    print(ssh_run(
        c,
        "sudo journalctl -u indcool-api --since '14 days ago' --no-pager 2>/dev/null | "
        "grep -m1 'SMTPAuthenticationError\\|WebLoginRequired' ",
    ).strip() or "(none found)")

    print("\n=== Recent email-related log lines (last 20) ===")
    print(ssh_run(
        c,
        "sudo journalctl -u indcool-api --since '5 days ago' --no-pager 2>/dev/null | "
        "grep -iE 'email sent:|email failed:|email skipped' | tail -20",
    ).strip() or "(none)")

    print("\n=== API service restarts (last 7 days) ===")
    print(ssh_run(
        c,
        "sudo journalctl -u indcool-api --since '7 days ago' --no-pager 2>/dev/null | "
        "grep -E 'Started indcool-api|Stopped indcool-api' | tail -10",
    ).strip() or "(none)")

    print("\n=== .env file last modified ===")
    print(ssh_run(c, "sudo stat -c '%y %n' /var/www/indcool/api/.env 2>/dev/null || sudo stat -f '%Sm %N' /var/www/indcool/api/.env").strip())

    print("\n=== Older journal: email sent before Sep 4 ===")
    print(ssh_run(
        c,
        "sudo journalctl -u indcool-api --since '2026-08-25' --until '2026-09-04 03:00:00' --no-pager 2>/dev/null | "
        "grep 'email sent:' | tail -5",
    ).strip() or "(none in journal)")

    print("\n=== API log files on disk ===")
    print(ssh_run(c, "sudo ls -la /var/www/indcool/api/*.log 2>/dev/null || echo '(no log files)'").strip())

    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
