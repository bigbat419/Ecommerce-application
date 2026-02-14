from flask import Blueprint, render_template
from flask_login import login_required, current_user
from extensions import mysql

orders_bp = Blueprint('orders', __name__, template_folder='../templates')

@orders_bp.route('/orders')
@login_required
def orders():
    cur = mysql.connection.cursor(dictionary=True)
    cur.execute(
        "SELECT * FROM orders WHERE user_id=%s ORDER BY created_at DESC",
        (current_user.id,)
    )
    orders = cur.fetchall()
    cur.close()
    return render_template('orders/list.html', orders=orders)


@orders_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    cur = mysql.connection.cursor(dictionary=True)
    cur.execute("""
        SELECT p.name, oi.price, oi.quantity
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        WHERE oi.order_id=%s
    """, (order_id,))
    items = cur.fetchall()
    cur.close()
    return render_template('orders/order_detail.html', items=items)
