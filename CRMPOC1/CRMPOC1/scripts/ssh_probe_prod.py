import paramiko

HOST = "97.74.83.211"
USER = "indcooladmin"
PASSWORD = "JAdJh@yg4SFDP#!nGH"

cmds = [
    "sudo cat /var/www/indcool/api/indcool-api.service",
    "sudo systemctl cat indcool-api | head -40",
]

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWORD, timeout=30)

for cmd in cmds:
    print("===", cmd, "===")
    _, stdout, _ = client.exec_command(cmd, get_pty=True)
    print(stdout.read().decode())

client.close()
