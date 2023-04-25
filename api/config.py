from app import app
from flaskext.mysql import MySQL

mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Iammico0619'
app.config['MYSQL_DATABASE_DB'] = 'burgis_db'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)