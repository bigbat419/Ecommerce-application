import os
import hmac
import hashlib
import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from extensions import mysql

checkout_bp = Blueprint('checkout', __name__, template_folder='../templates')


def _paystack_headers():
    secret = current_app.config.get('PAYSTACK_SECRET_KEY', '')
    return {
        'Authorization': f'Bearer {secret}',
        'Content-Type': 'application/json',
    }


# ----------------------------------
# Checkout page — initiates Paystack
# ----------------------------------
@checkout_bp.route('/', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'POST':
        total = float(request.form['total'])
        email = current_user.email
        callback_url = url_for('checkout.verify', _external=True)

        payload = {
            'email': email,
            'amount': int(total * 100),   # Paystack expects kobo/cents
            'currency': 'NGN',
            'callback_url': callback_url,
            'metadata': {'user_id': current_user.id},
        }

        try:
            resp = requests.post(
                'https://api.paystack.co/transaction/initialize',
                json=payload,
                headers=_paystack_headers(),
                timeout=15,
            )
            data = resp.json()
            if data.get('status'):
                # Save pending order before redirecting
                _create_pending_order(current_user.id, total, data['data']['reference'])
                return redirect(data['data']['authorization_url'])
            else:
                flash(f"Payment init failed: {data.get('message', 'Unknown error')}", 'danger')
        except Exception as e:
            flash(f'Payment error: {str(e)}', 'danger')

        return redirect(url_for('checkout.checkout'))

    # GET — load cart items and saved addresses
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT ci.id, p.name, p.price, ci.quantity
        FROM cart_items ci
        JOIN products p ON p.id = ci.product_id
        WHERE ci.user_id = %s
    """, (current_user.id,))
    items = cur.fetchall()
    cur.execute(
        "SELECT id, label, line1, city, country FROM addresses WHERE user_id=%s ORDER BY created_at DESC",
        (current_user.id,),
    )
    addresses = cur.fetchall()
    cur.close()

    for it in items:
        it['price'] = float(it['price'] or 0)
        it['quantity'] = int(it['quantity'] or 0)

    total = sum(it['price'] * it['quantity'] for it in items)
    public_key = current_app.config.get('PAYSTACK_PUBLIC_KEY', '')
    return render_template(
        'checkout/checkout.html',
        items=items,
        total=total,
        public_key=public_key,
        addresses=addresses,
    )


# ----------------------------------
# Paystack callback — verify payment
# ----------------------------------
@checkout_bp.route('/verify')
@login_required
def verify():
    reference = request.args.get('reference')
    if not reference:
        flash('No payment reference found.', 'danger')
        return redirect(url_for('cart.view_cart'))

    try:
        resp = requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers=_paystack_headers(),
            timeout=15,
        )
        data = resp.json()
        if data.get('status') and data['data']['status'] == 'success':
            _confirm_order(reference)
            _clear_cart(current_user.id)
            flash('Payment successful! Your order has been placed.', 'success')
            return redirect(url_for('checkout.success'))
        else:
            flash('Payment verification failed. Please contact support.', 'danger')
            _cancel_order(reference)
    except Exception as e:
        flash(f'Verification error: {str(e)}', 'danger')

    return redirect(url_for('checkout.cancel'))


# ----------------------------------
# Paystack webhook (server-to-server)
# ----------------------------------
@checkout_bp.route('/webhook', methods=['POST'])
def webhook():
    secret = current_app.config.get('PAYSTACK_SECRET_KEY', '')
    sig = request.headers.get('X-Paystack-Signature', '')
    computed = hmac.new(secret.encode(), request.data, hashlib.sha512).hexdigest()

    if not hmac.compare_digest(computed, sig):
        return jsonify({'error': 'Invalid signature'}), 400

    event = request.get_json()
    if event and event.get('event') == 'charge.success':
        ref = event['data'].get('reference')
        if ref:
            _confirm_order(ref)
            _clear_cart_by_reference(ref)

    return jsonify({'status': 'ok'}), 200


# ----------------------------------
# Success / Cancel pages
# ----------------------------------
@checkout_bp.route('/success')
@login_required
def success():
    return render_template('checkout/success.html')


@checkout_bp.route('/cancel')
@login_required
def cancel():
    return render_template('checkout/cancel.html')


# ----------------------------------
# Helpers
# ----------------------------------
def _create_pending_order(user_id, total, reference):
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO orders (user_id, total, status, paystack_reference)
        VALUES (%s, %s, 'pending', %s)
    """, (user_id, total, reference))
    order_id = cur.lastrowid

    # Copy cart items into order_items
    cur.execute("""
        INSERT INTO order_items (order_id, product_id, price, quantity)
        SELECT %s, ci.product_id, p.price, ci.quantity
        FROM cart_items ci
        JOIN products p ON p.id = ci.product_id
        WHERE ci.user_id = %s
    """, (order_id, user_id))

    mysql.connection.commit()
    cur.close()


def _confirm_order(reference):
    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE orders SET status='paid' WHERE paystack_reference=%s",
        (reference,)
    )
    # Award loyalty points: 1 pt per ₦100 spent
    cur.execute(
        "SELECT id, user_id, total FROM orders WHERE paystack_reference=%s",
        (reference,)
    )
    order = cur.fetchone()
    if order:
        points = max(1, int(float(order['total']) // 100))
        cur.execute(
            "INSERT INTO loyalty_points (user_id, points, event_type, reference) VALUES (%s,%s,'purchase',%s)",
            (order['user_id'], points, reference),
        )
        # Add first tracking event
        cur.execute(
            "INSERT INTO order_tracking (order_id, status, note, location) VALUES (%s,'Payment Confirmed','Payment verified via Paystack.','Flamingos Processing Centre')",
            (order['id'],),
        )
    mysql.connection.commit()
    cur.close()


def _cancel_order(reference):
    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE orders SET status='cancelled' WHERE paystack_reference=%s",
        (reference,)
    )
    mysql.connection.commit()
    cur.close()


def _clear_cart(user_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM cart_items WHERE user_id=%s", (user_id,))
    mysql.connection.commit()
    cur.close()


def _clear_cart_by_reference(reference):
    cur = mysql.connection.cursor()
    cur.execute("SELECT user_id FROM orders WHERE paystack_reference=%s", (reference,))
    row = cur.fetchone()
    if row:
        cur.execute("DELETE FROM cart_items WHERE user_id=%s", (row['user_id'],))
        mysql.connection.commit()
    cur.close()
