# routes/cart.py
from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from extensions import mysql

cart_bp = Blueprint("cart", __name__, template_folder="../templates")

# -------------------------
# Main cart view (for logged-in users)
# -------------------------
@cart_bp.route('/view', endpoint="view_cart")
@login_required
def cart_view():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT ci.id, p.id AS product_id, p.name, p.price, ci.quantity, p.image
        FROM cart_items ci
        JOIN products p ON p.id = ci.product_id
        WHERE ci.user_id = %s
    """, (current_user.id,))
    items = cur.fetchall()
    cur.close()
    # return jsonify({'items': items})

    # Force proper numeric types
    for it in items:
        try:
            it['price'] = float(it['price']) if it['price'] is not None else 0.0
        except (ValueError, TypeError):
            it['price'] = 0.0
        try:
            it['quantity'] = int(it['quantity']) if it['quantity'] is not None else 0
        except (ValueError, TypeError):
            it['quantity'] = 0
      # Return JSON response with cart items
    total = sum(it['price'] * it['quantity'] for it in items)
    # return jsonify({ 'items':items,'quantity, price': total})
    return render_template('cart/view.html', items=items, total=total)

# -------------------------
# Guest cart (session-based)
# -------------------------
@cart_bp.route('/cart/guest')
def guest_cart_view():
    guest_items = session.get("cart", [])
    total = sum([it['price'] * it['quantity'] for it in guest_items]) if guest_items else 0
    return render_template("cart/guest.html", items=guest_items, total=total)


# -------------------------
# Add product to cart
# -------------------------
@cart_bp.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def cart_add(product_id):
    qty = int(request.form.get('quantity', 1))

    cur = mysql.connection.cursor()
    cur.execute(
        'SELECT id, quantity FROM cart_items WHERE user_id=%s AND product_id=%s',
        (current_user.id, product_id)
    )
    row = cur.fetchone()

    if row:
        cur.execute(
            'UPDATE cart_items SET quantity = quantity + %s WHERE id = %s',
            (qty, row['id'])
        )
    else:
        cur.execute(
            'INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s, %s, %s)',
            (current_user.id, product_id, qty)
        )

    mysql.connection.commit()
    cur.close()

    flash('Added to cart', 'success')
    return redirect(url_for('products.product_detail', product_id=product_id))


# -------------------------
# Remove item from cart
# -------------------------
@cart_bp.route('/cart/remove/<int:item_id>', methods=['POST'], endpoint="remove")
@login_required
def cart_remove(item_id):
    cur = mysql.connection.cursor()
    cur.execute(
        'DELETE FROM cart_items WHERE id=%s AND user_id=%s',
        (item_id, current_user.id)
    )
    mysql.connection.commit()
    cur.close()

    flash('Removed from cart', 'info')
    return redirect(url_for('cart.view_cart'))
