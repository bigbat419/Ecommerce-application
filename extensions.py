# extensions.py
import os
from flask_mysqldb import MySQL
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Initialize empty extension instances (Flask will bind them later)
mysql = MySQL()
login_manager = LoginManager()
csrf = CSRFProtect()

def init_app(app):
    """Initialize all Flask extensions with the given app."""
    # MySQL configuration
    app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
    app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
    app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
    app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'ecommerce_db')
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

    # Initialize extensions
    mysql.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Login manager setup
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"
