import paramiko
import re

HOST = "97.74.83.211"
USER = "indcooladmin"
PASSWORD = "JAdJh@yg4SFDP#!nGH"

ALTER_SQL = (
    "ALTER TABLE item_masters "
    "ADD COLUMN serial_count INTEGER NOT NULL DEFAULT 1 AFTER mrp"
)
STAMP_SQL = (
    "UPDATE alembic_version SET version_num='0020_item_master_serial_count' "
    "WHERE version_num='0019_link_service_requests_to_complaints'"
)


def run(client, cmd: str) -> str:
    _, stdout, stderr = client.exec_command(cmd, get_pty=True)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    if err.strip():
        out += "\nSTDERR: " + err
    return out


client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWORD, timeout=30)

env_out = run(client, "sudo cat /var/www/indcool/api/.env")
match = re.search(
    r"MYSQL_DATABASE_URL=mysql\+mysqlconnector://([^:]+):([^@]+)@([^:/]+):(\d+)/(.+)",
    env_out,
)
if not match:
    raise SystemExit("Could not parse MYSQL_DATABASE_URL from production .env")

db_user, db_pass, db_host, db_port, db_name = match.groups()
db_user = db_user.strip()
db_pass = db_pass.replace("%40", "@").replace("%23", "#").strip()
db_host = db_host.strip()
db_port = db_port.strip()
db_name = db_name.strip()

mysql_base = (
    f"sudo mysql -h {db_host} -P {db_port} -u {db_user} "
    f"-p'{db_pass}' {db_name}"
)

print("=== check column ===")
check_out = run(
    client,
    f"{mysql_base} -e \"SHOW COLUMNS FROM item_masters LIKE 'serial_count';\"",
)
print(check_out)

if "serial_count" in check_out and "Field" in check_out:
    print("Column already exists on production.")
else:
    print("=== ALTER TABLE ===")
    alter_out = run(client, f"{mysql_base} -e \"{ALTER_SQL};\"")
    print(alter_out)
    if "Duplicate column name" in alter_out:
        print("Column already existed.")

    print("=== update alembic_version ===")
    print(run(client, f"{mysql_base} -e \"{STAMP_SQL}; SELECT * FROM alembic_version;\""))

print("=== verify ===")
print(run(client, f"{mysql_base} -e \"SHOW COLUMNS FROM item_masters LIKE 'serial_count';\""))
print(run(client, f"{mysql_base} -e \"SELECT version_num FROM alembic_version;\""))

print("=== restart API ===")
print(run(client, "sudo systemctl restart indcool-api && sleep 2 && sudo systemctl is-active indcool-api"))

client.close()
