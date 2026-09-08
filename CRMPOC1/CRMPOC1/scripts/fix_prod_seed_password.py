import paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("97.74.83.211", username="indcooladmin", password="JAdJh@yg4SFDP#!nGH", timeout=30)
_, o, _ = c.exec_command(
    "sudo sed -i 's/^SEED_ADMIN_PASSWORD=.*/SEED_ADMIN_PASSWORD=admin123/' /var/www/indcool/api/.env && sudo grep SEED_ADMIN_PASSWORD /var/www/indcool/api/.env",
    get_pty=True,
)
print(o.read().decode())
c.close()
