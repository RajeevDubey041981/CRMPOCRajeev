#!/usr/bin/env python3
"""Compare local vs production DB revision, counts, and key file hashes."""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

import paramiko
import mysql.connector
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api"
DEPLOY_ENV = ROOT / "scripts" / "deploy.env.example"


def read_deploy_password() -> str:
    for line in DEPLOY_ENV.read_text(encoding="utf-8").splitlines():
        if line.startswith("INDCOOL_DEPLOY_PASSWORD="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("INDCOOL_DEPLOY_PASSWORD not found in deploy.env.example")


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run_ssh(client: paramiko.SSHClient, cmd: str) -> str:
    _, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode("utf-8", "replace").strip()
    err = stderr.read().decode("utf-8", "replace").strip()
    return out or err or "(empty)"


def main() -> None:
    host = "97.74.83.211"
    user = "indcooladmin"
    pwd = read_deploy_password()

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=pwd, timeout=30)

    print("=" * 60)
    print("PRODUCTION")
    print("=" * 60)

    prod_cmds = {
        "alembic_version_table": "sudo mysql -N -e \"SELECT version_num FROM indcool.alembic_version\"",
        "databases": "sudo mysql -N -e \"SHOW DATABASES\"",
        "installation_tables": (
            "sudo mysql -N -e \"SELECT table_schema, table_name FROM information_schema.tables "
            "WHERE table_name LIKE '%installation%' ORDER BY 1,2\""
        ),
        "api_service": "systemctl is-active indcool-api",
        "resume_workflow_api": "grep -l resume-workflow /var/www/indcool/api/app/routers/*.py 2>/dev/null || echo NOT_FOUND",
        "completion_approval_count": "grep -c completion-approval /var/www/indcool/api/app/routers/installation_callcenter.py 2>/dev/null || echo 0",
        "returned_status_in_api": "grep -c Returned /var/www/indcool/api/app/routers/installations.py 2>/dev/null || echo 0",
        "api_mtime": "stat -c '%y %n' /var/www/indcool/api/app/routers/installation_callcenter.py /var/www/indcool/api/app/routers/installations.py",
        "ui_mtime": "stat -c '%y %n' /var/www/indcool/ui/index.html",
        "table_counts": (
            "sudo mysql -N -e \""
            "SELECT 'installation_requests', COUNT(*) FROM indcool.installation_requests "
            "UNION ALL SELECT 'complaints', COUNT(*) FROM indcool.complaints "
            "UNION ALL SELECT 'users', COUNT(*) FROM indcool.users "
            "UNION ALL SELECT 'orders', COUNT(*) FROM indcool.orders\""
        ),
        "install_statuses": (
            "sudo mysql -N -e \"SELECT status, COUNT(*) FROM indcool.installation_requests GROUP BY status ORDER BY status\""
        ),
        "install_61_63": (
            "sudo mysql -e \"SELECT id, status, admin_billing_type, assigned_engineer, order_id "
            "FROM indcool.installation_requests WHERE id IN (61,62,63) ORDER BY id\""
        ),
    }
    for name, cmd in prod_cmds.items():
        print(f"\n--- prod: {name} ---")
        print(run_ssh(client, cmd))

    print("\n" + "=" * 60)
    print("LOCAL")
    print("=" * 60)

    r = subprocess.run(
        [str(API / "venv" / "Scripts" / "alembic.exe"), "-c", "alembic.ini", "current"],
        capture_output=True,
        text=True,
        cwd=API,
    )
    print("\n--- local: alembic_current ---")
    print((r.stdout or r.stderr).strip())

    # Use same DB URL as the API (alembic already connects successfully)
    sys.path.insert(0, str(API))
    from app.config import settings

    url = settings.get_database_url()
    # mysql+mysqlconnector://user:pass@host:port/db
    import re

    m = re.match(r"mysql\+mysqlconnector://([^:]+):([^@]+)@([^:/]+):(\d+)/(.+)", url)
    if not m:
        raise SystemExit(f"Cannot parse database URL: {url}")
    user, password, host, port, database = m.groups()
    from urllib.parse import unquote

    password = unquote(password)
    conn = mysql.connector.connect(
        host=host if host != "host.docker.internal" else "127.0.0.1",
        user=user,
        password=password,
        database=database,
        port=int(port),
    )
    cur = conn.cursor()
    print("\n--- local: table_counts ---")
    for t in ["installation_requests", "complaints", "users", "orders"]:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"{t}\t{cur.fetchone()[0]}")
    print("\n--- local: install_statuses ---")
    cur.execute("SELECT status, COUNT(*) FROM installation_requests GROUP BY status ORDER BY status")
    for status, count in cur.fetchall():
        print(f"{status}\t{count}")
    print("\n--- local: install_61_63 ---")
    cur.execute(
        "SELECT id, status, admin_billing_type, assigned_engineer, order_id "
        "FROM installation_requests WHERE id IN (61,62,63) ORDER BY id"
    )
    cols = [d[0] for d in cur.description]
    print("\t".join(cols))
    for row in cur.fetchall():
        print("\t".join(str(x) if x is not None else "NULL" for x in row))
    conn.close()

    print("\n" + "=" * 60)
    print("CODE FILE COMPARISON (MD5)")
    print("=" * 60)

    file_pairs = [
        ("api/app/routers/installation_callcenter.py", API / "app/routers/installation_callcenter.py"),
        ("api/app/routers/installations.py", API / "app/routers/installations.py"),
        ("api/app/services/installation_workflow.py", API / "app/services/installation_workflow.py"),
        ("ui/src/components/installations/InstallationPostVerifyWorkflow.jsx", ROOT / "ui/src/components/installations/InstallationPostVerifyWorkflow.jsx"),
        ("ui/src/pages/Dashboard.jsx", ROOT / "ui/src/pages/Dashboard.jsx"),
        ("ui/src/utils/installationWorkflowSteps.js", ROOT / "ui/src/utils/installationWorkflowSteps.js"),
    ]
    for remote_rel, local_path in file_pairs:
        remote = f"/var/www/indcool/{remote_rel.replace('api/', 'api/').replace('ui/', 'ui/')}"
        if remote_rel.startswith("api/"):
            remote = "/var/www/indcool/" + remote_rel
        else:
            remote = "/var/www/indcool/" + remote_rel
        local_md5 = md5_file(local_path)
        prod_out = run_ssh(client, f"md5sum {remote} 2>/dev/null || echo MISSING")
        prod_md5 = prod_out.split()[0] if prod_out and prod_out != "MISSING" and not prod_out.startswith("md5sum:") else "MISSING"
        match = "SAME" if prod_md5 == local_md5 else "DIFFERENT"
        print(f"\n{remote_rel}")
        print(f"  local: {local_md5}")
        print(f"  prod:  {prod_md5}")
        print(f"  => {match}")

    # UI built assets - check if prod has recent dashboard filters
    print("\n--- prod: ui built assets (grep patterns) ---")
    ui_patterns = [
        "queryType",
        "query_type",
        "Query Type",
        "serviceType",
        "Service Type",
        "resumeWorkflow",
        "Completion Pending Approval",
        "Return to engineer",
        "showSerialWorkflow",
    ]
    for pattern in ui_patterns:
        out = run_ssh(client, f"grep -rl '{pattern}' /var/www/indcool/ui/assets/*.js 2>/dev/null | wc -l")
        print(f"  {pattern}: {out} file(s)")

    print("\n--- local: key source file mtimes ---")
    import datetime

    local_ui_files = [
        ROOT / "ui/src/pages/Dashboard.jsx",
        ROOT / "ui/src/pages/installations/InstallationDetail.jsx",
        ROOT / "ui/src/pages/installations/BulkInstallationWorkflowModal.jsx",
        ROOT / "ui/src/pages/installations/InstallationCallCenterWorkflow.jsx",
        ROOT / "ui/src/components/installations/InstallationPostVerifyWorkflow.jsx",
    ]
    deploy_cutoff = datetime.datetime(2026, 9, 4, 19, 9, 43)  # prod ui index.html mtime UTC
    for p in local_ui_files:
        if p.exists():
            mtime = datetime.datetime.fromtimestamp(p.stat().st_mtime)
            flag = " (NEWER than prod deploy)" if mtime > deploy_cutoff else ""
            print(f"  {p.relative_to(ROOT)}: {mtime}{flag}")

    client.close()


if __name__ == "__main__":
    main()
