import os, time
import MySQLdb
from werkzeug.security import generate_password_hash

# Wait for DB to be ready
host = os.getenv('MYSQL_HOST','db')
user = os.getenv('MYSQL_USER','root')
pwd = os.getenv('MYSQL_PASSWORD','example')
db = os.getenv('MYSQL_DB','ecommerce_db')
admin_email = os.getenv('ADMIN_EMAIL','admin@example.com')
admin_password = os.getenv('ADMIN_PASSWORD','adminpass')

print('Waiting for database...')
for _ in range(30):
    try:
        conn = MySQLdb.connect(host=host, user=user, passwd=pwd, db=db, charset='utf8mb4')
        break
    except Exception as e:
        print('DB not ready, retrying...', e)
        time.sleep(2)
else:
    raise SystemExit('DB did not become ready in time')

cur = conn.cursor()
# hash password
pw_hash = generate_password_hash(admin_password)
# insert or update admin user
cur.execute("""INSERT INTO users (name, email, password, is_admin) VALUES (%s,%s,%s,1)
ON DUPLICATE KEY UPDATE password=%s, is_admin=1""", ('Administrator', admin_email, pw_hash, pw_hash))
conn.commit()
cur.close()
conn.close()
print('Admin account ensured for', admin_email)
