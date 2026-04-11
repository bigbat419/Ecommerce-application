from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import mysql
from utils import hash_password, verify_password

account_bp = Blueprint("account", __name__, url_prefix="/account", template_folder="../templates")


@account_bp.route("/")
@login_required
def profile():
    return render_template("account/profile.html", user=current_user)


@account_bp.route("/profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    cur = mysql.connection.cursor()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Name is required.", "warning")
            return redirect(url_for("account.edit_profile"))
        cur.execute("UPDATE users SET name=%s WHERE id=%s", (name, current_user.id))
        mysql.connection.commit()
        current_user.name = name
        flash("Profile updated.", "success")
        return redirect(url_for("account.edit_profile"))

    cur.execute("SELECT id, name, email FROM users WHERE id=%s", (current_user.id,))
    user = cur.fetchone()
    cur.close()
    return render_template("account/edit_profile.html", user=user)


@account_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_pw = request.form.get("current_password", "")
        new_pw = request.form.get("new_password", "")
        confirm_pw = request.form.get("confirm_password", "")

        cur = mysql.connection.cursor()
        cur.execute("SELECT password FROM users WHERE id=%s", (current_user.id,))
        row = cur.fetchone()

        if not verify_password(row["password"], current_pw):
            flash("Current password is incorrect.", "danger")
            cur.close()
            return redirect(url_for("account.change_password"))

        if new_pw != confirm_pw:
            flash("New passwords do not match.", "warning")
            cur.close()
            return redirect(url_for("account.change_password"))

        if len(new_pw) < 6:
            flash("Password must be at least 6 characters.", "warning")
            cur.close()
            return redirect(url_for("account.change_password"))

        cur.execute("UPDATE users SET password=%s WHERE id=%s", (hash_password(new_pw), current_user.id))
        mysql.connection.commit()
        cur.close()
        flash("Password changed successfully.", "success")
        return redirect(url_for("account.edit_profile"))

    return render_template("account/change_password.html")


@account_bp.route("/addresses", methods=["GET", "POST"])
@login_required
def addresses():
    cur = mysql.connection.cursor()
    if request.method == "POST":
        label = request.form.get("label", "").strip()
        line1 = request.form.get("line1", "").strip()
        city = request.form.get("city", "").strip()
        country = request.form.get("country", "").strip()

        if not line1 or not city or not country:
            flash("Please complete all required fields.", "warning")
        else:
            cur.execute(
                "INSERT INTO addresses (user_id, label, line1, city, country) VALUES (%s,%s,%s,%s,%s)",
                (current_user.id, label, line1, city, country),
            )
            mysql.connection.commit()
            flash("Address added.", "success")
            cur.close()
            return redirect(url_for("account.addresses"))

    cur.execute(
        "SELECT id, label, line1, city, country FROM addresses WHERE user_id=%s ORDER BY created_at DESC",
        (current_user.id,),
    )
    addresses = cur.fetchall()
    cur.close()
    return render_template("account/addresses.html", addresses=addresses)


@account_bp.route("/addresses/delete/<int:addr_id>", methods=["POST"])
@login_required
def delete_address(addr_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM addresses WHERE id=%s AND user_id=%s", (addr_id, current_user.id))
    mysql.connection.commit()
    cur.close()
    flash("Address removed.", "info")
    return redirect(url_for("account.addresses"))


@account_bp.route("/orders")
@login_required
def orders():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT id, total, status, created_at FROM orders WHERE user_id=%s ORDER BY created_at DESC",
        (current_user.id,),
    )
    orders = cur.fetchall()
    cur.close()
    return render_template("account/orders.html", orders=orders)


@account_bp.route("/order/<int:order_id>")
@login_required
def order_detail(order_id):
    cur = mysql.connection.cursor()
    # Verify order belongs to user
    cur.execute("SELECT id, total, status, created_at FROM orders WHERE id=%s AND user_id=%s", (order_id, current_user.id))
    order = cur.fetchone()
    if not order:
        flash("Order not found.", "warning")
        cur.close()
        return redirect(url_for("account.orders"))

    cur.execute("""
        SELECT oi.id, oi.price, oi.quantity, p.name, p.image
        FROM order_items oi
        LEFT JOIN products p ON p.id = oi.product_id
        WHERE oi.order_id=%s
    """, (order_id,))
    items = cur.fetchall()
    cur.close()
    return render_template("account/order_detail.html", order=order, items=items)
