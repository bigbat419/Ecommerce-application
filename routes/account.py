from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import mysql
from utils import hash_password, verify_password

account_bp = Blueprint("account", __name__, url_prefix="/account", template_folder="../templates")


@account_bp.route("/")
@login_required
def profile():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) AS cnt FROM orders WHERE user_id=%s", (current_user.id,))
    order_count = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) AS cnt FROM wishlist WHERE user_id=%s", (current_user.id,))
    wishlist_count = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) AS cnt FROM addresses WHERE user_id=%s", (current_user.id,))
    address_count = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) AS cnt FROM reviews WHERE user_id=%s", (current_user.id,))
    review_count = cur.fetchone()['cnt']
    cur.execute(
        "SELECT id, total, status, created_at, paystack_reference FROM orders WHERE user_id=%s ORDER BY created_at DESC LIMIT 5",
        (current_user.id,),
    )
    recent_orders = cur.fetchall()
    cur.close()
    return render_template(
        "account/profile.html",
        user=current_user,
        order_count=order_count,
        wishlist_count=wishlist_count,
        address_count=address_count,
        review_count=review_count,
        recent_orders=recent_orders,
    )


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


# ─────────────────────────────────────────────
# Order Tracking
# ─────────────────────────────────────────────
@account_bp.route("/order/<int:order_id>/track")
@login_required
def track_order(order_id):
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT id, total, status, created_at, paystack_reference, tracking_number, shipping_address "
        "FROM orders WHERE id=%s AND user_id=%s",
        (order_id, current_user.id),
    )
    order = cur.fetchone()
    if not order:
        flash("Order not found.", "warning")
        cur.close()
        return redirect(url_for("account.orders"))

    cur.execute(
        "SELECT status, note, location, created_at FROM order_tracking "
        "WHERE order_id=%s ORDER BY created_at ASC",
        (order_id,),
    )
    tracking_events = cur.fetchall()

    # If no manual tracking events yet, synthesise one from order status
    if not tracking_events:
        tracking_events = [{
            'status': 'Order Placed',
            'note':   'Your order has been received and is being processed.',
            'location': 'Flamingos Warehouse',
            'created_at': order['created_at'],
        }]
        if order['status'] in ('paid', 'shipped', 'delivered'):
            tracking_events.append({
                'status': 'Payment Confirmed',
                'note': 'Payment verified successfully.',
                'location': 'Flamingos Processing Centre',
                'created_at': order['created_at'],
            })
        if order['status'] in ('shipped', 'delivered'):
            tracking_events.append({
                'status': 'Shipped',
                'note': 'Your order has left our warehouse.',
                'location': 'Lagos Hub',
                'created_at': order['created_at'],
            })
        if order['status'] == 'delivered':
            tracking_events.append({
                'status': 'Delivered',
                'note': 'Your order has been delivered.',
                'location': 'Delivery Address',
                'created_at': order['created_at'],
            })

    cur.close()
    return render_template(
        "account/track_order.html",
        order=order,
        tracking_events=tracking_events,
    )


# ─────────────────────────────────────────────
# Returns — submit request
# ─────────────────────────────────────────────
@account_bp.route("/order/<int:order_id>/return", methods=["GET", "POST"])
@login_required
def request_return(order_id):
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT id, total, status, created_at FROM orders WHERE id=%s AND user_id=%s",
        (order_id, current_user.id),
    )
    order = cur.fetchone()
    if not order:
        flash("Order not found.", "warning")
        cur.close()
        return redirect(url_for("account.orders"))

    if request.method == "POST":
        reason  = request.form.get("reason", "").strip()
        details = request.form.get("details", "").strip()
        if not reason:
            flash("Please select a reason.", "warning")
        else:
            # Check no existing pending request
            cur.execute(
                "SELECT id FROM return_requests WHERE order_id=%s AND user_id=%s AND status='pending'",
                (order_id, current_user.id),
            )
            if cur.fetchone():
                flash("A return request for this order is already pending.", "warning")
            else:
                cur.execute(
                    "INSERT INTO return_requests (order_id, user_id, reason, details) VALUES (%s,%s,%s,%s)",
                    (order_id, current_user.id, reason, details),
                )
                mysql.connection.commit()
                flash("Return request submitted. We'll review it within 24 hours.", "success")
                cur.close()
                return redirect(url_for("account.order_detail", order_id=order_id))

    cur.execute(
        "SELECT id, reason, details, status, created_at FROM return_requests "
        "WHERE order_id=%s AND user_id=%s ORDER BY created_at DESC",
        (order_id, current_user.id),
    )
    existing_returns = cur.fetchall()
    cur.close()
    return render_template(
        "account/request_return.html",
        order=order,
        existing_returns=existing_returns,
    )


# ─────────────────────────────────────────────
# Loyalty / Rewards
# ─────────────────────────────────────────────
@account_bp.route("/rewards")
@login_required
def rewards():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT SUM(points) AS total FROM loyalty_points WHERE user_id=%s",
        (current_user.id,),
    )
    row = cur.fetchone()
    total_points = int(row['total'] or 0)

    cur.execute(
        "SELECT points, event_type, reference, created_at "
        "FROM loyalty_points WHERE user_id=%s ORDER BY created_at DESC LIMIT 30",
        (current_user.id,),
    )
    history = cur.fetchall()

    # Points value: 100 pts = ₦1,000
    value = (total_points // 100) * 1000
    cur.close()
    return render_template(
        "account/rewards.html",
        total_points=total_points,
        history=history,
        value=value,
    )
