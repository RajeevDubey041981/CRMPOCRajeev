import json
import paramiko

HOST = "97.74.83.211"
USER = "indcooladmin"
PASSWORD = "JAdJh@yg4SFDP#!nGH"

cmds = [
    "sudo journalctl -u indcool-api --no-pager 2>/dev/null | grep -iE 'complaint|Unknown column|ProgrammingError|500' | tail -40",
    "curl -s -o /dev/null -w 'complaints:%{http_code}\\n' https://indcoolapplainces.com/api/complaints",
    "curl -s -X POST https://indcoolapplainces.com/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"admin@indcool.com\",\"password\":\"change-this-password\"}' | head -c 200",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASSWORD, timeout=30)
for cmd in cmds:
    print("===", cmd[:100])
    _, o, _ = c.exec_command(cmd, get_pty=True)
    print(o.read().decode())
c.close()
