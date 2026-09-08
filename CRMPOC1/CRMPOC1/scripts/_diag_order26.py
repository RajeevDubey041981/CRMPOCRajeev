"""Diagnose order 26 vendor edit permissions on production."""
import os
import sys

import paramiko

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOST = os.environ.get("INDCOOL_DEPLOY_HOST", "97.74.83.211")
USER = os.environ.get("INDCOOL_DEPLOY_USER", "indcooladmin")
PASSWORD = os.environ.get("INDCOOL_DEPLOY_PASSWORD", "JAdJh@yg4SFDP#!nGH")

REMOTE = r"""
import os
from pathlib import Path
from sqlalchemy import create_engine, text

for line in Path("/var/www/indcool/api/.env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ[k.strip()] = v.strip()

engine = create_engine(os.environ["MYSQL_DATABASE_URL"])
with engine.connect() as conn:
    order = conn.execute(text(
        "SELECT id, order_no, status, vendor_id, oem_bill_no, lrn_no, vendor_bill_no "
        "FROM orders WHERE id = 26"
    )).mappings().first()
    print("ORDER:", dict(order) if order else None)
    if order and order["vendor_id"]:
        vendor = conn.execute(text(
            "SELECT id, name_of_firm, email FROM vendors WHERE id = :vid"
        ), {"vid": order["vendor_id"]}).mappings().first()
        print("VENDOR:", dict(vendor) if vendor else None)
    users = conn.execute(text(
        "SELECT id, name, email, role FROM users WHERE role LIKE '%vendor%' OR email LIKE '%vendor%'"
    )).mappings().all()
    print("VENDOR_USERS:")
    for u in users:
        print(" ", dict(u))
    if order and order["vendor_id"]:
        for u in users:
            match = conn.execute(text(
                "SELECT id, email FROM vendors WHERE id = :vid AND email = :email"
            ), {"vid": order["vendor_id"], "email": u["email"]}).first()
            print(f"  owns_order[{u['email']}]:", bool(match))
    role = conn.execute(text(
        "SELECT r.name, p.module, p.can_view, p.can_create, p.can_edit, p.can_delete "
        "FROM roles r JOIN permissions p ON p.role_id = r.id "
        "WHERE r.name = 'vendor' AND p.module = 'orders'"
    )).mappings().all()
    print("VENDOR_ORDER_PERMS:")
    for row in role:
        print(" ", dict(row))
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
client.exec_command("cat > /tmp/diag_order26.py <<'PY'\n" + REMOTE + "\nPY")
_, stdout, _ = client.exec_command(
    "sudo -u www-data /var/www/indcool/api/venv/bin/python /tmp/diag_order26.py",
    get_pty=True,
)
print(stdout.read().decode("utf-8", "replace"))
client.close()
