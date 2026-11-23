import os
from flask import Flask, render_template, redirect, url_for
from extensions import init_app, mysql
from routes.auth import auth_bp
from routes.products import products_bp
from routes.cart import cart_bp
from routes.admin import admin_bp
from routes.account import account_bp
from routes.checkout import checkout_bp
from routes.wishlist import wishlist_bp
from routes.reviews import reviews_bp
from routes.static_pages import static_pages_bp

from config import Config


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    init_app(app)

    # ── Core blueprints ───────────────────────────────────────────
    app.register_blueprint(auth_bp,          url_prefix="/auth")
    app.register_blueprint(products_bp,      url_prefix="/products")
    app.register_blueprint(cart_bp,          url_prefix="/cart")
    app.register_blueprint(admin_bp,         url_prefix="/admin")
    app.register_blueprint(account_bp)                           # /account/* (prefix set in blueprint)
    app.register_blueprint(checkout_bp,      url_prefix="/checkout")
    app.register_blueprint(wishlist_bp,      url_prefix="/wishlist")
    app.register_blueprint(reviews_bp,       url_prefix="/reviews")
    app.register_blueprint(static_pages_bp,  url_prefix="/pages")

    _db_migrated = False

    @app.before_request
    def run_migrations():
        nonlocal _db_migrated
        if _db_migrated:
            return
        try:
            cur = mysql.connection.cursor()

            # ── Phase-1 tables ────────────────────────────────────
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
            # Safe paystack_reference column add
            try:
                cur.execute("""
                    ALTER TABLE orders ADD COLUMN IF NOT EXISTS
                    paystack_reference VARCHAR(100) DEFAULT NULL
                """)
            except Exception:
                pass  # column already exists on older MySQL without IF NOT EXISTS
            cur.execute("""
                CREATE TABLE IF NOT EXISTS wishlist (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    product_id INT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_wish (user_id, product_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT NOT NULL,
                    user_id INT NOT NULL,
                    rating TINYINT NOT NULL DEFAULT 5,
                    title VARCHAR(160),
                    body TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS coupons (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    code VARCHAR(50) UNIQUE NOT NULL,
                    discount_pct DECIMAL(5,2) NOT NULL DEFAULT 0,
                    max_uses INT DEFAULT NULL,
                    uses INT DEFAULT 0,
                    active TINYINT DEFAULT 1,
                    expires_at DATE DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # ── Phase-2 tables ────────────────────────────────────
            cur.execute("""
                CREATE TABLE IF NOT EXISTS brands (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(120) NOT NULL,
                    slug VARCHAR(120) UNIQUE NOT NULL,
                    description TEXT,
                    logo VARCHAR(255),
                    website VARCHAR(255),
                    active TINYINT(1) DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(120) NOT NULL,
                    slug VARCHAR(120) UNIQUE NOT NULL,
                    parent_id INT DEFAULT NULL,
                    description TEXT,
                    image VARCHAR(255),
                    active TINYINT(1) DEFAULT 1,
                    sort_order INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS product_images (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT NOT NULL,
                    image VARCHAR(255) NOT NULL,
                    sort_order INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS shipping_methods (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(120) NOT NULL,
                    description VARCHAR(255),
                    price DECIMAL(10,2) NOT NULL DEFAULT 0,
                    min_days INT DEFAULT 1,
                    max_days INT DEFAULT 7,
                    free_above DECIMAL(10,2) DEFAULT NULL,
                    active TINYINT(1) DEFAULT 1,
                    sort_order INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS order_tracking (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    order_id INT NOT NULL,
                    status VARCHAR(80) NOT NULL,
                    note VARCHAR(255),
                    location VARCHAR(120),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS return_requests (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    order_id INT NOT NULL,
                    user_id INT NOT NULL,
                    reason VARCHAR(200) NOT NULL,
                    details TEXT,
                    status VARCHAR(50) DEFAULT 'pending',
                    admin_note TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id)  REFERENCES users(id)  ON DELETE CASCADE
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS loyalty_points (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    points INT NOT NULL DEFAULT 0,
                    event_type VARCHAR(80) NOT NULL,
                    reference VARCHAR(120),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS store_settings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    key_name VARCHAR(100) UNIQUE NOT NULL,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS staff_roles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(80) NOT NULL,
                    permissions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # ── Safe ALTER TABLE additions ─────────────────────────
            for alter in [
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS brand_id INT DEFAULT NULL",
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS compare_at_price DECIMAL(10,2) DEFAULT NULL",
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS cost_price DECIMAL(10,2) DEFAULT NULL",
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS sku VARCHAR(100) DEFAULT NULL",
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS barcode VARCHAR(100) DEFAULT NULL",
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS short_description TEXT DEFAULT NULL",
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS specifications TEXT DEFAULT NULL",
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS weight DECIMAL(8,2) DEFAULT NULL",
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS length DECIMAL(8,2) DEFAULT NULL",
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS width DECIMAL(8,2) DEFAULT NULL",
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS height DECIMAL(8,2) DEFAULT NULL",
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS low_stock_threshold INT DEFAULT 5",
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS manage_stock TINYINT(1) DEFAULT 1",
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active'",
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS taxable TINYINT(1) DEFAULT 1",
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS tags VARCHAR(255) DEFAULT NULL",
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS meta_title VARCHAR(255) DEFAULT NULL",
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS meta_description TEXT DEFAULT NULL",
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS is_featured TINYINT(1) DEFAULT 0",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS staff_role_id INT DEFAULT NULL",
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipping_method_id INT DEFAULT NULL",
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS tracking_number VARCHAR(100) DEFAULT NULL",
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipping_address TEXT DEFAULT NULL",
            ]:
                try:
                    cur.execute(alter)
                except Exception:
                    pass  # column already exists

            # ── Default store settings (idempotent) ───────────────
            for k, v in [
                ('site_name',           'Flamingos'),
                ('site_tagline',        'Shop Smarter. Live Better.'),
                ('currency',            'NGN'),
                ('currency_symbol',     '₦'),
                ('free_shipping_above', '25000'),
                ('contact_email',       'support@flamingos.com'),
                ('contact_phone',       '+234 801 234 5678'),
                ('loyalty_points_rate', '1'),
                ('meta_description',    'Flamingos — Premium fashion at unbeatable prices.'),
            ]:
                cur.execute(
                    "INSERT IGNORE INTO store_settings (key_name, value) VALUES (%s, %s)",
                    (k, v),
                )

            mysql.connection.commit()
            cur.close()
            _db_migrated = True
        except Exception as e:
            app.logger.warning(f"Migration warning: {e}")
            # Do NOT set _db_migrated = True — retry on next request

    # ── Root routes ───────────────────────────────────────────────
    @app.route("/")
    def index():
        try:
            cur = mysql.connection.cursor()
            cur.execute(
                "SELECT id, name, description, price, stock, image, category "
                "FROM products ORDER BY created_at DESC LIMIT 8"
            )
            featured = cur.fetchall()
            cur.close()
        except Exception:
            featured = []
        return render_template("index.html", featured_products=featured)

    @app.route("/admin/")
    def admin_root():
        """Redirect /admin/ to the dashboard so the URL doesn't 404."""
        return redirect(url_for("admin.dashboard"))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
