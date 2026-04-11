import os
from flask import Flask, render_template
from extensions import init_app, mysql
from routes.auth import auth_bp
from routes.products import products_bp
from routes.cart import cart_bp
from routes.admin import admin_bp
from routes.account import account_bp
from routes.checkout import checkout_bp


from config import Config

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(products_bp, url_prefix="/products")
    app.register_blueprint(cart_bp, url_prefix="/cart")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(account_bp)
    app.register_blueprint(checkout_bp, url_prefix="/checkout")

    _db_migrated = False

    @app.before_request
    def run_migrations():
        nonlocal _db_migrated
        if _db_migrated:
            return
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS addresses (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    label VARCHAR(100),
                    line1 VARCHAR(255) NOT NULL,
                    city VARCHAR(100) NOT NULL,
                    country VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                ALTER TABLE orders ADD COLUMN IF NOT EXISTS
                paystack_reference VARCHAR(100) DEFAULT NULL
            """)
            mysql.connection.commit()
            cur.close()
            _db_migrated = True
        except Exception as e:
            app.logger.warning(f"Migration warning: {e}")

    @app.route("/")
    def index():
        return render_template("index.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
