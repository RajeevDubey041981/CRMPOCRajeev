import paramiko
import re

HOST = "97.74.83.211"
USER = "indcooladmin"
PASSWORD = "JAdJh@yg4SFDP#!nGH"
ORDER_ID = 13


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
    raise SystemExit("Could not parse MYSQL_DATABASE_URL")

db_user, db_pass, db_host, db_port, db_name = match.groups()
db_pass = db_pass.replace("%40", "@").replace("%23", "#").strip()
mysql_base = (
    f"sudo mysql -h {db_host.strip()} -P {db_port.strip()} -u {db_user.strip()} "
    f"-p'{db_pass}' {db_name.strip()}"
)

print(f"=== Order {ORDER_ID} ===")
print(run(client, f"""{mysql_base} -e "
SELECT o.id, o.order_no, o.customer_name, o.status, v.id AS vendor_id, v.vendor_code, v.name_of_firm, v.email AS vendor_email
FROM orders o
LEFT JOIN vendors v ON v.id = o.vendor_id
WHERE o.id = {ORDER_ID};
\""""))

print("=== Vendor users ===")
print(run(client, f"""{mysql_base} -e "
SELECT u.id, u.name, u.email, u.role, v.name_of_firm, v.vendor_code
FROM users u
LEFT JOIN vendors v ON LOWER(v.email) = LOWER(u.email)
WHERE u.role = 'vendor';
\""""))

print("=== User for vendor@indcool.com ===")
print(run(client, f"""{mysql_base} -e "
SELECT id, name, email, role, is_active FROM users WHERE email = 'vendor@indcool.com';
\""""))

client.close()
