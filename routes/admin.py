import os
import re
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from extensions import mysql


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[\s_-]+', '-', text)


admin_bp = Blueprint("admin", __name__, template_folder="../templates")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access required.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────
@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    cur = mysql.connection.cursor()

    # Core counts
    cur.execute("SELECT COUNT(*) AS cnt FROM products")
    total_products = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) AS cnt FROM users")
    total_users = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) AS cnt FROM orders")
    total_orders = cur.fetchone()["cnt"]
    cur.execute("SELECT COALESCE(SUM(total),0) AS rev FROM orders WHERE status='paid'")
    revenue = cur.fetchone()["rev"]

    # Delta stats
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    cur.execute("SELECT COUNT(*) AS cnt FROM products WHERE created_at >= %s", (week_ago,))
    new_products = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) AS cnt FROM users WHERE created_at >= %s", (week_ago,))
    new_users = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) AS cnt FROM orders WHERE status='pending'")
    pending_orders = cur.fetchone()["cnt"]

    # Recent orders
    cur.execute("""
        SELECT o.id, u.name, o.total, o.status, o.created_at, o.paystack_reference
        FROM orders o JOIN users u ON u.id = o.user_id
        ORDER BY o.created_at DESC LIMIT 10
    """)
    recent_orders = cur.fetchall()

    # Revenue last 7 days
    revenue_labels = []
    revenue_data = []
    for i in range(6, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        label = (datetime.now() - timedelta(days=i)).strftime('%d %b')
        cur.execute(
            "SELECT COALESCE(SUM(total),0) AS rev FROM orders WHERE status='paid' AND DATE(created_at)=%s",
            (d,)
        )
        rev = float(cur.fetchone()["rev"])
        revenue_labels.append(label)
        revenue_data.append(rev)

    # Status distribution
    cur.execute("SELECT COUNT(*) AS cnt FROM orders WHERE status='paid'")
    paid_cnt = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) AS cnt FROM orders WHERE status='pending'")
    pend_cnt = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) AS cnt FROM orders WHERE status='cancelled'")
    canc_cnt = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) AS cnt FROM orders WHERE status='shipped'")
    ship_cnt = cur.fetchone()["cnt"]
    status_data = [paid_cnt, pend_cnt, canc_cnt, ship_cnt]

    # Top categories
    cur.execute("""
        SELECT category, COUNT(*) AS cnt FROM products
        WHERE category IS NOT NULL AND category <> ''
        GROUP BY category ORDER BY cnt DESC LIMIT 5
    """)
    top_categories = cur.fetchall()

    cur.close()
    return render_template(
        "admin/admin_dashboard.html",
        total_products=total_products,
        total_users=total_users,
        total_orders=total_orders,
        revenue=revenue,
        new_products=new_products,
        new_users=new_users,
        pending_orders=pending_orders,
        recent_orders=recent_orders,
        revenue_labels=revenue_labels,
        revenue_data=revenue_data,
        status_data=status_data,
        top_categories=top_categories,
    )


# ─────────────────────────────────────────────
# Products
# ─────────────────────────────────────────────
@admin_bp.route("/products")
@login_required
@admin_required
def products():
    q = request.args.get('q', '').strip()
    cur = mysql.connection.cursor()
    if q:
        cur.execute(
            "SELECT id, name, slug, price, stock, category, image, created_at FROM products WHERE name LIKE %s ORDER BY created_at DESC",
            (f"%{q}%",)
        )
    else:
        cur.execute("SELECT id, name, slug, price, stock, category, image, created_at FROM products ORDER BY created_at DESC")
    products = cur.fetchall()
    cur.close()
    return render_template("admin/products.html", products=products)


