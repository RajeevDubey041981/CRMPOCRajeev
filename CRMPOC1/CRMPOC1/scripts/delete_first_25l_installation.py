"""Delete the first Geyser 25L installation request from production DB."""
import paramiko
import re

HOST = "97.74.83.211"
USER = "indcooladmin"
PASSWORD = "JAdJh@yg4SFDP#!nGH"


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
db_pass = db_pass.replace("%40", "@").replace("%23", "#").strip()
mysql_base = (
    f"sudo mysql -h {db_host.strip()} -P {db_port.strip()} -u {db_user.strip()} "
    f"-p'{db_pass}' {db_name.strip()}"
)

print("=== Matching installation requests (Geyser 25L) ===")
list_sql = (
    "SELECT id, customer_name, product_name, status, request_date "
    "FROM installation_requests "
    "WHERE product_name LIKE '%25L%' OR product_name LIKE '%Geyser 25L%' "
    "ORDER BY id ASC LIMIT 10;"
)
print(run(client, f'{mysql_base} -e "{list_sql}"'))

print("=== First row id ===")
id_sql = (
    "SELECT id FROM installation_requests "
    "WHERE product_name LIKE '%25L%' OR product_name LIKE '%Geyser 25L%' "
    "ORDER BY id ASC LIMIT 1;"
)
id_out = run(client, f'{mysql_base} -N -e "{id_sql}"')
m = re.search(r"\b(\d+)\b", id_out)
if not m:
    raise SystemExit(f"No matching installation request found. Output: {id_out!r}")
first_id = m.group(1)

print(f"Deleting installation request id={first_id}")
delete_sql = f"DELETE FROM installation_requests WHERE id = {first_id};"
print(run(client, f'{mysql_base} -e "{delete_sql} SELECT ROW_COUNT() AS deleted;"'))

print("=== Remaining count ===")
count_sql = (
    "SELECT COUNT(*) AS remaining FROM installation_requests "
    "WHERE product_name LIKE '%25L%' OR product_name LIKE '%Geyser 25L%';"
)
print(run(client, f'{mysql_base} -e "{count_sql}"'))

client.close()
print("Done.")
