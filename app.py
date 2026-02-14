# app.py
import os
from flask import Flask
from extensions import init_app 
from routes.auth import auth_bp
from routes.products import products_bp
from routes.cart import cart_bp
from routes.account import account_bp
from flask import Flask
from routes.checkout import checkout_bp
from routes.admin import admin_bp


def create_app():
    """Application factory for the ecommerce platform."""
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

    if __name__=="__main__":
        app.run(debug=True)


    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(products_bp, url_prefix="/products")
    app.register_blueprint(cart_bp, url_prefix="/cart")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(account_bp, url_prefix="/account")
    app.register_blueprint(checkout_bp, url_prefix="/checkout")
    # Home route
    return app
    
create_app()