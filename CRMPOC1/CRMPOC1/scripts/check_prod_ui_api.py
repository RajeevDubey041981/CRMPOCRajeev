import paramiko
HOST = "97.74.83.211"
USER = "indcooladmin"
PASSWORD = "JAdJh@yg4SFDP#!nGH"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASSWORD, timeout=30)
cmds = [
    "grep -o 'http://localhost[^\" ]*' /var/www/indcool/ui/assets/index-DfsK9vcM.js | sort -u | head",
    "grep -o 'https://indcoolapplainces.com[^\" ]*' /var/www/indcool/ui/assets/index-DfsK9vcM.js | head -3",
    "sudo journalctl -u indcool-api --since '30 min ago' --no-pager | grep complaints | tail -20",
]
for cmd in cmds:
    print('===', cmd)
    _, o, _ = c.exec_command(cmd, get_pty=True)
    print(o.read().decode() or '(none)')
c.close()