@admin_bp.route("/products/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_product():
    if request.method == "POST":
        name        = request.form.get("name", "").strip()
        price       = request.form.get("price", "").strip()
        stock       = request.form.get("stock", "").strip()
        category    = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        image       = request.files.get("image")

        if not name or not price or not stock:
            flash("Name, price, and stock are required.", "danger")
            return redirect(url_for("admin.add_product"))

        try:
            price = float(price)
            stock = int(stock)
        except ValueError:
            flash("Price must be a number and stock must be an integer.", "danger")
            return redirect(url_for("admin.add_product"))

        image_path = None
        if image and image.filename and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            upload_folder = os.path.join(current_app.root_path, "static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            image.save(os.path.join(upload_folder, filename))
            image_path = f"uploads/{filename}"

        slug = slugify(name)
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM products WHERE slug=%s", (slug,))
        if cur.fetchone()['cnt'] > 0:
            slug = f"{slug}-{int(__import__('time').time())}"
        cur.execute(
            "INSERT INTO products (name, price, stock, category, description, image, slug) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (name, price, stock, category, description, image_path, slug),
        )
        mysql.connection.commit()
        cur.close()
        flash("Product added successfully.", "success")
        return redirect(url_for("admin.products"))

    return render_template("admin/new_product.html")


@admin_bp.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_product(product_id):
    cur = mysql.connection.cursor()
    if request.method == "POST":
        name        = request.form.get("name", "").strip()
        price       = request.form.get("price", "").strip()
        stock       = request.form.get("stock", "").strip()
        category    = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        image       = request.files.get("image")

        try:
            price = float(price)
            stock = int(stock)
        except ValueError:
            flash("Invalid price or stock.", "danger")
            return redirect(url_for("admin.edit_product", product_id=product_id))

        image_path = None
        if image and image.filename and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            upload_folder = os.path.join(current_app.root_path, "static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            image.save(os.path.join(upload_folder, filename))
            image_path = f"uploads/{filename}"

        if image_path:
            cur.execute(
                "UPDATE products SET name=%s, price=%s, stock=%s, category=%s, description=%s, image=%s WHERE id=%s",
                (name, price, stock, category, description, image_path, product_id),
            )
        else:
            cur.execute(
                "UPDATE products SET name=%s, price=%s, stock=%s, category=%s, description=%s WHERE id=%s",
                (name, price, stock, category, description, product_id),
            )
        mysql.connection.commit()
        cur.close()
        flash("Product updated.", "success")
        return redirect(url_for("admin.products"))

    cur.execute("SELECT * FROM products WHERE id=%s", (product_id,))
    product = cur.fetchone()
    cur.close()
    if not product:
        flash("Product not found.", "warning")
        return redirect(url_for("admin.products"))
    return render_template("admin/edit_product.html", product=product)


@admin_bp.route("/products/delete/<int:product_id>", methods=["POST"])
@login_required
@admin_required
def delete_product(product_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM products WHERE id=%s", (product_id,))
    mysql.connection.commit()
    cur.close()
    flash("Product deleted.", "info")
    return redirect(url_for("admin.products"))


# ─────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────
@admin_bp.route("/users")
@login_required
@admin_required
def users():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name, email, role, is_admin, created_at FROM users ORDER BY created_at DESC")
    users = cur.fetchall()
    cur.close()
    return render_template("admin/users.html", users=users)


@admin_bp.route("/users/toggle-admin/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def toggle_admin(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT is_admin FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()
    if row:
        new_val = 0 if row["is_admin"] else 1
        cur.execute("UPDATE users SET is_admin=%s WHERE id=%s", (new_val, user_id))
        mysql.connection.commit()
        flash("User admin status updated.", "success")
    cur.close()
    return redirect(url_for("admin.users"))


# ─────────────────────────────────────────────
# Orders
# ─────────────────────────────────────────────
@admin_bp.route("/orders")
@login_required
@admin_required
def orders():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT o.id, u.name, o.total, o.status, o.created_at, o.paystack_reference
        FROM orders o
        JOIN users u ON u.id = o.user_id
        ORDER BY o.created_at DESC
    """)
    orders = cur.fetchall()
    cur.close()
    return render_template("admin/orders.html", orders=orders)


@admin_bp.route("/orders/update/<int:order_id>", methods=["POST"])
@login_required
@admin_required
def update_order(order_id):
    new_status = request.form.get("status")
    cur = mysql.connection.cursor()
    cur.execute("UPDATE orders SET status=%s WHERE id=%s", (new_status, order_id))
    mysql.connection.commit()
    cur.close()
    flash("Order status updated.", "success")
    return redirect(url_for("admin.orders"))


# ─────────────────────────────────────────────
# Reviews
# ─────────────────────────────────────────────
@admin_bp.route("/reviews")
@login_required
@admin_required
def reviews_list():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT r.id, r.rating, r.title, r.body, r.created_at,
               u.name AS reviewer,
               p.name AS product_name
        FROM reviews r
        JOIN users u    ON u.id = r.user_id
        JOIN products p ON p.id = r.product_id
        ORDER BY r.created_at DESC
    """)
    reviews = cur.fetchall()
    cur.close()
    return render_template("admin/reviews.html", reviews=reviews)


@admin_bp.route("/reviews/delete/<int:review_id>", methods=["POST"])
@login_required
@admin_required
def delete_review(review_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM reviews WHERE id=%s", (review_id,))
    mysql.connection.commit()
    cur.close()
    flash("Review deleted.", "info")
    return redirect(url_for("admin.reviews_list"))


# ─────────────────────────────────────────────
# Coupons
# ─────────────────────────────────────────────
@admin_bp.route("/coupons")
@login_required
@admin_required
def coupons():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, code, discount_pct, max_uses, uses, active, expires_at FROM coupons ORDER BY created_at DESC")
    coupons = cur.fetchall()
    cur.close()
    return render_template("admin/coupons.html", coupons=coupons)


@admin_bp.route("/coupons/create", methods=["POST"])
@login_required
@admin_required
def create_coupon():
    code         = request.form.get("code", "").strip().upper()
    discount_pct = request.form.get("discount_pct", "0").strip()
    max_uses     = request.form.get("max_uses", "").strip() or None
    expires_at   = request.form.get("expires_at", "").strip() or None

    if not code or not discount_pct:
        flash("Code and discount are required.", "danger")
        return redirect(url_for("admin.coupons"))

    try:
        discount_pct = float(discount_pct)
        max_uses = int(max_uses) if max_uses else None
    except ValueError:
        flash("Invalid discount or max uses value.", "danger")
        return redirect(url_for("admin.coupons"))

    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO coupons (code, discount_pct, max_uses, expires_at) VALUES (%s,%s,%s,%s)",
        (code, discount_pct, max_uses, expires_at),
    )
    mysql.connection.commit()
    cur.close()
    flash(f"Coupon {code} created.", "success")
    return redirect(url_for("admin.coupons"))


@admin_bp.route("/coupons/delete/<int:coupon_id>", methods=["POST"])
@login_required
@admin_required
def delete_coupon(coupon_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM coupons WHERE id=%s", (coupon_id,))
    mysql.connection.commit()
    cur.close()
    flash("Coupon deleted.", "info")
    return redirect(url_for("admin.coupons"))


# ─────────────────────────────────────────────
# Categories
# ─────────────────────────────────────────────
@admin_bp.route("/categories")
@login_required
@admin_required
def categories():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT c.id, c.name, c.slug, c.active, c.sort_order, c.created_at,
               p.name AS parent_name
        FROM categories c
        LEFT JOIN categories p ON p.id = c.parent_id
        ORDER BY c.sort_order, c.name
    """)
    cats = cur.fetchall()
    cur.close()
    return render_template("admin/categories.html", categories=cats)


@admin_bp.route("/categories/save", methods=["POST"])
@login_required
@admin_required
def save_category():
    cat_id   = request.form.get("id", "").strip()
    name     = request.form.get("name", "").strip()
    parent   = request.form.get("parent_id", "").strip() or None
    desc     = request.form.get("description", "").strip()
    active   = 1 if request.form.get("active") else 0
    sort_ord = int(request.form.get("sort_order", 0) or 0)

    if not name:
        flash("Category name is required.", "danger")
        return redirect(url_for("admin.categories"))

    slug = slugify(name)
    cur = mysql.connection.cursor()
    if cat_id:
        cur.execute(
            "UPDATE categories SET name=%s, slug=%s, parent_id=%s, description=%s, active=%s, sort_order=%s WHERE id=%s",
            (name, slug, parent, desc, active, sort_ord, int(cat_id)),
        )
        flash("Category updated.", "success")
    else:
        cur.execute(
            "INSERT INTO categories (name, slug, parent_id, description, active, sort_order) VALUES (%s,%s,%s,%s,%s,%s)",
            (name, slug, parent, desc, active, sort_ord),
        )
        flash("Category created.", "success")
    mysql.connection.commit()
    cur.close()
    return redirect(url_for("admin.categories"))


@admin_bp.route("/categories/delete/<int:cat_id>", methods=["POST"])
@login_required
@admin_required
def delete_category(cat_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM categories WHERE id=%s", (cat_id,))
    mysql.connection.commit()
    cur.close()
    flash("Category deleted.", "info")
    return redirect(url_for("admin.categories"))


# ─────────────────────────────────────────────
# Brands
# ─────────────────────────────────────────────
@admin_bp.route("/brands")
@login_required
@admin_required
def brands():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM brands ORDER BY name")
    brands = cur.fetchall()
    cur.close()
    return render_template("admin/brands.html", brands=brands)


@admin_bp.route("/brands/save", methods=["POST"])
@login_required
@admin_required
def save_brand():
    brand_id = request.form.get("id", "").strip()
    name     = request.form.get("name", "").strip()
    website  = request.form.get("website", "").strip()
    desc     = request.form.get("description", "").strip()
    active   = 1 if request.form.get("active") else 0
    logo     = request.files.get("logo")

    if not name:
        flash("Brand name is required.", "danger")
        return redirect(url_for("admin.brands"))

    logo_path = None
    if logo and logo.filename and allowed_file(logo.filename):
        filename = secure_filename(logo.filename)
        upload_folder = os.path.join(current_app.root_path, "static", "uploads", "brands")
        os.makedirs(upload_folder, exist_ok=True)
        logo.save(os.path.join(upload_folder, filename))
        logo_path = f"uploads/brands/{filename}"

    slug = slugify(name)
    cur = mysql.connection.cursor()
    if brand_id:
        if logo_path:
            cur.execute(
                "UPDATE brands SET name=%s, slug=%s, description=%s, website=%s, logo=%s, active=%s WHERE id=%s",
                (name, slug, desc, website, logo_path, active, int(brand_id)),
            )
        else:
            cur.execute(
                "UPDATE brands SET name=%s, slug=%s, description=%s, website=%s, active=%s WHERE id=%s",
                (name, slug, desc, website, active, int(brand_id)),
            )
        flash("Brand updated.", "success")
    else:
        cur.execute(
            "INSERT INTO brands (name, slug, description, website, logo, active) VALUES (%s,%s,%s,%s,%s,%s)",
            (name, slug, desc, website, logo_path, active),
        )
        flash("Brand created.", "success")
    mysql.connection.commit()
    cur.close()
    return redirect(url_for("admin.brands"))


@admin_bp.route("/brands/delete/<int:brand_id>", methods=["POST"])
@login_required
@admin_required
def delete_brand(brand_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM brands WHERE id=%s", (brand_id,))
    mysql.connection.commit()
    cur.close()
    flash("Brand deleted.", "info")
    return redirect(url_for("admin.brands"))


# ─────────────────────────────────────────────
# Inventory
# ─────────────────────────────────────────────
@admin_bp.route("/inventory")
@login_required
@admin_required
def inventory():
    low_threshold = int(request.args.get("low", 10))
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, name, sku, category, stock, price, created_at
        FROM products ORDER BY stock ASC, name
    """)
    products = cur.fetchall()
    cur.execute("SELECT COUNT(*) AS cnt FROM products WHERE stock = 0")
    out_of_stock = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) AS cnt FROM products WHERE stock > 0 AND stock <= %s", (low_threshold,))
    low_stock = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) AS cnt FROM products WHERE stock > %s", (low_threshold,))
    healthy = cur.fetchone()["cnt"]
    cur.close()
    return render_template(
        "admin/inventory.html",
        products=products,
        low_threshold=low_threshold,
        out_of_stock=out_of_stock,
        low_stock=low_stock,
        healthy=healthy,
    )


@admin_bp.route("/inventory/update", methods=["POST"])
@login_required
@admin_required
def inventory_update():
    """Bulk-update stock levels submitted as product_id → new_stock pairs."""
    updated = 0
    cur = mysql.connection.cursor()
    for key, val in request.form.items():
        if key.startswith("stock_") and val.strip().isdigit():
            pid = int(key.split("_", 1)[1])
            cur.execute("UPDATE products SET stock=%s WHERE id=%s", (int(val), pid))
            updated += 1
    mysql.connection.commit()
    cur.close()
    flash(f"{updated} stock level(s) updated.", "success")
    return redirect(url_for("admin.inventory"))


# ─────────────────────────────────────────────
# Shipping
# ─────────────────────────────────────────────
@admin_bp.route("/shipping")
@login_required
@admin_required
def shipping():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM shipping_methods ORDER BY sort_order, name")
    methods = cur.fetchall()
    cur.close()
    return render_template("admin/shipping.html", methods=methods)


@admin_bp.route("/shipping/save", methods=["POST"])
@login_required
@admin_required
def save_shipping():
    sid      = request.form.get("id", "").strip()
    name     = request.form.get("name", "").strip()
    desc     = request.form.get("description", "").strip()
    price    = request.form.get("price", "0").strip()
    min_days = request.form.get("min_days", "1").strip()
    max_days = request.form.get("max_days", "7").strip()
    free_ab  = request.form.get("free_above", "").strip() or None
    active   = 1 if request.form.get("active") else 0
    sort_ord = int(request.form.get("sort_order", 0) or 0)

    if not name:
        flash("Method name is required.", "danger")
        return redirect(url_for("admin.shipping"))
    try:
        price    = float(price)
        min_days = int(min_days)
        max_days = int(max_days)
        free_ab  = float(free_ab) if free_ab else None
    except ValueError:
        flash("Invalid numeric values.", "danger")
        return redirect(url_for("admin.shipping"))

    cur = mysql.connection.cursor()
    if sid:
        cur.execute(
            "UPDATE shipping_methods SET name=%s, description=%s, price=%s, min_days=%s, max_days=%s, free_above=%s, active=%s, sort_order=%s WHERE id=%s",
            (name, desc, price, min_days, max_days, free_ab, active, sort_ord, int(sid)),
        )
        flash("Shipping method updated.", "success")
    else:
        cur.execute(
            "INSERT INTO shipping_methods (name, description, price, min_days, max_days, free_above, active, sort_order) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (name, desc, price, min_days, max_days, free_ab, active, sort_ord),
        )
        flash("Shipping method created.", "success")
    mysql.connection.commit()
    cur.close()
    return redirect(url_for("admin.shipping"))


@admin_bp.route("/shipping/delete/<int:method_id>", methods=["POST"])
@login_required
@admin_required
def delete_shipping(method_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM shipping_methods WHERE id=%s", (method_id,))
    mysql.connection.commit()
    cur.close()
    flash("Shipping method deleted.", "info")
    return redirect(url_for("admin.shipping"))


# ─────────────────────────────────────────────
# Returns management
# ─────────────────────────────────────────────
@admin_bp.route("/returns")
@login_required
@admin_required
def returns():
    status_filter = request.args.get("status", "")
    cur = mysql.connection.cursor()
    if status_filter:
        cur.execute("""
            SELECT rr.id, rr.reason, rr.status, rr.created_at,
                   u.name AS customer, u.email,
                   o.id AS order_id, o.total
            FROM return_requests rr
            JOIN users u  ON u.id  = rr.user_id
            JOIN orders o ON o.id  = rr.order_id
            WHERE rr.status = %s ORDER BY rr.created_at DESC
        """, (status_filter,))
    else:
        cur.execute("""
            SELECT rr.id, rr.reason, rr.status, rr.created_at,
                   u.name AS customer, u.email,
                   o.id AS order_id, o.total
            FROM return_requests rr
            JOIN users u  ON u.id  = rr.user_id
            JOIN orders o ON o.id  = rr.order_id
            ORDER BY rr.created_at DESC
        """)
    returns = cur.fetchall()
    cur.close()
    return render_template("admin/returns.html", returns=returns, status_filter=status_filter)


@admin_bp.route("/returns/update/<int:return_id>", methods=["POST"])
@login_required
@admin_required
def update_return(return_id):
    new_status = request.form.get("status")
    admin_note = request.form.get("admin_note", "").strip()
    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE return_requests SET status=%s, admin_note=%s WHERE id=%s",
        (new_status, admin_note, return_id),
    )
    mysql.connection.commit()
    cur.close()
    flash(f"Return #{return_id} updated to '{new_status}'.", "success")
    return redirect(url_for("admin.returns"))


# ─────────────────────────────────────────────
# Reports & Analytics
# ─────────────────────────────────────────────
@admin_bp.route("/reports")
@login_required
@admin_required
def reports():
    from datetime import datetime, timedelta
    period = request.args.get("period", "30")
    try:
        days = int(period)
    except ValueError:
        days = 30

    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    cur = mysql.connection.cursor()

    # Revenue summary
    cur.execute("SELECT COALESCE(SUM(total),0) AS rev FROM orders WHERE status='paid' AND created_at >= %s", (since,))
    period_revenue = float(cur.fetchone()["rev"])
    cur.execute("SELECT COUNT(*) AS cnt FROM orders WHERE status='paid' AND created_at >= %s", (since,))
    period_orders = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(DISTINCT user_id) AS cnt FROM orders WHERE created_at >= %s", (since,))
    active_customers = cur.fetchone()["cnt"]
    cur.execute("SELECT COALESCE(AVG(total),0) AS avg FROM orders WHERE status='paid' AND created_at >= %s", (since,))
    avg_order = float(cur.fetchone()["avg"])

    # Daily revenue chart
    labels, rev_data = [], []
    for i in range(days - 1, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        cur.execute(
            "SELECT COALESCE(SUM(total),0) AS r FROM orders WHERE status='paid' AND DATE(created_at)=%s", (d,)
        )
        rev_data.append(float(cur.fetchone()["r"]))
        labels.append((datetime.now() - timedelta(days=i)).strftime("%d %b"))

    # Top products
    cur.execute("""
        SELECT p.name, SUM(oi.quantity) AS sold, SUM(oi.price * oi.quantity) AS revenue
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        JOIN orders o ON o.id = oi.order_id
        WHERE o.status='paid' AND o.created_at >= %s
        GROUP BY p.id, p.name ORDER BY revenue DESC LIMIT 10
    """, (since,))
    top_products = cur.fetchall()

    # Top customers
    cur.execute("""
        SELECT u.name, u.email, COUNT(o.id) AS orders, SUM(o.total) AS spent
        FROM orders o JOIN users u ON u.id = o.user_id
        WHERE o.status='paid' AND o.created_at >= %s
        GROUP BY u.id, u.name, u.email ORDER BY spent DESC LIMIT 10
    """, (since,))
    top_customers = cur.fetchall()

    # Category breakdown
    cur.execute("""
        SELECT p.category, SUM(oi.quantity) AS sold
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        JOIN orders o ON o.id = oi.order_id
        WHERE o.status='paid' AND o.created_at >= %s AND p.category IS NOT NULL
        GROUP BY p.category ORDER BY sold DESC
    """, (since,))
    cat_data = cur.fetchall()

    # Order status breakdown
    cur.execute("""
        SELECT status, COUNT(*) AS cnt FROM orders
        WHERE created_at >= %s GROUP BY status
    """, (since,))
    status_rows = cur.fetchall()

    cur.close()
    return render_template(
        "admin/reports.html",
        period=days,
        period_revenue=period_revenue,
        period_orders=period_orders,
        active_customers=active_customers,
        avg_order=avg_order,
        labels=labels,
        rev_data=rev_data,
        top_products=top_products,
        top_customers=top_customers,
        cat_data=cat_data,
        status_rows=status_rows,
    )


# ─────────────────────────────────────────────
# Store Settings
# ─────────────────────────────────────────────
@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
@admin_required
def settings():
    cur = mysql.connection.cursor()
    if request.method == "POST":
        keys = [
            "site_name", "site_tagline", "currency", "currency_symbol",
            "free_shipping_above", "contact_email", "contact_phone",
            "address", "loyalty_points_rate", "meta_description",
        ]
        for k in keys:
            v = request.form.get(k, "").strip()
            cur.execute(
                "INSERT INTO store_settings (key_name, value) VALUES (%s,%s) "
                "ON DUPLICATE KEY UPDATE value=%s",
                (k, v, v),
            )
        mysql.connection.commit()
        flash("Settings saved.", "success")
        return redirect(url_for("admin.settings"))

    cur.execute("SELECT key_name, value FROM store_settings")
    rows = cur.fetchall()
    cur.close()
    s = {r["key_name"]: r["value"] for r in rows}
    return render_template("admin/settings.html", s=s)


# ─────────────────────────────────────────────
# Staff & Permissions
# ─────────────────────────────────────────────
@admin_bp.route("/staff")
@login_required
@admin_required
def staff():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT u.id, u.name, u.email, u.is_admin, u.created_at,
               sr.name AS role_name
        FROM users u
        LEFT JOIN staff_roles sr ON sr.id = u.staff_role_id
        ORDER BY u.is_admin DESC, u.name
    """)
    staff_members = cur.fetchall()
    cur.execute("SELECT id, name, permissions FROM staff_roles ORDER BY name")
    roles = cur.fetchall()
    cur.close()
    return render_template("admin/staff.html", staff_members=staff_members, roles=roles)


@admin_bp.route("/staff/assign-role/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def assign_role(user_id):
    role_id = request.form.get("role_id") or None
    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET staff_role_id=%s WHERE id=%s", (role_id, user_id))
    mysql.connection.commit()
    cur.close()
    flash("Role assigned.", "success")
    return redirect(url_for("admin.staff"))


@admin_bp.route("/staff/roles/save", methods=["POST"])
@login_required
@admin_required
def save_role():
    role_id = request.form.get("id", "").strip()
    name    = request.form.get("name", "").strip()
    perms   = request.form.get("permissions", "").strip()
    if not name:
        flash("Role name required.", "danger")
        return redirect(url_for("admin.staff"))
    cur = mysql.connection.cursor()
    if role_id:
        cur.execute("UPDATE staff_roles SET name=%s, permissions=%s WHERE id=%s", (name, perms, int(role_id)))
        flash("Role updated.", "success")
    else:
        cur.execute("INSERT INTO staff_roles (name, permissions) VALUES (%s,%s)", (name, perms))
        flash("Role created.", "success")
    mysql.connection.commit()
    cur.close()
    return redirect(url_for("admin.staff"))


@admin_bp.route("/staff/roles/delete/<int:role_id>", methods=["POST"])
@login_required
@admin_required
def delete_role(role_id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET staff_role_id=NULL WHERE staff_role_id=%s", (role_id,))
    cur.execute("DELETE FROM staff_roles WHERE id=%s", (role_id,))
    mysql.connection.commit()
    cur.close()
    flash("Role deleted.", "info")
    return redirect(url_for("admin.staff"))
