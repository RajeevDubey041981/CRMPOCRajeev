"""Verify production deployment health and key feature markers."""
from __future__ import annotations

import sys
from pathlib import Path

import paramiko

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deploy import load_config, ssh_run  # noqa: E402


def main() -> int:
    config = load_config()
    if not config.get("INDCOOL_DEPLOY_PASSWORD") or config["INDCOOL_DEPLOY_PASSWORD"] == "YOUR_PASSWORD_HERE":
        example = Path(__file__).resolve().parent / "deploy.env.example"
        if example.is_file():
            for line in example.read_text(encoding="utf-8").splitlines():
                if line.startswith("INDCOOL_DEPLOY_PASSWORD="):
                    config["INDCOOL_DEPLOY_PASSWORD"] = line.split("=", 1)[1].strip()

    remote_api = config["REMOTE_API"]
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        config["INDCOOL_DEPLOY_HOST"],
        username=config["INDCOOL_DEPLOY_USER"],
        password=config["INDCOOL_DEPLOY_PASSWORD"],
        timeout=30,
    )

    print("=== Production verification ===\n")

    api_status = ssh_run(client, "sudo systemctl is-active indcool-api").strip()
    print(f"API service: {api_status}")

    health = ssh_run(client, "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/health").strip()
    print(f"API health (server): {health}")

    migrate = ssh_run(
        client,
        f"sudo -u www-data bash -lc 'cd {remote_api} && "
        "export $(grep -E ^DATABASE_BACKEND= .env | xargs) "
        "$(grep -E ^MYSQL_DATABASE_URL= .env | xargs) && "
        "venv/bin/alembic -c alembic.ini current 2>&1 | tail -1'",
    ).strip()
    print(f"DB migration: {migrate}")

    js_file = ssh_run(client, "ls -1t /var/www/indcool/ui/assets/index-*.js | head -1").strip()
    print(f"UI bundle: {js_file}")

    markers = {
        "Order search on New Complaint": "Search Orders",
        "Workflow: Ask for Invoice": "Ask for Invoice",
        "Workflow: Request Sent": "Request Sent",
        "Workflow: Documents Received": "Documents Received",
        "Workflow yellow color": "bg-yellow-400",
        "Complaint create search hint": "Search by customer name",
    }
    for label, term in markers.items():
        count = ssh_run(client, f"grep -c '{term}' {js_file} 2>/dev/null || echo 0").strip()
        status = "OK" if count.isdigit() and int(count) > 0 else "MISSING"
        print(f"  {label}: {status}")

    api_flag = ssh_run(
        client,
        f"grep -c 'customer_documents_received' {remote_api}/app/routers/complaints.py 2>/dev/null || echo 0",
    ).strip()
    print(f"API customer_documents_received: {'OK' if api_flag.isdigit() and int(api_flag) > 0 else 'MISSING'}")

    client.close()

    ok = api_status == "active" and health == "200"
    print("\n" + ("All core checks passed." if ok else "Some checks failed — review above."))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
