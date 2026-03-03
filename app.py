# app.py
import os
from flask import Flask, render_template
from extensions import init_app  # use your central init function
from routes.auth import auth_bp
from routes.products import products_bp
from routes.cart import cart_bp
from routes.admin import admin_bp
from routes.account import account_bp
from routes.checkout import checkout_bp


def create_app():
    """Application factory for the ecommerce platform."""
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

    # Initialize extensions and database config
    init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(products_bp, url_prefix="/products")
    app.register_blueprint(cart_bp, url_prefix="/cart")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(account_bp, url_prefix="/account")
    app.register_blueprint(checkout_bp, url_prefix="/checkout")

    # Home route
    @app.route("/")
    def index():
        return render_template("index.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
