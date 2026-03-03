# routes/account.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import mysql   # use extensions.py, not app.py

account_bp = Blueprint('account', __name__, url_prefix='/account', template_folder='../templates')


# -----------------------------
# Manage Addresses
# -----------------------------
@account_bp.route('/addresses', methods=['GET','POST'])
@login_required
def addresses():
    cur = mysql.connection.cursor()

    # ⚠️ Table creation should NOT happen in route handlers.
    # Better to use migrations or schema.sql.
    # I'm leaving it here since you wrote it, but recommend removing.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS addresses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            label VARCHAR(100),
            line1 VARCHAR(255),
            city VARCHAR(100),
            country VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    mysql.connection.commit()

    if request.method == 'POST':
        label = request.form.get('label', '').strip()
        line1 = request.form.get('line1', '').strip()
        city = request.form.get('city', '').strip()
        country = request.form.get('country', '').strip()

        if not line1 or not city or not country:
            flash("Please complete all required fields.", "warning")
        else:
            cur.execute(
                'INSERT INTO addresses (user_id, label, line1, city, country) VALUES (%s,%s,%s,%s,%s)',
                (current_user.id, label, line1, city, country)
            )
            mysql.connection.commit()
            flash('Address added successfully', 'success')
            return redirect(url_for('account.addresses'))

    cur.execute(
        'SELECT id, label, line1, city, country FROM addresses WHERE user_id=%s ORDER BY created_at DESC',
        (current_user.id,)
    )
    addresses = cur.fetchall()
    cur.close()

    return render_template('account/addresses.html', addresses=addresses)


# -----------------------------
# User Orders
# -----------------------------
@account_bp.route('/orders')
@login_required
def orders():
    cur = mysql.connection.cursor()
    cur.execute(
        """SELECT o.id, o.total, o.status, o.created_at
           FROM orders o 
           WHERE o.user_id=%s
           ORDER BY o.created_at DESC""",
        (current_user.id,)
    )
    orders = cur.fetchall()
    cur.close()
    return render_template('account/orders.html', orders=orders)


# -----------------------------
# Order Detail
# -----------------------------
@account_bp.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    cur = mysql.connection.cursor()
    cur.execute(
        """SELECT oi.id, oi.product_id, oi.price, oi.quantity, p.name
           FROM order_items oi
           LEFT JOIN products p ON p.id = oi.product_id
           WHERE oi.order_id = %s""",
        (order_id,)
    )
    items = cur.fetchall()
    cur.close()
    return render_template('account/order_detail.html', items=items)