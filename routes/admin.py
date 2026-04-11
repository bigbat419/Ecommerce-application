import os
import re
from functools import wraps
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
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


# ----------------------
# Dashboard
# ----------------------
@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) AS cnt FROM products")
    total_products = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) AS cnt FROM users")
    total_users = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) AS cnt FROM orders")
    total_orders = cur.fetchone()["cnt"]
    cur.execute("SELECT COALESCE(SUM(total), 0) AS rev FROM orders WHERE status='paid'")
    revenue = cur.fetchone()["rev"]
    cur.execute("""
        SELECT o.id, u.name, o.total, o.status, o.created_at
        FROM orders o JOIN users u ON u.id = o.user_id
        ORDER BY o.created_at DESC LIMIT 5
    """)
    recent_orders = cur.fetchall()
    cur.close()
    return render_template(
        "admin/admin_dashboard.html",
        total_products=total_products,
        total_users=total_users,
        total_orders=total_orders,
        revenue=revenue,
        recent_orders=recent_orders,
    )


# ----------------------
# Manage Products
# ----------------------
@admin_bp.route("/products")
@login_required
@admin_required
def products():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name, price, stock, category, created_at FROM products ORDER BY created_at DESC")
    products = cur.fetchall()
    cur.close()
    return render_template("admin/products.html", products=products)


@admin_bp.route("/products/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_product():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = request.form.get("price", "").strip()
        stock = request.form.get("stock", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        image = request.files.get("image")

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
        # Ensure slug uniqueness
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
        name = request.form.get("name", "").strip()
        price = request.form.get("price", "").strip()
        stock = request.form.get("stock", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        image = request.files.get("image")

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


# ----------------------
# Manage Users
# ----------------------
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


# ----------------------
# Manage Orders
# ----------------------
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
