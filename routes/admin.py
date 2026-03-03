# routes/admin.py
import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from extensions import mysql

admin_bp = Blueprint("admin", __name__, template_folder="../templates")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ----------------------
# Dashboard
# ----------------------
@admin_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("admin_dashboard.html")


# ----------------------
# Manage Products
# ----------------------
@admin_bp.route("/products")
@login_required
def products():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name, price, stock, category, created_at FROM products")
    products = cur.fetchall()
    cur.close()
    return render_template("products.html", products=products)


@admin_bp.route("/products/add", methods=["GET", "POST"])
@login_required
def add_product():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = request.form.get("price", "").strip()
        stock = request.form.get("stock", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        image = request.files.get("image")

        # Validation
        if not name or not price or not stock:
            flash("Name, price, and stock are required.", "danger")
            return redirect(url_for("admin.add_product"))

        try:
            price = float(price)
            stock = int(stock)
        except ValueError:
            flash("Price must be a number and stock must be an integer.", "danger")
            return redirect(url_for("admin.add_product"))

        # Handle image upload
        image_path = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            upload_folder = os.path.join(current_app.root_path, "static/uploads")
            os.makedirs(upload_folder, exist_ok=True)
            image.save(os.path.join(upload_folder, filename))
            image_path = f"uploads/{filename}"
        elif image:
            flash("Invalid image format. Only png, jpg, jpeg, gif allowed.", "danger")
            return redirect(url_for("admin.add_product"))

        # Insert into database
        cur = mysql.connection.cursor()
        cur.execute(
            """
            INSERT INTO products (name, price, stock, category, description, image)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (name, price, stock, category, description, image_path),
        )
        mysql.connection.commit()
        cur.close()

        flash("Product added successfully!", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("new_product.html")

@admin_bp.route("/products/delete/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM products WHERE id=%s", (product_id,))
    mysql.connection.commit()
    cur.close()

    flash("Product deleted!", "info")
    return redirect(url_for("admin.products"))


# ----------------------
# Manage Users
# ----------------------
@admin_bp.route("/users")
@login_required
def users():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, email FROM users")
    users = cur.fetchall()
    cur.close()
    return render_template("admin/users.html", users=users)


# ----------------------
# Manage Orders
# ----------------------
@admin_bp.route("/orders")
@login_required
def orders():
    cur = mysql.connection.cursor()
    cur.execute(
        """SELECT o.id, u.username, o.total, o.status, o.created_at
           FROM orders o 
           JOIN users u ON u.id = o.user_id
           ORDER BY o.created_at DESC"""
    )
    orders = cur.fetchall()
    cur.close()
    return render_template("admin/orders.html", orders=orders)


@admin_bp.route("/orders/update/<int:order_id>", methods=["POST"])
@login_required
def update_order(order_id):
    new_status = request.form.get("status")

    cur = mysql.connection.cursor()
    cur.execute("UPDATE orders SET status=%s WHERE id=%s", (new_status, order_id))
    mysql.connection.commit()
    cur.close()

    flash("Order status updated!", "success")
    return redirect(url_for("admin.orders"))
