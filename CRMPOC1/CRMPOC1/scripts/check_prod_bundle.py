import paramiko
HOST = "97.74.83.211"
USER = "indcooladmin"
PASSWORD = "JAdJh@yg4SFDP#!nGH"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASSWORD, timeout=30)
cmds = [
    "ls -la /var/www/indcool/ui/assets/",
    "grep -o 'http://localhost:8010' /var/www/indcool/ui/assets/index-C_I500zA.js | wc -l",
    "grep -o 'http://localhost:8010' /var/www/indcool/ui/assets/*.js | sort | uniq -c",
]
for cmd in cmds:
    print('===', cmd)
    _, o, _ = c.exec_command(cmd, get_pty=True)
    print(o.read().decode())
c.close()
